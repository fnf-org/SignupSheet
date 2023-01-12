#! /bin/bash 

set -e 

echo STARTING Signup Application 

ls -la / 
ls -la /runtime

# Source the environment from the runtime.
if [ -f /runtime/config ]; then 
    echo Sourcing runtime configuration... 
    cat /runtime/config
    . /runtime/config
fi

. /runtime/config
printenv 

# Apply migrations, if necessary
echo Apply migrations...
python3 ./manage.py migrate 

# FIXME: Determine if initialization is needed. 
if /bin/false; then 
    for fixture in fixtures/*.json; do 
        python3 ./manage.py loaddata $fixture
    done
fi

# Run the app
echo Run the app!
python3 ./manage.py runserver --insecure 0.0.0.0:${PORT}
