import pytest
from pydantic import ValidationError
from app.schemas import EmailRequest

def test_accepts_basic_resend_shape():
    item = EmailRequest.model_validate({
        "from": "Billing <billing@example.com>",
        "to": ["one@example.net", "two@example.net"],
        "subject": "Welcome",
        "html": "<p>Hello</p>",
        "text": "Hello",
    })
    assert item.recipients == ["one@example.net", "two@example.net"]

def test_requires_text_or_html():
    with pytest.raises(ValidationError):
        EmailRequest.model_validate({
            "from": "billing@example.com",
            "to": "one@example.net",
            "subject": "Welcome",
        })

def test_normalizes_single_recipient():
    item = EmailRequest.model_validate({
        "from": "billing@example.com",
        "to": "one@example.net",
        "subject": "Welcome",
        "text": "Hello",
    })
    assert item.recipients == ["one@example.net"]
