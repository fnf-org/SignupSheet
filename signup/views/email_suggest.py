
from django.contrib.auth.decorators import user_passes_test
from signup.access import is_coordinator
from django.contrib.auth.models import User
from django.http import JsonResponse

from django.core.cache import cache

@user_passes_test(lambda u: is_coordinator(u))
def email_suggest(request, query=""):
    users = cache.get('user_suggest_cache')
    if users is None:
        users = list(map(lambda u: (f'"{u.first_name} {u.last_name}" <{u.email}>', f'"{u.first_name} {u.last_name}" <{u.email}>'.lower()), 
            User.objects.all()))
        cache.set('user_suggest_cache', users)

    if query.strip() == "":
        items = []
    else:
        items = list(user[0] for user in users if query.lower() in user[1])[0:20]

    return JsonResponse({
        'items': items
    })
