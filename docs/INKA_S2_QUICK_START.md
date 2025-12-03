# INKA S2 Booking Engine — Quick Start

## Для кого это руководство?

Для разработчиков, которые хотят **быстро интегрировать S2 Booking Engine** в свой проект.

---

## За 5 минут

### 1️⃣ Импортируй модули

```python
from src.services.inka_ai import INKA
from src.services.inka_booking_engine import INKABookingEngine, BookingEngineStage
```

### 2️⃣ Инициализируй INKA

```python
inka = INKA()
```

### 3️⃣ Используй S2 для предложения слотов

```python
# Получи слоты из БД
available_slots = [
    {
        "slot_id": "S-1",
        "date": "2025-12-12",
        "start_time": "14:00",
        "end_time": "18:00",
        "available": True
    },
    {
        "slot_id": "S-2",
        "date": "2025-12-14",
        "start_time": "15:00",
        "end_time": "19:00",
        "available": True
    }
]

# Обработай через S2
result = inka.process_s2_booking(
    available_slots=available_slots,
    stage="offer_slots"
)

# Отправь клиенту
await message.answer(result['message'])

# Создай inline keyboard
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(
            text=slot['display_text'],
            callback_data=f"slot_{slot['slot_id']}"
        )]
        for slot in result['formatted_slots']
    ]
)

await message.answer(result['message'], reply_markup=keyboard)
```

### 4️⃣ Обработай выбор слота

```python
@router.callback_query(lambda c: c.data.startswith("slot_"))
async def handle_slot_selection(callback: types.CallbackQuery):
    slot_id = callback.data.replace("slot_", "")
    
    # Найди выбранный слот в БД
    selected_slot = db.get_slot_by_id(slot_id)
    
    # Проверь доступность
    slot_taken = not selected_slot['available']
    
    # Обработай через S2
    result = inka.process_s2_booking(
        available_slots=[],  # Не нужно для confirming_choice
        stage="confirming_choice",
        selected_slot=selected_slot,
        slot_taken=slot_taken
    )
    
    # Отправь подтверждение
    await callback.message.answer(result['message'])
    
    if result['success']:
        # Передай в S3 для финального бронирования
        await book_slot(selected_slot)
    else:
        # Предложи другие варианты
        await offer_slots_again(callback.message)
```

**Готово!** 🚀

---

## Полный пример Telegram бота

```python
from aiogram import Bot, Dispatcher, Router, types
from aiogram.filters import Command
from src.services.inka_ai import INKA

router = Router()
inka = INKA()

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "Привет! Я ИНКА, ассистент Ани. Чем могу помочь?"
    )

@router.message()
async def handle_message(message: types.Message):
    # S1: Классификация
    result = inka.process(
        message=message.text,
        client_context={"client_id": message.from_user.id}
    )
    
    # Если нужно предложить слоты → S2
    if result['next_action'] == 'offer_slots':
        # Получи слоты из БД
        slots = get_available_slots(
            booking_type=result['classification']['booking_type']
        )
        
        # Обработай через S2
        s2_result = inka.process_s2_booking(
            available_slots=slots,
            stage="offer_slots"
        )
        
        # Создай кнопки
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(
                    text=slot['display_text'],
                    callback_data=f"slot_{slot['slot_id']}"
                )]
                for slot in s2_result['formatted_slots']
            ]
        )
        
        await message.answer(
            s2_result['message'],
            reply_markup=keyboard
        )
    else:
        # Обычный ответ S1
        await message.answer(result['response'])

@router.callback_query(lambda c: c.data.startswith("slot_"))
async def handle_slot_selection(callback: types.CallbackQuery):
    slot_id = callback.data.replace("slot_", "")
    
    # Получи слот из БД
    selected_slot = get_slot_by_id(slot_id)
    
    if not selected_slot or not selected_slot['available']:
        # Слот занят
        result = inka.process_s2_booking(
            available_slots=[],
            stage="confirming_choice",
            selected_slot=selected_slot or {"slot_id": slot_id},
            slot_taken=True
        )
        
        await callback.message.answer(result['message'])
        await callback.answer()
        return
    
    # Подтверждение
    result = inka.process_s2_booking(
        available_slots=[],
        stage="confirming_choice",
        selected_slot=selected_slot,
        slot_taken=False
    )
    
    await callback.message.answer(result['message'])
    
    # Забронируй слот (S3)
    booking_id = book_slot(
        client_id=callback.from_user.id,
        slot_id=slot_id
    )
    
    await callback.answer("Готово!")

# Запуск бота
async def main():
    bot = Bot(token="YOUR_BOT_TOKEN")
    dp = Dispatcher()
    dp.include_router(router)
    
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

---

## Запуск примеров

```bash
# Запусти примеры использования
python examples_s2_booking_engine.py
```

**Вывод:**
```
🚀 INKA S2 BOOKING ENGINE - USAGE EXAMPLES

============================================================
EXAMPLE 1: Offering Slots
============================================================
Message to client:
Вот ближайшие свободные окна:

— 12.12 в 14:00
— 14.12 в 15:00
— 15.12 в 12:00

Нажми на удобный вариант, и я закреплю время.

Has slots: True
Slot count: 3
============================================================
```

---

## Make.com интеграция

### Webhook для S2 из Python бота:

```python
import requests

# После S1 классификации, если next_action == "offer_slots"
webhook_url = "https://hook.make.com/your-s2-webhook"

payload = {
    "client_id": message.from_user.id,
    "client_name": message.from_user.first_name,
    "route": result['classification']['route'],
    "stage": "offer_slots",
    "booking_type": result['classification']['booking_type']
}

response = requests.post(webhook_url, json=payload)
```

### В Make.com:

1. **Webhook** → получи данные
2. **Google Sheets** → получи слоты
3. **OpenAI** → используй System Prompt из `INKA_S2_BOOKING_ENGINE_PROMPT.md`
4. **Telegram Bot** → отправь сообщение + inline keyboard

**Подробнее**: `docs/INKA_S2_MAKE_INTEGRATION.md`

---

## System Prompts

### Для S2 (offer_slots):

```python
prompts = inka.get_system_prompts()

print(prompts['s2_offer_slots_prompt'])
```

**Или используй готовый файл**:  
`docs/INKA_S2_BOOKING_ENGINE_PROMPT.md`

---

## Тестирование

```python
# Тест 1: Предложение слотов
result = inka.process_s2_booking(
    available_slots=[
        {"slot_id": "S-1", "date": "2025-12-12", "start_time": "14:00", "end_time": "18:00"}
    ],
    stage="offer_slots"
)

assert result['has_slots'] == True
assert "12.12" in result['message']

# Тест 2: Нет слотов
result = inka.process_s2_booking(
    available_slots=[],
    stage="offer_slots"
)

assert result['has_slots'] == False
assert "нет" in result['message'].lower()

# Тест 3: Подтверждение
result = inka.process_s2_booking(
    available_slots=[],
    stage="confirming_choice",
    selected_slot={"slot_id": "S-1", "date": "2025-12-12", "start_time": "14:00"},
    slot_taken=False
)

assert result['success'] == True
assert "записала" in result['message'].lower()
```

---

## FAQ

### Где хранятся слоты?

В Google Sheets, таблица `Slots`:

| slot_id | date | start_time | end_time | available | booking_type |
|---------|------|------------|----------|-----------|--------------|
| S-1 | 2025-12-12 | 14:00 | 18:00 | YES | tattoo |

### Как обновить доступность слота?

```python
# После бронирования
db.update_slot(slot_id, available=False)
```

### ИНКА придумывает даты?

Нет! ИНКА использует **только** слоты из массива `available_slots`.  
Проверь System Prompt — там есть жёсткий запрет:  
**"Тебе запрещено добавлять новые даты"**

### Можно использовать без OpenAI?

Да! `INKABookingEngine` работает без API:

```python
booking_engine = INKABookingEngine()

result = booking_engine.generate_slot_offer_message(available_slots)
print(result['message'])  # Готовое сообщение
```

---

## Что дальше?

1. ✅ Интегрируй S2 в Telegram бота
2. ✅ Настрой Make.com (см. `INKA_S2_MAKE_INTEGRATION.md`)
3. ✅ Протестируй все сценарии
4. ✅ Создай S3 (Confirmation & Payment)

---

## Документация

- 📘 **Полная документация S2**: `docs/INKA_S2_BOOKING_ENGINE_PROMPT.md`
- 🔗 **Make.com интеграция**: `docs/INKA_S2_MAKE_INTEGRATION.md`
- 🎯 **Примеры использования**: `examples_s2_booking_engine.py`
- 🧪 **API Reference**: `src/services/inka_booking_engine.py`

---

**Готово! Начинай использовать S2 Booking Engine! 🚀**
