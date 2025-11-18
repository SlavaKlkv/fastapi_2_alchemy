from os import getenv

from celery import Celery


def make_celery():
    broker_url = getenv('CELERY_BROKER_URL', 'redis://redis:6379/0')
    result_backend = getenv('CELERY_RESULT_BACKEND', 'redis://redis:6379/1')

    celery = Celery(
        'worker',
        broker_url=broker_url,
        result_backend=result_backend,
    )

    celery.conf.update(
        task_serializer='json',
        result_serializer='json',
        accept_content=['json'],
        timezone='UTC',
        enable_utc=True,
    )

    return celery


celery_app = make_celery()

celery_app.autodiscover_tasks(['apps.tasks'])
