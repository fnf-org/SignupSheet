"""
Views for our new React front-end
"""

import json 

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.conf import settings
from django.http import Http404
from django.db.models import Sum

from signup.views.jobs import filterNavData, index

from signup.models import Coordinator, Job, Role, Volunteer, Global
from signup.access import is_coordinator, is_coordinator_of, is_ea, is_ld, EA_THRESHOLD, LD_THRESHOLD, global_signup_enable


@login_required
def react_jobs(request, title):
    """
    Fetch the clade of the db that's needed to render a jobs page.
    """        
    # Fetch the role information 
    roles = Role.objects.filter(source__exact=title)
    if len(roles) == 0:
        raise Http404("That role was not found.")
    
    coordinators = []
    jobstaff = []
    volunteers = []
    role = {
        'role': title, 
        'status': roles[0].status,
        'contact': roles[0].contact,
        'description': roles[0].description,
        'coordinators': coordinators,
        'jobs': jobstaff,
        'is_coordinator': is_coordinator_of(request.user, roles[0].source),
        'is_user': request.user.username,
        'volunteers': volunteers,
        'summary': get_job_summary(request)
    }
    for c in Coordinator.objects.filter(source__exact=title):
        if c.url == "" : 
            c.url = settings.COORDINATOR_DEFAULT_IMG
        elif c.url[0:4] != "http" :
            c.url = settings.COORDINATOR_STATIC_IMG_URL + c.url
        coordinators.append({
            'name': c.name,
            'email': c.email,
            'img': c.url,
        })

    for job in Job.objects.filter(source__exact=title).order_by('start'):
        entry = {
            'title': job.title,
            'start': job.start.strftime("%A %H:%M"), 
            'end': job.end.strftime("%A %H:%M"),
            'description': job.description,
            'needs': job.needs,
            'protected': job.protected,
        }
        jobstaff.append(entry)

    for vol in Volunteer.objects.filter(source__exact=job.source.pk).select_related('user'):
        volunteers.append({
            'username': vol.user.username,
            'first_name': vol.user.first_name,
            'last_name': vol.user.last_name,
            'comment': vol.comment,
            'role': vol.source,
            'title': vol.title, 
            'start': vol.start.strftime("%A %H:%M"),
            'end': vol.end.strftime("%A %H:%M"),
        })


    context = {
        'data': json.dumps(role),
    }
    return render(request, 'react/jobpage.html', context={'data': role})

def get_job_summary(request) :
    """
    Get the job summary information.     
    """    
    roles = Role.objects.all().order_by('source')
    navdata = []
    for role in roles : 
        jobcount = Job.objects.filter(source__exact=role.source.pk).aggregate(Sum('needs'))['needs__sum']
        if jobcount is None : 
            jobcount = 0            
        personcount = Volunteer.objects.filter(source__exact=role.source.pk).count()
        navdata.append({
            'role': role.pk, 
            'needed': jobcount - personcount, 
            'jobs': jobcount, 
            'status': role.status,
            'is_coordinator': is_coordinator_of(request.user, role.source)          
        })
    
    navdata.sort(reverse=True, key=lambda role: role['needed'])
    return navdata
