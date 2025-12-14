"""
INKA ACL helper: enforce that code paths talking to DB from INKA have proper permissions
"""
from typing import List

# Minimal role-based access matrix
ROLE_PERMISSIONS = {
    'inka_llm_runtime': {
        'read': ['services', 'masters_public', 'availability_view', 'pricing', 'faq_approved'],
        'write': ['lead_requests', 'booking_drafts', 'conversation_logs', 'services']
    },
    'inka_booking_agent': {
        'read': ['availability_lock_view', 'masters', 'availability_view'],
        'write': ['bookings_pending', 'calendar_sync_queue', 'slot_locks']
    },
    'inka_learning_agent': {
        'read': ['learning_*'],
        'write': ['learning_rules', 'learning_faq', 'learning_style']
    },
    'inka_analytics_readonly': {
        'read': ['bookings_stats_view', 'conversion_metrics', 'faq_usage', 'dialog_outcomes']
    }
}


def can_write(role: str, table: str) -> bool:
    allowed = ROLE_PERMISSIONS.get(role, {}).get('write', [])
    if '*' in allowed:
        return True
    # allow prefix matches for learning_* etc
    for a in allowed:
        if a.endswith('*') and table.startswith(a[:-1]):
            return True
    return table in allowed


def can_read(role: str, table: str) -> bool:
    # A role that can write to a table should generally be allowed to read it as well.
    perms = ROLE_PERMISSIONS.get(role, {})
    allowed = perms.get('read', []) + perms.get('write', [])
    if '*' in allowed:
        return True
    for a in allowed:
        if a.endswith('*') and table.startswith(a[:-1]):
            return True
    return table in allowed
