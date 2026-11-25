script_dir=$(dirname $(realpath "$0"))

cd $script_dir/../app_backend

pipenv run bash -c 'DEPLOYMENT_MODE=unit_test ./manage.py test'
