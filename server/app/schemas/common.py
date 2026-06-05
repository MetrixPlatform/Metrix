import re

from pydantic import BaseModel, Field
from pydantic_core import PydanticCustomError

PHONE_RE = re.compile(r"^1[3-9]\d{9}$")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
MessageParam = str | int | float | bool | None


class MessageResponse(BaseModel):
    code: str
    message: str = ""
    params: dict[str, MessageParam] = Field(default_factory=dict)


def message_response(code: str, message: str = "", **params: MessageParam) -> MessageResponse:
    return MessageResponse(code=code, message=message, params={key: value for key, value in params.items() if value is not None})


def normalize_phone(value: str) -> str:
    phone = value.strip()
    if not PHONE_RE.fullmatch(phone):
        raise PydanticCustomError("validation.phone", "Invalid phone number")
    return phone


def normalize_email(value: str) -> str:
    email = value.strip()
    if not EMAIL_RE.fullmatch(email):
        raise PydanticCustomError("validation.email", "Invalid email address")
    return email
