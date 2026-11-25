from typing import Any
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator

class EmailRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    from_: str = Field(alias="from", min_length=3, max_length=320)
    to: list[EmailStr] | EmailStr
    subject: str = Field(min_length=1, max_length=998)
    text: str | None = None
    html: str | None = None
    cc: list[EmailStr] | EmailStr | None = None
    bcc: list[EmailStr] | EmailStr | None = None
    reply_to: list[EmailStr] | EmailStr | None = Field(default=None, alias="reply_to")
    headers: dict[str, str] | None = None
    tags: list[dict[str, str]] | None = None

    @field_validator("from_")
    @classmethod
    def validate_from(cls, value: str) -> str:
        if "<" in value and ">" in value:
            address = value.rsplit("<", 1)[-1].split(">", 1)[0].strip()
        else:
            address = value.strip()
        if "@" not in address or any(ch.isspace() for ch in address):
            raise ValueError("from must contain a valid email address")
        return value

    @model_validator(mode="after")
    def require_body(self):
        if self.text is None and self.html is None:
            raise ValueError("At least one of text or html is required")
        return self

    @staticmethod
    def as_list(value: Any) -> list[str]:
        if value is None:
            return []
        if isinstance(value, str):
            return [value]
        return [str(item) for item in value]

    @property
    def recipients(self) -> list[str]:
        return self.as_list(self.to) + self.as_list(self.cc) + self.as_list(self.bcc)

    @property
    def reply_to_list(self) -> list[str]:
        return self.as_list(self.reply_to)
