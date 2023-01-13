#! /bin/bash 

set -e 

# Source the environment from the runtime.
if [ -f /runtime/config ]; then 
    . /runtime/config
fi

# Run the app
python3 ./manage.py runserver --insecure 0.0.0.0:${PORT}
