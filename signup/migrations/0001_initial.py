# Generated by Django 4.0.2 on 2022-02-16 00:08

import datetime
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Global',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('user_enable', models.IntegerField(choices=[(0, 'Restricted: Only coordinators can fill shifts, and only protected shifts.'), (1, 'Open access: Anyone can signup for shifts.'), (2, 'Closed: Signups are closed. See you next year!')], default=0)),
            ],
        ),
        migrations.CreateModel(
            name='Source',
            fields=[
                ('title', models.CharField(max_length=64, primary_key=True, serialize=False, verbose_name='Coordinator Role Name')),
                ('text', models.TextField(default='\ncoordinator "Name" "" ""\ncontact ""\ndescription {\n}\n    ')),
                ('version', models.DateTimeField(auto_now_add=True, verbose_name='Changed On')),
                ('owner', models.CharField(max_length=64, verbose_name='Changed By')),
            ],
        ),
        migrations.CreateModel(
            name='Role',
            fields=[
                ('source', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, serialize=False, to='signup.source')),
                ('status', models.IntegerField(choices=[(0, 'Signups for this job are disabled.'), (1, 'Signups are available.'), (2, 'This job is under construction and will be available soon.')], default=1)),
                ('contact', models.EmailField(default='', max_length=254)),
                ('description', models.TextField()),
            ],
        ),
        migrations.CreateModel(
            name='Job',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=64)),
                ('start', models.DateTimeField()),
                ('end', models.DateTimeField()),
                ('description', models.TextField()),
                ('needs', models.IntegerField()),
                ('protected', models.BooleanField()),
                ('source', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='signup.source')),
            ],
        ),
        migrations.CreateModel(
            name='Coordinator',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=64)),
                ('email', models.EmailField(max_length=254)),
                ('url', models.URLField()),
                ('source', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='signup.source')),
            ],
        ),
        migrations.CreateModel(
            name='Volunteer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('source', models.CharField(max_length=64)),
                ('title', models.CharField(max_length=64)),
                ('start', models.DateTimeField()),
                ('end', models.DateTimeField(default=datetime.datetime.now)),
                ('comment', models.TextField()),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'index_together': {('source', 'title', 'start')},
            },
        ),
    ]
