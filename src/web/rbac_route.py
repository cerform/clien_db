from fastapi.routing import APIRoute
from fastapi import Request, HTTPException
from typing import Callable
from src.services.permissions import check_permission
import logging

logger = logging.getLogger(__name__)


class RBACRoute(APIRoute):
    """APIRoute subclass that enforces RBAC per-endpoint based on __required_permission__ metadata."""

    def get_route_handler(self) -> Callable:
        original_route_handler = super().get_route_handler()

        async def custom_route_handler(request: Request) -> Callable:
            # Identify required permission from endpoint (supports wrappers via __wrapped__)
            required_permission = None
            endpoint = self.endpoint
            current = endpoint
            while current is not None:
                required_permission = getattr(current, '__required_permission__', None)
                if required_permission:
                    break
                current = getattr(current, '__wrapped__', None)

            if required_permission:
                # Determine actor
                actor = None
                auth_hdr = request.headers.get('authorization')
                x_requester = request.headers.get('x-requester')
                if auth_hdr:
                    try:
                        from src.web.auth import validate_admin_token
                        admin = validate_admin_token(auth_hdr)
                        if admin and admin.get('role'):
                            actor = admin.get('role')
                        elif admin and admin.get('id'):
                            actor = admin.get('id')
                    except Exception as e:
                        logger.debug(f"RBACRoute: validate_admin_token error: {e}")
                if actor is None and x_requester:
                    actor = x_requester
                if actor is None:
                    raise HTTPException(status_code=403, detail="Missing actor for permission check")
                if not check_permission(actor, required_permission):
                    raise HTTPException(status_code=403, detail=f"Permission denied for actor '{actor}' to perform '{required_permission}'")

            return await original_route_handler(request)

        return custom_route_handler
