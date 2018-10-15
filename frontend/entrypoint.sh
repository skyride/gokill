#!/bin/sh
echo yes | ./manage.py collectstatic
gunicorn -w 2 -b 0.0.0.0:80 frontend.wsgi:application
