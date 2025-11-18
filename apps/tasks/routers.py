from fastapi import APIRouter

from apps.tasks.email import send_email
from apps.tasks.schemas import EmailRequest, EmailResponse

tasks_router = APIRouter(tags=['tasks'])


@tasks_router.post('/send-email', response_model=EmailResponse)
def send_email_endpoint(payload: EmailRequest):
    task = send_email.delay(payload.email)
    return EmailResponse(task_id=task.id)
