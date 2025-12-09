from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp, Receive, Scope, Send
from fastapi import Request, HTTPException
from typing import Callable, Optional
from src.services.permissions import check_permission
import logging

logger = logging.getLogger(__name__)


class RBACMiddleware(BaseHTTPMiddleware):
    """Middleware enforcing RBAC actions defined on endpoints via __required_permission__ attribute.

    It extracts the actor from `Authorization` or `X-Requester` header and verifies the permission.
    """
    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable):
        endpoint = request.scope.get('endpoint')
        required_permission = None
        # Walk through wrappers to find __required_permission__ attribute
        if endpoint is not None:
            current = endpoint
            while current is not None:
                required_permission = getattr(current, '__required_permission__', None)
                if required_permission:
                    break
                current = getattr(current, '__wrapped__', None)

        # If no required permission defined, proceed
        if not required_permission:
            return await call_next(request)

        # Determine actor (Authorization header or X-Requester)
        auth_hdr = request.headers.get('authorization')
        x_requester = request.headers.get('x-requester')
        actor = None
        if auth_hdr:
            # Use existing codepath: validate token -> role
            try:
                from src.web.auth import validate_admin_token
                admin = validate_admin_token(auth_hdr)
                if admin and admin.get('role'):
                    actor = admin.get('role')
                elif admin and admin.get('id'):
                    actor = admin.get('id')
            except Exception as e:
                logger.debug(f"RBAC: validate_admin_token error: {e}")
        if actor is None and x_requester:
            actor = x_requester

        if actor is None:
            raise HTTPException(status_code=403, detail="Missing actor for permission check")

        # Check permission
        if not check_permission(actor, required_permission):
            raise HTTPException(status_code=403, detail=f"Permission denied for actor '{actor}' to perform '{required_permission}'")

        # passes
        return await call_next(request)
