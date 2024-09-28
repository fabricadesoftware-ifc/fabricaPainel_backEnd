import os

from celery import Celery

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_project.settings')

app = Celery('django_project', broker='amqp://lucas:240600@localhost/fabricapainel')


app.conf.update(
    broker_connection_retry_on_startup=True,
)
app.conf.task_always_eager = False
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks([
    'core.__seedwork.domain.tasks',
])


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')

