#!/bin/bash

# migrações
python3 manage.py migrate

# seed da base de dados
python3 seed.py

# start server
python3 manage.py runserver 0.0.0.0:8000
