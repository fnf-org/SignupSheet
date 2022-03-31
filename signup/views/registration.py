# 
# This file contains the user and registration related views
#

from django.http import Http404
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.contrib.auth.models import User
from django.forms import ValidationError
from django.utils.translation import gettext as _
from django.contrib.auth.decorators import login_required
from django.core.cache import cache

from signup.models import Volunteer

class UserCreateWithEmailForm(UserCreationForm):
    name = forms.CharField(required=True)
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ("name", "email", "password1", "password2")

    def save(self, commit=True):
        user = super(UserCreateWithEmailForm, self).save(commit=False)
        user.username = self.cleaned_data["email"]
        user.email = self.cleaned_data["email"]
        names = self.cleaned_data['name'].split(None, 1);
        user.first_name = names[0]
        if len(names) == 2:
            user.last_name = names[1]
        else:
            user.last_name = ""

        if commit:
            cache.clear()
            user.save()
        return user
    
    def clean_email(self):
        address = self.cleaned_data['email']
        print("validating address:", address)
        # Look at users to see if this email is already registered. 
        if User.objects.filter(email__exact=address).count() > 0 :
            raise ValidationError(_('That email address already belongs to a user.'), code='Already registered')
        return address

def register(request, template_name='registration/register.html'):
    if request.method == 'POST':
        form = UserCreateWithEmailForm(request.POST)
        if form.is_valid():
            new_user = form.save()
            return HttpResponseRedirect("/")
    else:
        form = UserCreateWithEmailForm()
    return render(request, template_name, {
        'form': form,
    })

class UserPreferencesForm(forms.Form):
    name = forms.CharField(required=True)

    class Meta:
        fields = ("name",)
            
@login_required   
def user(request, template_name='registration/userprefs.html'):
    user = User.objects.get(pk=request.user.id)
    signups = Volunteer.objects.filter(user__exact=user)
    if request.method == 'POST':
        form = UserPreferencesForm(request.POST)
        if form.is_valid():
            names = form.cleaned_data['name'].split(None, 1);
            user.first_name = names[0]
            if len(names) == 2:
                user.last_name = names[1]
            else:
                user.last_name = ""
            user.save()
            cache.clear()

    form = UserPreferencesForm({'name' : user.first_name + ' ' + user.last_name, 'email': user.email})
    return render(request, template_name, {
        'form': form,
        'signups' : signups,
    })
    