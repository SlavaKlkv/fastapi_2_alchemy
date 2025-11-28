import logging
import time

from pydantic import EmailStr

from celery_utils import celery_app

logger = logging.getLogger(__name__)

MESSAGE_TEXT = 'Письмо отправлено.'


@celery_app.task
def send_email(email: EmailStr):
    """
    Фейковая отправка письма на указанный адрес.
    """
    logger.info(f'Отправка письма на {email} ...')
    time.sleep(2)
    logger.info(f'Письмо отправлено на {email}: {MESSAGE_TEXT}')
    return {
        'email': email,
        'status': 'отправлено',
        'message': MESSAGE_TEXT,
    }
