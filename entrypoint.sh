#! /bin/bash 

set -e 

echo STARTING Signup container.

# Source the environment from the runtime.
if [ -f /runtime/config ]; then 
    echo Sourcing runtime /runtime/config
    . /runtime/config
fi

# Apply migrations, if necessary
echo Apply migrations...
python3 ./manage.py migrate 

# FIXME: Determine if initialization is needed. 
if /bin/false; then 
    echo "Applying default data."
    for fixture in fixtures/*.json; do 
        python3 ./manage.py loaddata $fixture
    done
fi

# Run the app
echo STARTING Signup application.
python3 ./manage.py runserver --insecure 0.0.0.0:${PORT}
