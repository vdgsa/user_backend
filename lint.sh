pycodestyle . \
&& isort --check --diff --skip migrations . \
&& mypy . --exclude "vdgsa_backend/rental_viols/"
