from __future__ import unicode_literals

import uuid 

from django.contrib.auth.models import User
from django.db import models
from django.db.models import ForeignKey
from django.db.models.fields import (
    TextField, CharField, EmailField, URLField, DateTimeField, IntegerField, BooleanField
)
from datetime import datetime

class Global(models.Model):
    '''This model supports the public release feature of the staff sheet, there 
    should only ever be one row in this table. If the user_enable field is false 
    then only marked admin roles can be claimed. This way I can release the staff
    sheet to coordinators with the permanent URL and not worry about leaks. Further,
    even coordinators will not be able to pre-fill slots without having them marked
    admin. This might cut down on cheating a bit.'''
    
    COORDINATOR_ONLY = 0 
    AVAILABLE = 1
    CLOSED = 2
    
    CHOICES = (
            (COORDINATOR_ONLY, 'Restricted: Only coordinators can fill shifts, and only protected shifts.'),
            (AVAILABLE, 'Open access: Anyone can signup for shifts.'),
            (CLOSED, 'Closed: Signups are closed. See you next year!'),
    )
    
    user_enable = IntegerField(choices=CHOICES, default=COORDINATOR_ONLY)

class Source(models.Model):
    '''This is the source code used to generate the staff sheet'''
    title = CharField("Coordinator Role Name", max_length=64, primary_key=True)
    text = TextField(default='''
coordinator "Name" "" ""
contact ""
description {
}
    ''');
    version = DateTimeField("Changed On", auto_now_add=True)
    owner = CharField("Changed By", 
        max_length=64
    )

class Role(models.Model):
    '''The parsed Role'''
    DISABLED = 0
    ACTIVE = 1
    WORKING = 2
    
    STATUS = ((DISABLED, 'Signups for this job are disabled.'),
              (ACTIVE, 'Signups are available.'),
              (WORKING, 'This job is under construction and will be available soon.'),
    )
    
    source = models.OneToOneField(
        Source,
        on_delete=models.CASCADE,
        primary_key=True,
    )

    status = IntegerField(choices=STATUS, default=ACTIVE)
    contact = EmailField(default='')
    description = TextField()

class Coordinator(models.Model):
    '''A coordinator in one role.''' 

    models.UUIDField()
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    source = ForeignKey(Source, on_delete=models.CASCADE)
    name = CharField(max_length=64)
    email = EmailField()
    url = URLField()

class Job(models.Model):
    '''An individual job (volunteer shift) in a role''' 

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    source = ForeignKey(Source, on_delete=models.CASCADE)
    title = CharField(max_length=64)
    start = DateTimeField() 
    end = DateTimeField()
    description = TextField()
    needs = IntegerField()
    protected = BooleanField()
    
class Volunteer(models.Model):
    '''
    A volunteer in a role
    
    The volunteer must be able to join with Job, but it cannot use a surrogate key.
    Recompiling the Role source will delete Coordinators and Jobs, but should not
    delete the people who have already signed up. Instead they should be joined 
    with the natural key of Job which is (role, title, start). This is a shitty
    join, if it's too slow I can probably figure out how to use hashes as the PK
    for Volunteer and Job
    '''
    
    class Meta :
        index_together = ['source', 'title', 'start']
        

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = ForeignKey(User, on_delete=models.DO_NOTHING)
    
    # The natural key of Job 
    source = CharField(max_length=64)
    title = CharField(max_length=64)
    start = DateTimeField()
    
    # Not used in the join, just so that overlaps can be detected
    end = DateTimeField(default=datetime.now)
    # --- 
    
    comment = TextField()

   
