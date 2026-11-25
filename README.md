# VdGSA Web Applications
Web application code for parts of the VdGSA website including: user account system, Conclave registration, rental viol system, historical viols database.

The commands listed are relative to the root directory of the repository unless otherwise specified.

## Development Environment Setup

### Install Prerequisites

- We recommend using a supported Ubuntu LTS version.
- Python 3.10 or later with pip and venv
  ```
  sudo add-apt-repository ppa:deadsnakes/ppa
  sudo apt-get update
  sudo apt-get install python3.10
  sudo apt-get install python3.10-venv
  python3.10 -m ensurepip
  ```
- [Docker](https://docs.docker.com/engine/install/ubuntu/)

### Clone the Repository
```
git clone git@github.com:vdgsa/user_backend.git vdgsa_website
cd vdgsa_website
```

### Install Pipenv and Python Dependencies Locally

This is needed for running tests and generating migrations.
Install [pipenv](https://pipenv.pypa.io/en/latest/installation.html) and the required Python packages.
```
sudo apt install pipenv
cd app_backend
pipenv sync --dev
```

Note: `pipenv sync` installs needed packages but does not remove unneeded ones.
`pipenv clean` removes extra packages.

### Set Secrets & Application Public Keys

The secrets files and environment variables set here apply to the development stack (`DEPLOYMENT_MODE=dev`) and unit test mode (`DEPLOYMENT_MODE=unit_test`).

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

### How the Dev Stack Sends Emails

The development stack will write the contents of any emails it would send to the directory `/usr/src/app/emails.log` in the `vdgsa_django` container.
The filename is configured in `vdgsa_backend/settings.py`.

To print the most email file:
```
docker exec -it vdgsa_django bash -c "cat $(tail -n 1 $(ls -1 /usr/src/app/emails.log))"
```

### Creating a User Account for Development

To create a superuser (has all permissions):
```
DEPLOYMENT_MODE=unit_test pipenv run ./manage.py
```

Note: You can set specific user permissions through the django admin site at <http://localhost:1680/admin>.
Log in with your superuser account.

You can also create an account and "purchase" a membership through the site's normal interface.
When you get to the phase of receiving an email with a link to finish creating the account, print the most recent logged email with:
```
./dev_scripts/email_log_print_most_recent.sh
```

In `dev_scripts`, there are several other shortcut scripts for interacting with logged emails.

## Running Linters and Tests
Note: We have been lax in running these. Expect errors.
```
cd app_backend
pipenv shell
../lint.sh
# If start_postgres.sh says the container vdgsa-dev-postgres already exists,
# start instead it with `docker start vdgsa-dev-postgres`
../dev_scripts/start_postgres.sh
DEPLOYMENT_MODE=unit_test ./manage.py test
```

## Generating and Applying Django DB Migrations
Whenever you add/alter/remove DB Models, run the following to generate migration files:
```
cd app_backend
DEPLOYMENT_MODE=unit_test pipenv run ./manage.py makemigrations
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

Before deploying for the first time, the secrets and public keys need to be set as described [below](#set-secrets--application-public-keys-1).

To deploy an update on our current production server:
```
cd vdgsa_backend
git pull
cd
./deploy.sh
```

The `deploy.sh` script only exists on the server and has the following contents:
```
compose_file=vdgsa_backend/deployment/prod/docker-compose.yml
docker compose -f $compose_file build
docker compose -f $compose_file up -d
sleep 3
docker exec -it vdgsa_prod_django python3 manage.py migrate
docker exec -it vdgsa_prod_django python3 manage.py collectstatic
```

### Set Secrets & Application Public Keys

#### Application Public Keys
In `deployment/prod/.env`, set the following environment variables:
- STRIPE_PUBLIC_KEY to the publishable key for your selected Stripe sandbox.
- RECAPTCHA_PUBLIC_KEY to the recaptcha public key.

#### Secrets
Write these values to files with the names specified below.
1. Postgres password (this can be any random string): `deployment/prod/secrets/postgres_password`
1. Stripe secret key (use the key for your stripe sandbox): `deployment/prod/secrets/stripe_private_key`
1. Django app secret key (this can be any random string of letters): `deployment/prod/secrets/django_app_secret_key`
1. Recaptcha private key: `deployment/prod/secrets/recaptcha_private_key`

## Setting Up Read-Only Remote DB Access
Things to know:
- The nginx-acme directory has:
  - The nginx config for a webserver that the acme challenge can send requests to (conf.d/default.conf)
  - The directory for the acme challenge file to be written to (acme-challenge)
- The directory letsencrypt/certificates is where the SSL cert will be saved to.

### Create a Read-only postgres user
```
docker exec -it vdgsa_prod_postgres psql -U postgres
```
Then in the postgres shell (replace <password> with an actual password):
```
CREATE ROLE hex_read_only WITH LOGIN PASSWORD '<password>';
\connect postgres;

GRANT CONNECT ON DATABASE postgres TO hex_read_only;
GRANT USAGE ON SCHEMA public TO hex_read_only;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO hex_read_only;
```
Note that the "public" schema exists by default.
Since we haven't configured anything otherwise, all our tables are in the "public" schema.

### Obtain an SSL Cert with Let's Encrypt
If it doesn't exist already, create a "letsencrypt" directory that the cert will be added to.
```
mkdir -p /home/vdgsaapi/letsencrypt
```

Using the Docker version of the LEGO acme client, obtain the cert:
```
docker run -i -v /home/vdgsaapi/letsencrypt:/.lego -v /home/vdgsaapi/nginx-acme/acme-webroot:/webroot goacme/lego --http.webroot /webroot  --email="webmaster@vdgsa.org" --domains="marais.vdgsa.org" --http run
```

### Set Up a Cron Job to Renew the Cert
Open crontab with `crontab -e`, then add the following:
```0 3 1 * * docker run -i --rm -v /home/vdgsaapi/letsencrypt:/.lego -v /home/vdgsaapi/nginx-acme/acme-webroot:/webroot goacme/lego --http.webroot /webroot  --email="webmaster@vdgsa.org" --domains="marais.vdgsa.org" --http renew &>> /home/vdgsaapi/crontablog.dbcert.log && docker exec -it -u postgres vdgsa_prod_postgres pg_ctl reload

### Update postgres.conf to use the cert
If it doesn't exist already, make a copy of the default postgres.conf file.
```
mkdir -p /home/vdgsaapi/postgres
if ! test -f /home/vdgsaapi/postgres/postgresql.conf; then
  docker exec -it vdgsa_prod_postgres cat /usr/share/postgresql/postgresql.conf.sample > /home/vdgsaapi/postgres/postgresql.conf
fi
```
Then find and update the following settings in postgresql.conf:
```
listen_addresses = '*'
ssl = on
ssl_cert_file = '/letsencrypt/marais.vdgsa.org.crt'
ssl_key_file = '/letsencrypt/marais.vdgsa.org.key'
```

### Re-up the Postgres Service
```
cd vdgsa_backend/deployment/prod
docker compose stop postgres
docker compose up -d postgres
