"""Simple permission manager for roles and actors

This module contains a small permission map used to check whether a given actor
is allowed to perform an action on the database. It's intentionally simple and
super extensible for future enhancements (RBAC, ACL, external auth providers).
"""
from typing import Dict

ROLE_PERMISSIONS = {
    'superadmin': ['*'],
    'admin': ['*'],
    'inka': [
        'get_clients', 'add_client', 'edit_client', 'get_masters', 'get_services',
        'add_booking', 'confirm_booking', 'complete_booking', 'cancel_booking'
    ],
    'bot': [
        'get_clients', 'get_masters', 'get_services'
    ],
}


def check_permission(actor: str, action: str) -> bool:
    """Return True if actor can perform action.

    Actor could be a role name (admin, inka) or user id string that maps to a role.
    For now, we expect caller to pass either a role or the alias 'inka' for the assistant.
    """
    if not actor:
        return False
    if actor == 'superadmin':
        return True
    role = actor.lower()
    perms = ROLE_PERMISSIONS.get(role, [])
    if '*' in perms:
        return True
    return action in perms
