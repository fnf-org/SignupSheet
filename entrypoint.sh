#! /bin/sh 

set -e 

#if [ -z "$DJANGO_DEBUG"]; then 
#    export DJANGO_DEBUG=True
#fi

if [ "$DJANGO_DEBUG" = "True" ]; then 
    export DJANGO_ADMIN_EMAIL=test@test.test 
    export DJANGO_ADMIN_USERNAME=$DJANGO_ADMIN_EMAIL
    export DJANGO_SUPERUSER_PASSWORD=test 
fi 

. ./venv/bin/activate
python3 ./manage.py migrate 
python3 ./manage.py createsuperuser --no-input --email $DJANGO_ADMIN_EMAIL --username $DJANGO_ADMIN_USERNAME || true

#if [ "$DJANGO_DEBUG" = "True" ]; then 
#    for fixture in fixtures/*.json; do 
#        python3 ./manage.py loaddata $fixture
#    done
#fi

python3 ./manage.py runserver --insecure 0.0.0.0:8000
