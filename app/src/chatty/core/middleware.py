"""
FastAPI middleware for logging requests and responses.
"""
import time
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from chatty.core.logging import (
    get_logger,
    log_error,
    log_request_info,
    log_response_info,
)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log HTTP requests and responses."""
    
    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)
        self.logger = get_logger("middleware")
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and log information."""
        # Extract request information
        method = request.method
        path = request.url.path
        client_ip = self._get_client_ip(request)
        user_agent = request.headers.get("user-agent", "")
        headers = dict(request.headers)
        query_params = dict(request.query_params)
        
        # Log incoming request
        log_request_info(
            method=method,
            path=path,
            headers=headers,
            query_params=query_params,
            client_ip=client_ip,
            user_agent=user_agent,
        )
        
        # Process request and measure time
        start_time = time.time()
        response = await call_next(request)
        process_time = (time.time() - start_time) * 1000  # Convert to milliseconds
        
        # Log response
        log_response_info(
            method=method,
            path=path,
            status_code=response.status_code,
            response_time_ms=process_time,
            client_ip=client_ip,
        )
        
        # Log errors if status code indicates an error
        if response.status_code >= 400:
            error_message = f"HTTP {response.status_code} error"
            log_error(
                method=method,
                path=path,
                status_code=response.status_code,
                error_message=error_message,
                client_ip=client_ip,
            )
        
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address from request headers."""
        # Check for forwarded headers first (for reverse proxy setups)
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            # X-Forwarded-For can contain multiple IPs, take the first one
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        # Fallback to direct client IP
        if hasattr(request.client, "host"):
            return request.client.host
        
        return "unknown"


class ErrorLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to catch and log unhandled exceptions."""
    
    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)
        self.logger = get_logger("error_middleware")
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and catch exceptions."""
        try:
            response = await call_next(request)
            return response
        except Exception as exc:
            # Extract request information for error logging
            method = request.method
            path = request.url.path
            client_ip = self._get_client_ip(request)
            
            # Log the exception
            log_error(
                method=method,
                path=path,
                status_code=500,
                error_message="Unhandled exception occurred",
                exception=exc,
                client_ip=client_ip,
            )
            
            # Re-raise the exception so FastAPI can handle it
            raise
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address from request headers."""
        # Check for forwarded headers first (for reverse proxy setups)
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            # X-Forwarded-For can contain multiple IPs, take the first one
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        # Fallback to direct client IP
        if hasattr(request.client, "host"):
            return request.client.host
        
        return "unknown"
