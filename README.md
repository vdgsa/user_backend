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

### Set Secrets & Application Public Keys

#### Configure a Stripe Sandbox
In the stripe dashboard, create a sandbox (we're allowed 5, so double check that we have enough left).
The Stripe CLI in the dev stack is configured to listen for checkout.session.completed events and forward them to our django app endpoints:
- `/accounts/stripe_webhook/`
- `/stripe_emails/send_officer_emails/`

#### Application Public Keys
In `deployment/dev/.env`, set STRIPE_PUBLIC_KEY to the publishable key for your selected Stripe sandbox.

Note that the reCaptcha public key should not be set in development mode.

#### Secrets
Write these values to files with the names specified below.
1. Postgres password (this can be any random string): `deployment/dev/secrets/postgres_password`
1. Stripe secret key (use the key for your stripe sandbox): `deployment/dev/secrets/stripe_private_key`
1. Django app secret key (this can be any random string of letters): `deployment/dev/secrets/django_app_secret_key`

Note that the reCaptcha secrets should not be set in development mode.
This will make django-recaptcha use default test keys.

### Build and Start the Stack
The script `dev_scripts/compose_dev` is an alias for `docker compose -f deployment/dev/docker-compose.yml`.
```
./dev_scripts/compose_dev build
./dev_scripts/compose_dev watch
```

This will start the compose stack in watch mode.
The site will be available at localhost:1680.
Changes to the python code and most configuration files should cause the running app to update automatically.
If you change `docker-compose.yml`, or if you change another config file and the change doesn't seem to get picked up, stop the running watch command, [stop the stack](#stopping-the-stack), re-build, and re-run the watch command.

In a separate terminal, collect static files and apply migrations:
```
./dev_scripts/compose_dev exec django python3 manage.py collectstatic --noinput
./dev_scripts/compose_dev exec django python3 manage.py migrate
```

#### Stopping the stack
You can stop the stack with:
```
./dev_scripts/compose_dev stop
```

#### List Running Containers
To print information about the currently running containers of the stack:
```
./dev_scripts/compose_dev ps
```

### Authenticate the Stripe CLI
View the logs for the stripe container:
```
./dev_scripts/compose_dev logs -f --since 5m stripe-cli
```
Go to the url in the logs and sign in.
Select the sandbox that matches the [stripe secret key you set](#set-secrets-and-application-keys).
Check the pairing code printed to the logs, and click Allow Access.

Note that the Stripe CLI is currently only set to listen for checkout session completed events.
If any additional events need to be forwarded, add them to the stripe-cli command in deployment/dev/docker-compose.yml.

## Running Linters and Tests

## Generating and Applying Django DB Migrations
Whenever you add/alter/remove DB Models, run the following to generate migration files:
```
./manage.py makemigrations
```

To apply new migrations to your stack:
```
./dev_scripts/compose_dev exec django python3 manage.py migrate
```

## Updating Django Static Files
If you add/change/remove any files in `app_backend/static`, run the following to recollect migrations on your stack:
```
./dev_scripts/compose_dev exec django python3 manage.py collectstatic --noinput
```

## Deploying to Production

pip install django-recaptcha
pip install python-dotenv
pip install django-resized
pip install python-slugify

.env file contains key
RECAPTCHA_PUBLIC_KEY = ''
RECAPTCHA_PRIVATE_KEY = ''
