# VdGSA Web Applications
Web application code for parts of the VdGSA website including: user account system, Conclave registration, rental viol system, historical viols database.

## Running the Development Stack
The dev stack requires Python 3.10 or later and [Docker](https://docs.docker.com/engine/install/ubuntu/).
We recommend running the dev stack on a supported Ubuntu LTS version.

### Clone the Repository
```
git clone git@github.com:vdgsa/user_backend.git vdgsa_website
cd vdgsa_website
```

### Create a Self-Signed Certificate (Development only!)
DO NOT USE A SELF-SIGNED CERTIFICATE IN PRODUCTION.
This is for local dev builds only.

These instructions are from the [Let's Encrypt docs](https://letsencrypt.org/docs/certificates-for-localhost/#making-and-trusting-your-own-certificates), accessed on Oct 11, 2025.

### Obtain a TLS Certificate with Let's Encrypt (Production)

### Set Secrets and Application Keys
Write these values to files with the names specified below.
If this is a production deployment, put the files in `deployment/prod`. If this is a dev deployment, put the files in `deployment/dev`.
1. Postgres password (this can be any random string): `deployment/(dev|prod)/secrets/postgres_password`
1. Stripe secret key: `deployment/(dev|prod)/secrets/stripe_private_key`
1. Recaptcha private key: `deployment/(dev|prod)/secrets/recaptcha_private_key`
1. Django app secret key (this can be any random string of letters): `deployment/(dev|prod)/secrets/django_app_secret_key`

### Build and Start the Stack
```
./dev_scripts/compose_dev watch
```

This will start the compose stack in watch mode.
Changes to the python code should cause the running app to update automatically.

In a separate terminal, collect static files and apply migrations:
```
docker exec -it vdgsa_django python3 manage.py collectstatic --noinput
docker exec -it vdgsa_django python3 manage.py migrate
```

### Stopping the stack
You can stop the stack with:
```
./dev_scripts/compose_dev stop
```

## Running Linters and Tests

## Generating and Applying Django DB Migrations
Whenever you add/alter/remove DB Models, run the following to generate migration files:
```
./manage.py makemigrations
```

To apply new migrations to your stack:
```
docker exec -it vdgsa_django python3 manage.py migrate
```

## Updating Django Static Files
If you add/change/remove any files in `app_backend/static`, run the following to recollect migrations on your stack:
```
docker exec -it vdgsa_django python3 manage.py collectstatic --noinput
```

## Deploying to Production

pip install django-recaptcha
pip install python-dotenv

.env file contains key
RECAPTCHA_PUBLIC_KEY = ''
RECAPTCHA_PRIVATE_KEY = ''
