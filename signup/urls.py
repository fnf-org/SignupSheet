from django.urls import path, include

from signup.views import jobs
from signup.views import email_suggest
from signup.views.react import react_jobs
from signup.views.email_suggest import email_suggest

import signup.views.csv 
import signup.views.source 
import signup.views.registration 
import signup.views.jobs

urlpatterns = [
    path('source/', signup.views.source.source_list, name='source_list'),
    path('source/cr', signup.views.source.source_create, name='source_create'),
    path('source/u/<pk>', signup.views.source.source_update, name='source_update'),
    path('source/d/<pk>', signup.views.source.source_delete, name='source_delete'),
    path('source/a', signup.views.source.source_all, name='source_all'),
    path('sourcelock/', signup.views.source.source_lock, name='source_lock'),

    path('user/', signup.views.registration.user, name='user'),
    path('register/', signup.views.registration.register, name='register'),
    path('accounts/', include('django.contrib.auth.urls')),

    path('csv/', signup.views.csv.download_csv, name='download_csv'),
    path('eald/', signup.views.csv.eald_csv, name='eald_csv'),

    path('jobs/<title>/', signup.views.jobs.jobs, name='jobs'),
    path('email/<role>/', signup.views.jobs.email_list, name='email_list'),
    path('signup/', signup.views.jobs.signup_view, name='signup'),
    path('delete/', signup.views.jobs.delete, name='delete'),

    path('r/jobs/<title>/', react_jobs, name='react_jobs'),

    path('email_suggest/q=<query>', email_suggest, name='email_suggest'),

    path('', jobs.index, name='index'),
]
