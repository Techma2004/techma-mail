from datetime import datetime, timezone
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from app.auth import require_api_key
from app.config import get_settings
from app.mailer import MailDeliveryError, send_email
from app.schemas import EmailRequest

settings = get_settings()
app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="A small Resend-compatible email sending API backed by SMTP.",
    docs_url="/docs" if settings.environment != "production" else None,
    redoc_url=None,
)

@app.middleware("http")
async def limit_request_size(request: Request, call_next):
    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > settings.max_message_bytes:
        return JSONResponse(status_code=413, content={"message": "Request body too large", "name": "payload_too_large"})
    response = await call_next(request)
    return response

@app.get("/")
async def root():
    return {"name": settings.app_name, "status": "ok", "docs": "/docs" if settings.environment != "production" else None}

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/emails", dependencies=[Depends(require_api_key)])
async def create_email(payload: EmailRequest):
    if len(payload.recipients) > settings.max_recipients:
        raise HTTPException(status_code=422, detail={
            "message": f"Maximum of {settings.max_recipients} recipients per email",
            "name": "validation_error",
        })
    try:
        email_id = await send_email(payload, settings)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail={"message": str(exc), "name": "validation_error"}) from exc
    except MailDeliveryError as exc:
        raise HTTPException(status_code=502, detail={"message": str(exc), "name": "smtp_error"}) from exc

    return {
        "id": email_id,
        "object": "email",
        "from": payload.from_,
        "to": payload.as_list(payload.to),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    return JSONResponse(status_code=422, content={
        "message": "The request body is invalid",
        "name": "validation_error",
        "errors": exc.errors(include_input=False),
    })
