#! /bin/sh 

set -e 

echo STARTING Signup Application 

ls -la / 
ls -la /runtime

# Source the environment from the runtime.
if [ -f /runtime/config ]; then 
    . /runtime/config
fi

printenv 

# Apply migrations, if necessary
python3 ./manage.py migrate 

# FIXME: Determine if initialization is needed. 
if /bin/false; then 
    for fixture in fixtures/*.json; do 
        python3 ./manage.py loaddata $fixture
    done
fi

# Run the app
python3 ./manage.py runserver --insecure 0.0.0.0:${PORT}
