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

from signup.gql_helpers import client as gql_client

def index(request):
    title = 'Cafe Bruxia'

    clade = gql_client.get_clade(title)
    role = clade.staffroles.data[0].attributes
    coordinators = [ x.attributes for x in clade.coordinators.data ]
    jobs = [ x.attributes for x in clade.jobs.data ]
    status = "Fucked"

    template_values = {
        'title': title,
        'role': role,
        'coordinators' : coordinators,
        'jobs' : jobs,
        'user' : request.user,
    }
    return render(request, 'signup/simple_jobpage.html', context=template_values)
