set -e

script_dir=$(dirname $(realpath "$0"))

cd $script_dir/../app_backend
DEPLOYMENT_MODE=unit_test ./manage.py test -v2 $@
