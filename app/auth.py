import hmac
from fastapi import Header, HTTPException, status
from app.config import get_settings

async def require_api_key(authorization: str | None = Header(default=None)) -> None:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail={
            "message": "Missing or invalid authorization header",
            "name": "authentication_error",
        })
    supplied = authorization.removeprefix("Bearer ").strip()
    if not hmac.compare_digest(supplied, get_settings().api_key):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail={
            "message": "Invalid API key",
            "name": "authentication_error",
        })
