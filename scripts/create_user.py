#!/usr/bin/env python3
"""
CLI tool for managing users (masters, admins, super admins) in the tattoo salon system.
"""

import os
import sys
import argparse
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.services.user_manager import UserManager
from src.auth.roles import Role


def create_super_admin(args):
    """Create a super admin user."""
    manager = UserManager()

    result = manager.create_master(
        name=args.name,
        phone=args.phone,
        telegram_id=args.telegram_id,
        role=Role.SUPER_ADMIN,
        username=args.username,
        password=args.password
    )

    if result['success']:
        print(f"\n✅ {result['message']}")
        print(f"\n⚠️  СОХРАНИТЕ ЭТИ ДАННЫЕ - пароль больше не будет показан!")
        print(f"\n📋 Информация для входа:")
        print(f"   Username: {result['username']}")
        print(f"   Password: {result['password']}")
        print(f"   Telegram ID: {args.telegram_id}")
        print(f"\n📱 Теперь отправьте /start боту с этого Telegram аккаунта")
    else:
        print(f"\n❌ Ошибка: {result['message']}")
        sys.exit(1)


def create_admin(args):
    """Create an admin user."""
    manager = UserManager()

    result = manager.create_master(
        name=args.name,
        phone=args.phone,
        telegram_id=args.telegram_id,
        role=Role.ADMIN,
        username=args.username,
        password=args.password
    )

    if result['success']:
        print(f"\n✅ {result['message']}")
        print(f"\n⚠️  СОХРАНИТЕ ЭТИ ДАННЫЕ - пароль больше не будет показан!")
        print(f"\n📋 Информация для входа:")
        print(f"   Username: {result['username']}")
        print(f"   Password: {result['password']}")
        if args.telegram_id:
            print(f"   Telegram ID: {args.telegram_id}")
    else:
        print(f"\n❌ Ошибка: {result['message']}")
        sys.exit(1)


def create_master(args):
    """Create a master user."""
    manager = UserManager()

    result = manager.create_master(
        name=args.name,
        phone=args.phone,
        telegram_id=args.telegram_id,
        role=Role.MASTER,
        username=args.username,
        password=args.password
    )

    if result['success']:
        print(f"\n✅ {result['message']}")
        print(f"\n⚠️  СОХРАНИТЕ ЭТИ ДАННЫЕ - пароль больше не будет показан!")
        print(f"\n📋 Информация для входа:")
        print(f"   Username: {result['username']}")
        print(f"   Password: {result['password']}")
        if args.telegram_id:
            print(f"   Telegram ID: {args.telegram_id}")
    else:
        print(f"\n❌ Ошибка: {result['message']}")
        sys.exit(1)


def list_users(args):
    """List all users."""
    manager = UserManager()
    users = manager.list_all_users()

    if not users:
        print("\n📋 Пользователей не найдено")
        return

    print("\n📋 Список всех пользователей:\n")
    print(f"{'ID':<12} {'Имя':<20} {'Роль':<15} {'Телефон':<15} {'Telegram ID':<15} {'Активен'}")
    print("-" * 100)

    for user in users:
        print(f"{user['id']:<12} {user['name']:<20} {user['role']:<15} {user['phone']:<15} {user.get('telegram_id', 'N/A'):<15} {'✅' if user['is_active'] else '❌'}")


def update_role(args):
    """Update user role."""
    manager = UserManager()
    result = manager.update_role(args.master_id, Role(args.role))

    if result['success']:
        print(f"\n✅ {result['message']}")
    else:
        print(f"\n❌ Ошибка: {result['message']}")
        sys.exit(1)


def deactivate_user(args):
    """Deactivate (fire) a user."""
    manager = UserManager()
    result = manager.deactivate_user(args.master_id)

    if result['success']:
        print(f"\n✅ {result['message']}")
    else:
        print(f"\n❌ Ошибка: {result['message']}")
        sys.exit(1)


def activate_user(args):
    """Activate (hire back) a user."""
    manager = UserManager()
    result = manager.activate_user(args.master_id)

    if result['success']:
        print(f"\n✅ {result['message']}")
    else:
        print(f"\n❌ Ошибка: {result['message']}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Управление пользователями системы тату-салона",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:

  # Создать суперадмина
  python scripts/create_user.py super-admin \\
    --name "Владимир Петров" \\
    --phone "+972501111111" \\
    --telegram-id "123456789"

  # Создать админа
  python scripts/create_user.py admin \\
    --name "Анна Иванова" \\
    --phone "+972502222222" \\
    --telegram-id "987654321"

  # Создать мастера
  python scripts/create_user.py master \\
    --name "Мария Сидорова" \\
    --phone "+972503333333"

  # Список всех пользователей
  python scripts/create_user.py list

  # Изменить роль
  python scripts/create_user.py update-role \\
    --master-id "abc-123" --role admin

  # Уволить (деактивировать)
  python scripts/create_user.py deactivate --master-id "abc-123"

  # Нанять обратно (активировать)
  python scripts/create_user.py activate --master-id "abc-123"
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Команда')

    # Super admin command
    super_admin_parser = subparsers.add_parser('super-admin', help='Создать суперадмина')
    super_admin_parser.add_argument('--name', required=True, help='Имя и фамилия')
    super_admin_parser.add_argument('--phone', required=True, help='Телефон (+972...)')
    super_admin_parser.add_argument('--telegram-id', required=True, help='Telegram ID (обязательно для суперадмина)')
    super_admin_parser.add_argument('--username', help='Username (опционально, будет сгенерирован)')
    super_admin_parser.add_argument('--password', help='Пароль (опционально, будет сгенерирован)')

    # Admin command
    admin_parser = subparsers.add_parser('admin', help='Создать админа')
    admin_parser.add_argument('--name', required=True, help='Имя и фамилия')
    admin_parser.add_argument('--phone', required=True, help='Телефон (+972...)')
    admin_parser.add_argument('--telegram-id', help='Telegram ID (опционально)')
    admin_parser.add_argument('--username', help='Username (опционально, будет сгенерирован)')
    admin_parser.add_argument('--password', help='Пароль (опционально, будет сгенерирован)')

    # Master command
    master_parser = subparsers.add_parser('master', help='Создать мастера')
    master_parser.add_argument('--name', required=True, help='Имя и фамилия')
    master_parser.add_argument('--phone', required=True, help='Телефон (+972...)')
    master_parser.add_argument('--telegram-id', help='Telegram ID (опционально)')
    master_parser.add_argument('--username', help='Username (опционально, будет сгенерирован)')
    master_parser.add_argument('--password', help='Пароль (опционально, будет сгенерирован)')

    # List command
    subparsers.add_parser('list', help='Список всех пользователей')

    # Update role command
    update_role_parser = subparsers.add_parser('update-role', help='Изменить роль пользователя')
    update_role_parser.add_argument('--master-id', required=True, help='ID пользователя')
    update_role_parser.add_argument('--role', required=True,
                                   choices=['super_admin', 'admin', 'master'],
                                   help='Новая роль')

    # Deactivate command
    deactivate_parser = subparsers.add_parser('deactivate', help='Уволить (деактивировать) пользователя')
    deactivate_parser.add_argument('--master-id', required=True, help='ID пользователя')

    # Activate command
    activate_parser = subparsers.add_parser('activate', help='Нанять обратно (активировать) пользователя')
    activate_parser.add_argument('--master-id', required=True, help='ID пользователя')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Execute command
    if args.command == 'super-admin':
        create_super_admin(args)
    elif args.command == 'admin':
        create_admin(args)
    elif args.command == 'master':
        create_master(args)
    elif args.command == 'list':
        list_users(args)
    elif args.command == 'update-role':
        update_role(args)
    elif args.command == 'deactivate':
        deactivate_user(args)
    elif args.command == 'activate':
        activate_user(args)


if __name__ == '__main__':
    main()
