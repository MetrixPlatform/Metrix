import re

from pydantic import BaseModel

PHONE_RE = re.compile(r"^1[3-9]\d{9}$")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class MessageResponse(BaseModel):
    message: str


def normalize_phone(value: str) -> str:
    phone = value.strip()
    if not PHONE_RE.fullmatch(phone):
        raise ValueError("手机号码格式不正确")
    return phone


def normalize_email(value: str) -> str:
    email = value.strip()
    if not EMAIL_RE.fullmatch(email):
        raise ValueError("邮箱格式不正确")
    return email
