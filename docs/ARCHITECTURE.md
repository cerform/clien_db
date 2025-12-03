# Architecture

Layered architecture:
- **bot**: Aiogram handlers, FSM, keyboards
- **services**: Business logic (booking, calendar, client, master, admin)
- **db**: Google Sheets wrapper and repositories (clients, masters, calendar, bookings)
- **utils**: Logging, timezone, validation
- **interfaces**: Abstract interfaces for extensibility

Database: Single Google Spreadsheet with 4 tabs
- clients: id, telegram_id, name, phone, email, notes, created_at
- masters: id, name, calendar_id, specialties, active, created_at
- calendar: date, master_id, slot_start, slot_end, available, note
- bookings: id, client_id, master_id, date, slot_start, slot_end, status, created_at, google_event_id
