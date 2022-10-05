# Open Fibre Cove

## Dev installation

    git clone https://github.com/Open-Telecoms-Data/cove-ofds.git openfibre-cove-ofds
    cd openfibre-cove-ofds
    virtualenv .ve --python=/usr/bin/python3.9
    source .ve/bin/activate
    pip install -r requirements_dev.txt
    python manage.py migrate
    python manage.py compilemessages
    python manage.py runserver

You may need to pass `0.0.0.0:8000` to `runserver` in the last step, depending on your development environment.

Note: requires `gettext` to be installed. This should come by default with Ubuntu, but just in case:

```
apt-get update && apt-get install gettext
```


## Translations

There are currently no translations.

## Compile CSS

```
cd cove_ofds/sass && ./build_ofds.sh 
```

## Lint

Run 

```
isort cove_project/ cove_ofds/
black cove_project/ cove_ofds/
flake8 cove_project/ cove_ofds/
```

## Test

```
DJANGO_SETTINGS_MODULE=cove_project.settings python -m pytest cove_ofds/
```

## Adding and updating requirements

Add a new requirements to `requirements.in` or `requirements_dev.in` depending on whether it is just a development requirement or not.

Then, run `pip-compile requirements.in && pip-compile requirements_dev.in` this will populate `requirements.txt` and `requirements_dev.txt` with pinned versions of the new requirement and its dependencies.

`pip-compile --upgrade requirements.in && pip-compile --upgrade requirements_dev.in` will update all pinned requirements to the latest version. Generally we don't want to do this at the same time as adding a new dependency, to make testing any problems easier.
