#! /bin/bash

# Start a postgres server to run unit tests against

docker run -itd \
    --name vdgsa-dev-postgres \
    -v vdgsa-dev-postgres-data:/var/lib/postgresql/data/ \
    -p 127.0.0.1:5432:5432 \
    -e POSTGRES_DB=vdgsa_postgres \
    -e POSTGRES_PASSWORD=postgres \
    postgres:17
