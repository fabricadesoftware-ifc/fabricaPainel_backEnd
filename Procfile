web: gunicorn --pythonpath src django_project.wsgi:application
worker: celery -A src.django_project worker -l info
beat: celery -A src.django_project beat --loglevel=info
