"""
RBAC middleware for FastAPI: parse incoming requests and attach `request.state.role` and `request.state.role_source`.
- For bots and INKA flows, clients may set a special header or JWT: 'X-INKA-ROLE: inka_llm_runtime' or token in Authorization header.
- Admin tokens validated via existing `parse_admin_token` in app.py
- This middleware keeps things simple: it maps recognized tokens/headers to a specific role. It does not perform DB-level user mapping here.
"""
from fastapi import Request
from typing import Callable
import os


async def rbac_middleware(request: Request, call_next: Callable):
    # default role is None
    request.state.role = None
    request.state.role_source = None

    # If admin token parsed earlier, set admin role
    admin_id = getattr(request.state, 'admin_id', None)
    if admin_id:
        request.state.role = 'admin'
        request.state.role_source = 'admin_token'
        return await call_next(request)

    # Check for INKA-specific header
    role_hdr = request.headers.get('X-INKA-ROLE') or request.headers.get('x-inka-role')
    if role_hdr:
        request.state.role = role_hdr
        request.state.role_source = 'header'
        return await call_next(request)

    # Optional: check for JWT with role claim
    auth = request.headers.get('Authorization') or request.headers.get('authorization')
    if auth and auth.startswith('Bearer '):
        token = auth.split(' ', 1)[1]
        # If token is of format inka_token_<role>
        if token.startswith('inka_token_'):
            role = token.split('_', 2)[2] if '_' in token else 'inka_llm_runtime'
            request.state.role = role
            request.state.role_source = 'inka_token'
            return await call_next(request)

    # No role detected
    return await call_next(request)
