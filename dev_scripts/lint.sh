set -ex

script_dir=$(dirname $(realpath "$0"))

cd $script_dir/../app_backend

pipenv run pycodestyle .
pipenv run isort --check --diff --skip migrations .
pipenv run mypy . --exclude "vdgsa_backend/rental_viols/"
