pycodestyle . \
&& isort --check --diff --skip migrations . \
&& mypy . \
&& ./manage.py generateschema | diff -q - vdgsa_backend/api_schema/schema.yml
