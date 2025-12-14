"""
Role-Based Access Control (RBAC) system for tattoo salon.

Defines four roles:
- SUPER_ADMIN: Full system access, can manage all users and data
- ADMIN: Can manage bookings, clients, view all calendars
- MASTER: Can view own calendar, bookings, order materials
- INKA: AI bot with limited access for client interactions
"""

from enum import Enum
from typing import Set, List, Dict, Any


class Role(str, Enum):
    """User roles in the system."""
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    MASTER = "master"
    INKA = "inka"


class Permission(str, Enum):
    """Granular permissions for different operations."""
    # Dashboard & Monitoring
    VIEW_DASHBOARD = "view_dashboard"
    VIEW_MONITORING = "view_monitoring"
    RUN_TESTS = "run_tests"

    # User Management
    CREATE_USERS = "create_users"
    EDIT_USERS = "edit_users"
    DELETE_USERS = "delete_users"
    VIEW_ALL_USERS = "view_all_users"
    CHANGE_USER_ROLES = "change_user_roles"

    # Master Management
    HIRE_MASTER = "hire_master"
    FIRE_MASTER = "fire_master"
    VIEW_ALL_MASTERS = "view_all_masters"
    EDIT_MASTER = "edit_master"

    # Client Management
    VIEW_ALL_CLIENTS = "view_all_clients"
    VIEW_OWN_CLIENTS = "view_own_clients"
    EDIT_CLIENT = "edit_client"
    DELETE_CLIENT = "delete_client"
    VIEW_CLIENT_HISTORY = "view_client_history"

    # Booking Management
    VIEW_ALL_BOOKINGS = "view_all_bookings"
    VIEW_OWN_BOOKINGS = "view_own_bookings"
    CREATE_BOOKING = "create_booking"
    EDIT_BOOKING = "edit_booking"
    CANCEL_BOOKING = "cancel_booking"

    # Calendar Management
    VIEW_ALL_CALENDARS = "view_all_calendars"
    VIEW_OWN_CALENDAR = "view_own_calendar"
    EDIT_ALL_CALENDARS = "edit_all_calendars"
    EDIT_OWN_CALENDAR = "edit_own_calendar"

    # Materials Management
    ORDER_MATERIALS = "order_materials"
    VIEW_MATERIAL_ORDERS = "view_material_orders"
    APPROVE_MATERIAL_ORDERS = "approve_material_orders"

    # Database Access
    DIRECT_DB_ACCESS = "direct_db_access"
    BACKUP_DATABASE = "backup_database"
    RESTORE_DATABASE = "restore_database"

    # AI & Bot
    ACCESS_INKA_ADMIN = "access_inka_admin"
    CONFIGURE_BOT = "configure_bot"
    VIEW_BOT_LOGS = "view_bot_logs"

    # Statistics & Reports
    VIEW_ALL_STATS = "view_all_stats"
    VIEW_OWN_STATS = "view_own_stats"
    EXPORT_REPORTS = "export_reports"


# Role-Permission mapping
ROLE_PERMISSIONS: Dict[Role, Set[Permission]] = {
    Role.SUPER_ADMIN: {
        # Full access to everything
        Permission.VIEW_DASHBOARD,
        Permission.VIEW_MONITORING,
        Permission.RUN_TESTS,
        Permission.CREATE_USERS,
        Permission.EDIT_USERS,
        Permission.DELETE_USERS,
        Permission.VIEW_ALL_USERS,
        Permission.CHANGE_USER_ROLES,
        Permission.HIRE_MASTER,
        Permission.FIRE_MASTER,
        Permission.VIEW_ALL_MASTERS,
        Permission.EDIT_MASTER,
        Permission.VIEW_ALL_CLIENTS,
        Permission.VIEW_OWN_CLIENTS,
        Permission.EDIT_CLIENT,
        Permission.DELETE_CLIENT,
        Permission.VIEW_CLIENT_HISTORY,
        Permission.VIEW_ALL_BOOKINGS,
        Permission.VIEW_OWN_BOOKINGS,
        Permission.CREATE_BOOKING,
        Permission.EDIT_BOOKING,
        Permission.CANCEL_BOOKING,
        Permission.VIEW_ALL_CALENDARS,
        Permission.VIEW_OWN_CALENDAR,
        Permission.EDIT_ALL_CALENDARS,
        Permission.EDIT_OWN_CALENDAR,
        Permission.ORDER_MATERIALS,
        Permission.VIEW_MATERIAL_ORDERS,
        Permission.APPROVE_MATERIAL_ORDERS,
        Permission.DIRECT_DB_ACCESS,
        Permission.BACKUP_DATABASE,
        Permission.RESTORE_DATABASE,
        Permission.ACCESS_INKA_ADMIN,
        Permission.CONFIGURE_BOT,
        Permission.VIEW_BOT_LOGS,
        Permission.VIEW_ALL_STATS,
        Permission.VIEW_OWN_STATS,
        Permission.EXPORT_REPORTS,
    },

    Role.ADMIN: {
        # Can manage bookings, clients, view all calendars
        Permission.VIEW_DASHBOARD,
        Permission.VIEW_MONITORING,
        Permission.VIEW_ALL_MASTERS,
        Permission.VIEW_ALL_CLIENTS,
        Permission.EDIT_CLIENT,
        Permission.VIEW_CLIENT_HISTORY,
        Permission.VIEW_ALL_BOOKINGS,
        Permission.CREATE_BOOKING,
        Permission.EDIT_BOOKING,
        Permission.CANCEL_BOOKING,
        Permission.VIEW_ALL_CALENDARS,
        Permission.VIEW_MATERIAL_ORDERS,
        Permission.APPROVE_MATERIAL_ORDERS,
        Permission.VIEW_BOT_LOGS,
        Permission.VIEW_ALL_STATS,
        Permission.EXPORT_REPORTS,
    },

    Role.MASTER: {
        # Can view own calendar, bookings, order materials
        Permission.VIEW_OWN_CLIENTS,
        Permission.VIEW_CLIENT_HISTORY,
        Permission.VIEW_OWN_BOOKINGS,
        Permission.CREATE_BOOKING,
        Permission.EDIT_BOOKING,
        Permission.VIEW_OWN_CALENDAR,
        Permission.EDIT_OWN_CALENDAR,
        Permission.ORDER_MATERIALS,
        Permission.VIEW_OWN_STATS,
    },

    Role.INKA: {
        # AI bot with limited access
        Permission.VIEW_OWN_CLIENTS,
        Permission.EDIT_CLIENT,
        Permission.VIEW_CLIENT_HISTORY,
        Permission.VIEW_OWN_BOOKINGS,
        Permission.CREATE_BOOKING,
        Permission.VIEW_OWN_CALENDAR,
    }
}


def get_role_permissions(role: Role) -> Set[Permission]:
    """Get all permissions for a role."""
    return ROLE_PERMISSIONS.get(role, set())


def has_permission(role: Role, permission: Permission) -> bool:
    """Check if a role has a specific permission."""
    return permission in get_role_permissions(role)


def filter_bookings_by_role(role: Role, master_id: str, all_bookings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Filter bookings based on role permissions."""
    if has_permission(role, Permission.VIEW_ALL_BOOKINGS):
        return all_bookings
    elif has_permission(role, Permission.VIEW_OWN_BOOKINGS):
        return [b for b in all_bookings if b.get('master_id') == master_id]
    else:
        return []


def filter_calendars_by_role(role: Role, master_id: str, all_calendars: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Filter calendars based on role permissions."""
    if has_permission(role, Permission.VIEW_ALL_CALENDARS):
        return all_calendars
    elif has_permission(role, Permission.VIEW_OWN_CALENDAR):
        return [c for c in all_calendars if c.get('master_id') == master_id]
    else:
        return []


def filter_clients_by_role(role: Role, master_id: str, all_clients: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Filter clients based on role permissions."""
    if has_permission(role, Permission.VIEW_ALL_CLIENTS):
        return all_clients
    elif has_permission(role, Permission.VIEW_OWN_CLIENTS):
        return [c for c in all_clients if c.get('master_id') == master_id]
    else:
        return []


def can_edit_calendar(role: Role, master_id: str, calendar_master_id: str) -> bool:
    """Check if user can edit a specific calendar."""
    if has_permission(role, Permission.EDIT_ALL_CALENDARS):
        return True
    if has_permission(role, Permission.EDIT_OWN_CALENDAR) and master_id == calendar_master_id:
        return True
    return False


def can_manage_booking(role: Role, master_id: str, booking_master_id: str) -> bool:
    """Check if user can manage a specific booking."""
    if has_permission(role, Permission.VIEW_ALL_BOOKINGS):
        return True
    if has_permission(role, Permission.VIEW_OWN_BOOKINGS) and master_id == booking_master_id:
        return True
    return False
