# Moonshot

This application is designed to manage the issuance, validation, and storage of Digital Green Certificates (DGCs), which are used for recording COVID-19 vaccinations, tests, and recovery statuses. The system allows authorized users, such as health professionals, to create and manage these certificates.

## Summary

- [Moonshot](#moonshot)
  - [Summary](#summary)
  - [Requirements](#requirements)
  - [Installation](#installation)
    - [Configuration Variables](#configuration-variables)
    - [Install packages](#install-packages)
    - [Apply migrations](#apply-migrations)
    - [Populate database](#populate-database)
    - [Run the server](#run-the-server)
  - [Endpoints](#endpoints)

## Requirements

- [Python](https://www.python.org/) (3.11.5)
<!-- - [Django](https://www.djangoproject.com/) (5.0.7)
- [Django-REST-Framework](https://www.django-rest-framework.org/) (3.15.2) -->
- [PostgreSQL](https://www.postgresql.org/) (15.4)

## Installation

### Configuration Variables

| Variable      | Description                                      |
| ------------- | ------------------------------------------------ |
| `SECRET_KEY`  | Secret key used by Django to create hashes       |
| `DEBUG`       | Prints stack trace when server crashes (if True) |
| `DB_NAME`     | Database name                                    |
| `DB_USER`     | Database username                                |
| `DB_PASSWORD` | Database password                                |
| `DB_HOST`     | Database host IP or domain                       |
| `DB_PORT`     | Database port                                    |

These variables must be configured in file `.env`.

### Install packages

After making sure that Python is installed and PostgreSQL is configured with one database, the first step is to install all the required project dependicies:

```bash
pip install -r requirements.txt
```

### Apply migrations

With all the dependencies met, make sure all data models are up to date, applying migrations in the database:

```bash
python manage.py migrate
```

Remember that for this command to be successful, the database must be functional, and the respective environment variables set.

### Populate database

To populate the database with initial data, run (inspect `seed.py` to see credentials):

```bash
python seed.py
```

### Run the server

To start the server in development mode:

```bash
python manage.py runserver 0.0.0.0:8000
```

## Endpoints

After starting the server, go to `api/swagger` to check-out all the available endpoints.
