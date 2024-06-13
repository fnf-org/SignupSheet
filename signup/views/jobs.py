import csv, codecs, io, json, re
from operator import imod

from django.http import HttpResponse
from django.shortcuts import render
from django.http import Http404
from django.db import transaction
from django.db.utils import IntegrityError
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.models import User
from django.db.models import Q
from django.conf import settings
from django.db.models import Sum
from django.core.cache import cache
from django.views.decorators.http import require_http_methods

from signup.models import Coordinator, Job, Role, Volunteer, Global
from signup.access import is_coordinator, is_coordinator_of, can_signup, can_delete, is_ea, is_ld, EA_THRESHOLD, LD_THRESHOLD, global_signup_enable

from signup.views.badge import badgeFor
import signup.views.source

def index(request):
    
    navdata = filterNavData(request.user)
    
    if len(navdata) == 0 : 
        if request.user.is_superuser :
            return redirect(signup.views.source.source_all)    
        else:
            if request.user.is_authenticated:
                return render(request, "underconstruction.html")
            else:
                return redirect('/accounts/login')
    
    return redirect('jobs', navdata[0]['role'].source.pk)
        
def getNavData() :
    # Test if there's nav information cached. 
    navdata = cache.get('navdata')
    if navdata != None :
        return navdata 
    
    # Otherwise fetch navigation information 
    roles = Role.objects.all().order_by('source')
    navdata = []
    for role in roles : 
        ent = {}
        ent['role'] = role;
        
        jobcount = Job.objects.filter(source__exact=role.source.pk).aggregate(Sum('needs'))['needs__sum']
        # Make sure zero count-jobs don't cause a crash
        if jobcount is None : 
            jobcount = 0
            
        personcount = Volunteer.objects.filter(source__exact=role.source.pk).count()
        ent['needed'] = jobcount - personcount # sometimes incorrect, theories above
        ent['jobs'] = jobcount
        ent['status'] = role.status
        ent.update(badgeFor(role, jobcount, personcount))
        navdata.append(ent)
    
    navdata.sort(reverse=True, key=lambda role: role['needed'])
    cache.set('navdata', navdata)
    return navdata

def filterNavData(user) :
    navdata = getNavData()
    rval = []
    for role in navdata : 
        if role['status'] == Role.ACTIVE :
            rval.append(role)
        else :
            if is_coordinator_of(user, role['role'].source) :
                rval.append(role)
    return rval

def get_status(role, needed_staff, total_staff):
    """ Fill enablement and status data """
    status = {}
    status['enable'] = global_signup_enable()
    status['color'] = 'black'
    status['text'] = 'This is the status'
    if status['enable'] == Global.COORDINATOR_ONLY :
        status['color'] = 'red'
        status['text'] = '''The staff sheet is not yet enabled for general signups.
                If you're a coordinator you will be able to fill your protected jobs.
                Otherwise please wait for an announcement indicating the general availability of the staff sheet.'''
    elif status['enable'] == Global.AVAILABLE : 
        if role.status == Role.DISABLED : 
            status['color'] = 'red'
            status['text'] = '''Signups for this job have been temporarily disabled until essential jobs are filled.'''
        else : 
            if needed_staff > 0 :
                status['text'] = "There are " + str(total_staff) + " jobs and " + str(needed_staff) + " left to fill."
            else :
                status['text'] = "All " + str(total_staff) + " available shifts are taken!"
    elif status['enable'] == Global.CLOSED :
        status['color'] = 'red'
        status['text'] = 'Signups are closed. See you next year!'
    return status 

@login_required
def jobs(request, title):
    """Just like jobs but faster."""
    navdata = filterNavData(request.user)

    found = False
    for job in navdata : 
        if job['role'].source.title == title :
            found = True 
            break; 
    
    if not found : 
        return redirect('/')
    
    # Next and previous roles. 
    current_job_index = 0
    for i, item in enumerate(navdata) : 
        if item['role'].source.pk == title :
            current_job_index = i
            break

    next_job = navdata[(current_job_index + 1) % len(navdata)]['role'] 
    prev_job = navdata[(current_job_index - 1) % len(navdata)]['role'] 

    # Fetch the role information 
    roles = Role.objects.filter(source__exact=title)
    if len(roles) == 0:
        raise Http404("That role was not found.")

    role = roles[0]
    is_coordinator = is_coordinator_of(request.user, role.source)
    coordinators = []

    coordinators = Coordinator.objects.filter(source__exact=title)
    for c in coordinators : 
        # Fill images... 
        if c.url == "" : 
            c.url = settings.COORDINATOR_DEFAULT_IMG
        elif c.url[0:4] != "http" :
            c.url = settings.COORDINATOR_STATIC_IMG_URL + c.url

    volunteers = list(
        Volunteer.objects.filter(source__exact=role.source.pk).order_by('start', 'title').select_related('user')
    )

    jobstaff = []
    volnumber = 0
    total_staff = 0 
    needed_staff = 0

    for job in Job.objects.filter(source__exact=title).order_by('start', 'title'):
        entry = {}
        entry['job'] = job 
        entry['volunteers'] = []

        for volunteer in (v for v in volunteers if v.title == job.title and v.start == job.start):
            vol = {}
            vol['volunteer'] = f"{volunteer.user.first_name} {volunteer.user.last_name}"
            vol['comment'] = volunteer.comment
            if can_delete(request.user, volunteer) :
                vol['signupid'] = volunteer.id
            else:
                vol['signupid'] = None                                            
            entry['volunteers'].append(vol)

        needed = job.needs - len(entry['volunteers'])
        for _ in range(needed) :
            vol = {}
            vol['volunteer'] = None
            vol['comment'] = None
            vol['signupid'] = None 
            entry['volunteers'].append(vol)

        # Determine if the user is able to signup
        entry['needed'] = needed
        if needed > 0 :
            entry['can_signup'] = can_signup(request.user, job, role)
        else:
            entry['can_signup'] = False

        jobstaff.append(entry)
        total_staff += job.needs
        needed_staff += needed 

    status = get_status(role, needed_staff, total_staff)

    template_values = {
        'navdata': navdata, # .needed is sometimes incorrect
        'role': role,
        'coordinators' : coordinators,
        'jobs' : jobstaff,
        'user' : request.user,
        'total' : total_staff,  # correct
        'needed' : needed_staff, # correct
        'status' : status,
        'coordinator_of' : is_coordinator,
        'next' : next_job,
        'prev' : prev_job,
    }
    return render(request, 'signup/jobpage.html', context=template_values)


@login_required
@require_http_methods(["POST"])
def signup_view(request):

    try:
        data = json.loads(request.body)
        print('Request data:', data)
        data = {
            'jobid': data['jobid'],
            'comment': data['comment'],
            'user': data.get('user'), # user is optional
        }
        print("Signup for user:", data)
    except Exception as e: 
        print("Fucked request.")
        raise Http404()

    job = Job.objects.get(pk=data['jobid'])
    if job == None :
        print("Job doesn't exist.")
        raise Http404()

    try: 
        with transaction.atomic() :
            signup_user = request.user

            role = Role.objects.get(pk=job.source)
            if not can_signup(request.user, job, role):
                print("User cannot signup.")
                raise Http404()

            if data['user'] is not None:
                m = re.search(r'<(\S+)>$', data['user'])
                if m is not None:
                    data['user'] = m.group(1)
                if not is_coordinator_of(request.user, job.source):
                    print("Non-coordinator third party signup.")
                    raise Http404()
                found = list(User.objects.filter(email__exact=data['user']))
                if len(found) == 0:
                    print("No such user!")
                    raise Http404("No such user.")
                signup_user = found[0]
                
            # Create a Volunteer with form data 
            # We need the natural key from the job... this way 
            # if the job changes in a non-meaningful way this volunteer
            # continues to be valid. 
            v = Volunteer(
                            user = signup_user,
                            comment = data['comment'],
                            source = job.source.pk,
                            title = job.title, 
                            start = job.start,
                            end = job.end,
                            )

            # NB: This feature requires discussion: Doing this will make it 
            # impossible for people to sign up their friends for shifts.
            #
            # Before we commit this to the database let's check to see if the 
            # user is already signed up for a shift at this time...
            shifts = Volunteer.objects.filter(user__exact=signup_user)
            for s in shifts : 
                if s.start == v.start \
                    or ( v.start < s.start and s.end < v.end ) \
                    or ( v.start > s.start and v.start < s.end ):
                    print("Overlap.")
                    raise ValueError("Overlap!")

            # Now add the row, so the count query works...
            v.save()
            
            # Now check if there are too many volunteers. This has to 
            # be done atomically. If we're overbooked, rollback. 
            volcount = Volunteer.objects.filter(source__exact=job.source.pk, title__exact=job.title, start__exact=job.start).count()
            if volcount > job.needs :
                print("Nabbed.")
                raise IntegrityError("fuck! nabbed!")

            # Clear view caches.
            cache.clear()

    except IntegrityError:
        print("Nabbed")
        return HttpResponse('Oh no! This signup was nabbed!', status=450)

    except ValueError:
        print("Error")
        return HttpResponse('Wait a second!', status=451)
        
    return HttpResponse('You got it', status=200)
    
    
@login_required
@require_http_methods(["POST"])
def delete(request):

    try:
        data = json.loads(request.body)
        print('Request data:', data)
        data = {
            'signup': data['signup'],
        }
    except Exception as e: 
        print("Fucked request.")
        raise Http404()

    volunteer = Volunteer.objects.get(pk=data['signup'])
    if volunteer == None :
        print("Job does not exist.")
        raise Http404("Volunteer does not exist")

    # Check perimssions 
    if not can_delete(request.user, volunteer):
        print("Can't delete.")
        raise Http404("Can't delete.")

    volunteer.delete()

    # Clear view caches.
    cache.clear()

    return HttpResponse('Goodbye.', status=200)


@user_passes_test(lambda u: is_coordinator(u))
def email_list(request, role, template_name='misc/email_list.html'):
    data = {}        
    data['role'] = role;
    temp = {}
    for v in Volunteer.objects.filter(source__exact=role) :
        person = User.objects.get(pk=v.user.pk)
        temp[person.email] = person.first_name + " " + person.last_name

    data['volunteers'] = []
    for email,name in temp.items() :
        data['volunteers'].append('"' + name + '" <' + email + ">")
            
    return render(request, template_name, {'data':data} )


