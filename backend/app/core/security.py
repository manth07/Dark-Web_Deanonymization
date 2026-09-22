"""Security definitions, authentication stubs, and security headers configuration."""

from typing import Any, Optional
from fastapi import HTTPException, Request, Response, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware enforcing secure HTTP headers on all API responses."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains"
        )
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        return response


security_scheme = HTTPBearer(auto_error=False)


def verify_token_stub(
    credentials: Optional[HTTPAuthorizationCredentials],
) -> dict[str, Any]:
    """Stub function for JWT bearer token validation.

    Returns payload dict if valid, or raises HTTPException.
    """
    if not credentials:
        return {"sub": "anonymous", "roles": ["viewer"]}
    
    token = credentials.credentials
    if not token or token == "invalid":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token provided",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return {"sub": "analyst@thirdeye.intel", "roles": ["forensic_investigator"]}
