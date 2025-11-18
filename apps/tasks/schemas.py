from pydantic import BaseModel, EmailStr


class EmailRequest(BaseModel):
    email: EmailStr


class EmailResponse(BaseModel):
    task_id: str
    message: str = 'Задача поставлена в очередь'
