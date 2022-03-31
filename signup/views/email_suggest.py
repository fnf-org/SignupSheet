
from django.contrib.auth.decorators import user_passes_test
from signup.access import is_coordinator
from django.contrib.auth.models import User
from django.http import JsonResponse

from django.core.cache import cache

@user_passes_test(lambda u: is_coordinator(u))
def email_suggest(request, query=""):
    users = cache.get('user_suggest_cache')
    if users is None:
        users = list(map(lambda u: u.email, User.objects.all()))
        cache.set('user_suggest_cache', users)

    if query.strip() == "":
        items = []
    else:
        items = list(email for email in users if query in email)[0:20]
    
    return JsonResponse({
        'items': items
    })
