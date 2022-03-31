from signup.models import Source, Coordinator, Global, Role
from argparse import ArgumentError
from datetime import datetime 
import functools 
from django.core.cache import cache
from django.db import transaction

EA_THRESHOLD = datetime.strptime('07/29/2016 13:00:00+0000', '%m/%d/%Y %H:%M:%S%z')
LD_THRESHOLD = datetime.strptime('07/31/2016 12:00:00+0000', '%m/%d/%Y %H:%M:%S%z')

# Permissions caching... make these operations a bit less DB intensive. 
#
def memoize(func): 
    '''Store the permission lookup in memcache'''
    
    @functools.wraps(func)
    def memoizer(*args, **kwargs):
        key = func.__name__ 
        for arg in args:
            key += arg.__class__.__name__ + str(arg.pk).replace(' ', '_')
        
        rval = cache.get(key)
        if rval == None:
            rval = func(*args, **kwargs)
            cache.set(key, rval)
        return rval
    
    return memoizer

# Test if the job or volunteer model is an early arrival job.
def is_ea(job):
    return job.start <= EA_THRESHOLD

# Test if the job or volunteer model is a late departure job.
# This works because the fields in Job and Volunteer are similarly named.
def is_ld(job):
    return job.end > LD_THRESHOLD


# Return the state of the global signup lock.
#
# The global signup lock prevents users from signing up for shifts 
# before the sheet is generally available. This is necessary because 
# the URL is open to coordinators long before the sheet is ready. 
#
@memoize
def global_signup_enable():
    gbs = Global.objects.all()
    if len(gbs) == 0:
        return 0
    else:
        return gbs[0].user_enable 

def set_global_signup_enable(en):
    gbs = Global.objects.all()
    with transaction.atomic() :
        if len(gbs) == 0:
            setting = Global()
            setting.user_enable = en
            setting.save()
        else:
            gbs[0].user_enable = en
            gbs[0].save()
    
    cache.clear()
    
# Test if the user has any form of administrative privileges
# This is true for
#   - Super users 
#   - People with staff access  
#   - People who's email address is listed in a coordinator role.
#
@memoize
def is_coordinator(user):
    print(f"MISS! is_coordinator({user})")
    if user.is_anonymous:
        return False;
    
    return user.is_superuser or user.is_staff \
        or Coordinator.objects.filter(email__exact=user.email).count() > 0 

# Test if the user is the coordinator of a particular role. 
# This is used to restrict coordinator access to only the roles for 
# which they are responsible. This tests true for: 
#   - Super users
#   - People with staff access 
#   - Coordinators who's email address is listed in the role given
#
@memoize
def is_coordinator_of(user, source):
    print(f"MISS! is_coordinator_of({user}, {source})")
    if user.is_anonymous:
        return False;

    return user.is_superuser or user.is_staff \
        or Coordinator.objects.filter(email__exact=user.email, source__exact=source.pk).count() > 0

# Test if a user is able to signup for a job, taking into account the 
# global singup enable. The following conditions must be met:
#
# - Singups are always barred if there are no slots left. This function DOES NOT
#   check if the job is full. That's the responsibility of the caller.
# - Superusers are always able to signup for an available job (this is for testing) 
# - Coordinators can create signups on their own sheets. (XXX: Needs some policy)
#
# If GSE is in the COORDINATOR_ONLY state: 
#   - A coordinator can singup
#
# If GSE is in the AVAILABLE state: 
#   - If the job is protected a coordinator can signup
#   - Otherwise, anyone can. 
#
def can_signup(user, job, role):
    if user.is_anonymous:
        return False;

    gse = global_signup_enable()
    if gse == Global.CLOSED :
        # No one can signup, not even administrators.
        return False

    elif gse == Global.COORDINATOR_ONLY :
        # Coordinator preview.
        if role.status == Role.DISABLED :
            if user.is_superuser:
                return True;
            else:
                return False
        else :
            if user.is_superuser :
                return True;
            elif is_coordinator(user) and is_coordinator_of(user, job.source) and job.protected :
                # Coordinators can pre-fill protected jobs.
                return True
            else:
                return False

    elif gse == Global.AVAILABLE :
        # General availability

        if user.is_superuser:
            return True;
        elif is_coordinator(user) and is_coordinator_of(user, job.source) :
            return True
        else:
            if job.protected :
                return False
            else:
                return True

    # Never get here  
    raise ArgumentError("Failed to fully decode permissions in can_signup()")

# Test if the user can delete the specified volunteer signup. 
# The following conditions must be met: 
# 
# - The superuser can delete anything
# - A coordinator can delete a job for the role that they are the coordinator for
# - A user can delete their own signups. 
#
def can_delete(user, volunteer):
    if user.is_anonymous:
        return False

    gse = global_signup_enable()
    if gse == Global.CLOSED :
        return False

    if user.is_superuser :
        return True
    
    return (volunteer.user == user) or (is_coordinator(user) and is_coordinator_of(user, Source.objects.get(pk=volunteer.source)))
