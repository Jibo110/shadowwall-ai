"""
Security headers middleware.

Adds hardened HTTP security headers to every response.
These headers protect against common web attacks:

- X-Content-Type-Options: prevents MIME sniffing attacks
- X-Frame-Options: prevents clickjacking
- X-XSS-Protection: legacy XSS filter for older browsers
- Strict-Transport-Security: enforces HTTPS
- Content-Security-Policy: controls resource loading
- Referrer-Policy: controls referrer information leakage
- Permissions-Policy: disables browser features we don't use

This is OWASP A05:2021 (Security Misconfiguration) mitigation.
"""

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.core.config import get_settings

settings = get_settings()


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Injects security headers into every HTTP response.
    Must be added to the FastAPI app middleware stack.
    """

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)

        # Prevent MIME type sniffing
        # OWASP: prevents content-type confusion attacks
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Prevent clickjacking via iframes
        response.headers["X-Frame-Options"] = "DENY"

        # Legacy XSS protection for older browsers
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Force HTTPS in production
        if settings.is_production:
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )

       # Content Security Policy
        # In development, allow Swagger UI to load its resources
        # In production, lock this down completely
        if settings.is_production:
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "script-src 'self'; "
                "style-src 'self'; "
                "img-src 'self' data:; "
                "connect-src 'self' ws: wss:;"
            )
        else:
            response.headers["Content-Security-Policy"] = (
                "default-src 'self' 'unsafe-inline' 'unsafe-eval' cdn.jsdelivr.net; "
                "img-src 'self' data: fastapi.tiangolo.com; "
                "connect-src 'self' ws: wss:;"
            )
        # Control referrer information
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Disable unnecessary browser features
        response.headers["Permissions-Policy"] = (
            "camera=(), microphone=(), geolocation=(), "
            "payment=(), usb=(), magnetometer=()"
        )

        # Remove server identification header
        # Never tell attackers what software you're running
        if "server" in response.headers:
            del response.headers["server"]
        if "x-powered-by" in response.headers:
            del response.headers["x-powered-by"]

        return response
