pycodestyle . \
&& isort --check --diff --skip migrations . \
&& mypy .
