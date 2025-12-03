"""Admin keyboards"""
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

def admin_menu():
    """Admin main menu"""
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton("👥 Clients"), KeyboardButton("👨‍🎨 Masters")],
        [KeyboardButton("📅 Bookings"), KeyboardButton("➕ Add Master")],
        [KeyboardButton("🔔 Pending Approvals")]
    ], resize_keyboard=True)

def admin_actions_kb():
    """Admin action buttons"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Approve", callback_data="admin_approve"),
         InlineKeyboardButton(text="❌ Reject", callback_data="admin_reject")],
        [InlineKeyboardButton(text="🔄 Edit", callback_data="admin_edit"),
         InlineKeyboardButton(text="🗑 Delete", callback_data="admin_delete")]
    ])
