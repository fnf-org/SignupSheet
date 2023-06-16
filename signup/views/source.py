from django.contrib.auth.decorators import user_passes_test
from django.db import transaction
from django import forms
from django.forms import ValidationError
from django.http import Http404
from django.shortcuts import render, redirect
from django.utils.translation import gettext_lazy as _
from django.db.utils import IntegrityError
from django.db.models import Sum
from django.core.cache import cache

from signup.parser.StaffSheetLexer import StaffSheetLexer
from signup.parser.StaffSheetListener import StaffSheetListener
from signup.parser.StaffSheetParser import StaffSheetParser
from signup.schema import build, build_all, ReportedException
from signup.views.badge import badgeFor
from signup.access import is_coordinator, is_coordinator_of, global_signup_enable, set_global_signup_enable

from datetime import timedelta

from signup.models import Role, Coordinator, Job, Global, Volunteer
import signup.gql_wrapper as gql 

class SkipperForm(forms.Form):
    title = forms.CharField(label='title')
    text = forms.CharField(label='text', widget=forms.Textarea({'cols': '80', 'rows': '30'}))
    next = forms.CharField(label='next', widget=forms.HiddenInput(), required=False)

    def clean(self):
        super(SkipperForm, self).clean()
        try: 
            build(user=None, sourcetext=self.cleaned_data.get('text'), test_parse=True) 
        except ReportedException as e :
            raise ValidationError(
                _('Error: %(value)s'),
                params={'value': e.message},
            )

class BulkSourceForm(forms.Form):
    text = forms.CharField(label='text', widget=forms.Textarea({'cols': '80', 'rows': '30'}))
    def clean(self):
        super(BulkSourceForm, self).clean()
        try: 
            build_all(self.cleaned_data.get('text'), test_parse=True) 
        except ReportedException as e :
            raise ValidationError(
                _('Error: %(value)s'),
                params={'value': e.message},
            )

class SourceLockForm(forms.Form):
    lock = forms.IntegerField(label='Global Signup Enable', widget=forms.RadioSelect(choices=Global.CHOICES))
    
@user_passes_test(lambda u: is_coordinator(u))
def source_list(request, template_name='source/source_list.html'):
    data = {}
    data['sources'] = []
    jobs = 0
    people = 0
    for s in Source.objects.order_by('title') :
        # Adjust the version date to PDT
        s.version = s.version + timedelta(hours=-7)
        if is_coordinator_of(request.user, s) :
            entry = {}
            entry['jobcount'] = Job.objects.filter(source__exact=s).aggregate(Sum('needs'))['needs__sum']
            # jobcount will be None if there are no defined jobs. 
            if entry['jobcount'] is None :
                entry['jobcount'] = 0
                
            jobs += entry['jobcount']
            entry['personcount'] = Volunteer.objects.filter(source__exact=s.pk).count()
            people += entry['personcount']
            entry['source'] = s
            role = Role.objects.filter(source__exact=s.pk)[0]
            entry.update(badgeFor(role, entry['jobcount'], entry['personcount']))
            data['sources'].append(entry)

    data['totaljobs'] = jobs
    data['totalpeople'] = people
    
    if jobs != 0 :
        data['staffpercent'] = (100 * people) / jobs
    else:
        data['staffpercent'] = 0
    
    data['status'] = {}
    data['status']['enable'] = global_signup_enable()
    data['status']['color'] = 'black'
    data['status']['text'] = "This is the status"
    data['status']['can_edit'] = True
    if data['status']['enable'] == Global.AVAILABLE : 
        data['status']['color'] = 'green'
        data['status']['text'] = "Signups are enabled, anyone can sign up for a job on the staff sheet."
    elif data['status']['enable'] == Global.COORDINATOR_ONLY :
        data['status']['color'] = 'red'
        data['status']['text'] = "Signups are disabled, only protected jobs can be filled by coordinators at this time."
    else : 
        data['status']['color'] = 'red'
        data['status']['text'] = "The sheet is frozen. See you next year!"
        if not request.user.is_superuser :
            data['status']['can_edit'] = False
    
    return render(request, template_name, data)

@user_passes_test(lambda u: is_coordinator(u))
def source_create(request, template_name='source/source_form.html'):
    if request.method == 'POST' :
        form = SkipperForm(request.POST)
        if form.is_valid():
            source = Source()
            source.text = form.cleaned_data['text']
            source.title = form.cleaned_data['title']
            source.owner = request.user.first_name + ' ' + request.user.last_name
            source.save()
        
            # Now build it.
            build(user=request.user, sourceobj=source)

            cache.clear()
            return redirect('source_list')
        else:
            return render(request, template_name, {'form':form})            
    else:
        default = '''
coordinator "Name" "Email" "Url"
contact "Email"
description {
}
    ''' 
        form = SkipperForm( {'text': default, 'title': 'New Role'} )    
        return render(request, template_name, {'form':form})

@user_passes_test(lambda u: is_coordinator(u))
def source_update(request, pk, template_name='source/source_form.html'):    

    next_page = request.GET.get('next', None)
    source = Source.objects.get(title=pk)
    if source == None :
        raise Http404("Source does not exist")

    if request.method=='POST':
        form = SkipperForm(request.POST)
        if form.is_valid():
        
            try: 
                with transaction.atomic() :
                    # There is no update, sources must be deleted and remade.
                    # on_delete=CASCADE is emulated, but it works when my objects don't suck. 
                    source.delete()

                    # Create a new one 
                    source = Source()
                    source.title = pk
                    source.text = form.cleaned_data['text']
                    source.owner = request.user.first_name + ' ' + request.user.last_name
                    source.save()
        
                    # Now build it.
                    build(user=request.user, sourceobj=source)
            except IntegrityError as e:
                print("Transaction error:", e)
        
            cache.clear()
            if form.cleaned_data['next'] != "" : 
                return redirect('jobs', form.cleaned_data['next'])
            else:
                return redirect('source_list')
        else:
            return render(request, template_name, {'title': pk, 'form':form, 'next': next_page})

    else:
        form = SkipperForm({'text': source.text, 'title': source.title})
        return render(request, template_name, {'title': pk, 'form': form, 'next': next_page})

@user_passes_test(lambda u: u.is_superuser)
def source_delete(request, pk, template_name='source/confirm_delete.html'):
    source = Source.objects.get(title=pk)
    if source == None :
        raise Http404("Source does not exist")

    if request.method=='POST':
        source.delete()
        cache.clear()
        return redirect('source_list')
    
    return render(request, template_name, {'object':source})


@user_passes_test(lambda u: u.is_superuser)
def source_all(request, template_name='source/source_bulkedit.html'):
    
    if request.method=='POST':
        form = BulkSourceForm(request.POST)
        if form.is_valid():
            gql.clear_source()
            build_all(form.cleaned_data['text'], request.user)
            cache.clear()
            return redirect('source_all')
        else:
            return render(request, template_name, {'form':form})
    else:
        ## Fetch and unify the source 
        #sources = Source.objects.order_by('title')
        sources = gql.get_sources()
        text = ""
        for source in sources : 
            text += 'role "' + source.title + "\" (\n" + source.text + "\n)\n\n"
        
        form = BulkSourceForm({'text': text})
        return render(request, template_name, {'form':form})

@user_passes_test(lambda u: u.is_superuser)
def source_lock(request, template_name='source/source_lockform.html') :

    if request.method == 'POST' :
        form = SourceLockForm(request.POST)
        if form.is_valid() : 
            set_global_signup_enable(form.cleaned_data['lock'])            
            return redirect('source_list')
        else:
            return render(request, template_name, {'form': form})
    else:
        form = SourceLockForm({'lock': global_signup_enable()})
        return render(request, template_name, {'form': form})
