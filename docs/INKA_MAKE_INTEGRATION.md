# 🤖 INKA AI System - Make.com Integration Guide

## Overview

INKA is a three-in-one AI assistant that automatically switches between three roles:
1. **Classifier (S1)**: Determines what the client wants
2. **Consultant-Seller**: Responds professionally without pressure
3. **Booking Assistant**: Guides toward booking

---

## 📋 Architecture

```
CLIENT MESSAGE
    ↓
[S1: CLASSIFIER]  ← Determines route, stage, booking_type
    ↓
┌─────────────────────────────────────────────────┐
│                                                 │
├→ BOOKING     → [BOOKING ASSISTANT] → S2 Engine
├→ CONSULTATION → [CONSULTANT] ↓ then → S2 Engine
├→ INFO        → [CONSULTANT] ↓ then → S2 Engine  
├→ OTHER       → [CONSULTANT] ↓ then → option to book
└─────────────────────────────────────────────────┘
    ↓
CLIENT GETS RESPONSE + BOOKING OPTIONS
```

---

## 🎯 Classification Routes

The classifier determines one of 6 routes:

| Route | When | Next Action |
|-------|------|-------------|
| `booking` | "хочу записаться", "когда есть время" | Offer slots (S2) |
| `booking_confirm` | Selecting specific time: "12-го в 14:00" | Confirm & save (S3) |
| `booking_reschedule` | "перенести запись" (if has active booking) | Offer new slots |
| `consultation` | "идея тату", "что посоветуешь" | Consultant responds |
| `info` | "больно ли", "цена", "уход" | Consultant answers |
| `other` | Unclear / small talk | Clarification or consultant |

### Booking Types

When route = `booking*`, classifier determines booking_type:

| Type | Indicators | Duration |
|------|------------|----------|
| `tattoo` | Any full design mention | 60-240+ min |
| `walk-in` | "маленькая", "быстро", "на сегодня" | 30-120 min |
| `consultation` | "обсудить идею", "рефы" | 30 min |

---

## 🔧 Integration in Make.com

### Setup Overview

```
TELEGRAM BOT
    ↓
[WEBHOOK/POLLING]
    ↓
[PARSE MESSAGE]
    ↓
┌─────────────────────────────────────────────────────┐
│  [CLASSIFIER] → Determine route                      │
├─────────────────────────────────────────────────────┤
│ IF route = consultation/info/other:                 │
│   [CONSULTANT BOT] → Get AI response                │
│ ELSE IF route = booking*:                           │
│   [TRANSITION] → "Show slots?"                      │
│ ELSE:                                               │
│   [DEFAULT] → "Let me help"                         │
└─────────────────────────────────────────────────────┘
    ↓
[SEND RESPONSE to client]
    ↓
[IF ready_for_booking → S2 Engine]
```

---

## 💬 System Prompts for Make.com

### 1️⃣ CONSULTATION/INFO/COMMUNICATION Branch

**Where to paste**: Set this in Make.com Webhook → **System Prompt field**

```
Ты — ИНКА, персональный ассистент тату-мастера Ани.

Тебе доверено три роли одновременно:
 1. Классификатор намерений (определяешь, что клиент хочет).
 2. Консультант-продавец, который общается мягко и профессионально.
 3. Ассистент записи, который помогает клиенту попасть в календарь.

Ты работаешь в Telegram-формате: коротко, тёпло, по делу, без навязчивости.

🟥 ЖЁСТКИЕ ЗАПРЕТЫ (важно):

Ты НЕ можешь:
 • придумывать даты, слоты, время,
 • предлагать свободные дни без данных,
 • называть стоимость, если инфы нет в контексте,
 • давать медицинские советы,
 • спорить с клиентом,
 • писать длинные лекции,
 • предлагать перенести запись без факта существующей booking,
 • осуждать, оценивать идеи,
 • обещать то, чего нет.

🟧 ТВ ТЕБЯ ВЫЗЫВАЮТ, КОГДА:

- Клиент спрашивает о боли, уходе, стоимости, месте для тату
- Клиент делится идеей / рефами / концепцией
- Сообщение неясное / small talk / не распознаётся

Твой тон:
✓ Профессиональный, спокойный, дружелюбный
✓ Без агрессивных продаж
✓ Без сухой бюрократии
✓ Краткие, живые сообщения (1-2 предложения)
✓ Стиль Ани: тёплый, уважительный, без сюсюкалки

Твое поведение:
1. Слушай внимательно, что просит клиент
2. Задай 1–2 уточняющих вопроса, если нужно
3. Объясни возможности (но НЕ придумывай даты/цены/слоты)
4. Если человек готов записаться → мягко предложи:
   "Хорошо, могу показать свободные варианты. Хочешь посмотреть время?"

🟪 ПРИМЕРЫ:

❓ "Больно ли делать тату?"
📱 "Ощущения индивидуальны — зависит от места и болевого порога. Аня подберёт место и подготовит. Где ты думаешь сделать?"

❓ "У меня идея: птица и волны"
📱 "Звучит красиво! Это большая работа или компактная? И у тебя есть рефы?"

❓ "Хочу записаться на маленькую"
📱 "Хорошо! Хочешь посмотреть свободные варианты?"

🔥 ЗАПОМНИ:

Никогда не смешивай JSON и текст.
Выдавай только человеческий, теплый текст ответа.
Если сомневаешься → спроси уточняющий вопрос.
Будь как Ани: опытная, теплая, без давления.
```

---

### 2️⃣ CLASSIFIER Module (Optional - for Python backend)

If you want the classifier to run server-side before Make.com:

```python
from src.services.inka_ai import INKA, INKAClassifier

classifier = INKAClassifier()
result = classifier.classify(
    message="когда можно записаться?",
    has_active_booking=False
)

# Returns:
# {
#   "route": "booking",
#   "stage": "offer_slots", 
#   "booking_type": "tattoo",
#   "intent_summary": "Client wants to book tattoo appointment",
#   "confidence": 0.85
# }
```

---

## 🚀 Step-by-Step Make.com Setup

### Step 1: Create CONSULTATION/INFO/COMMUNICATION webhook

1. In Make.com, create new scenario
2. Add **Telegram Bot → Wait for Webhook** trigger
3. Set webhook URL: `https://hook.make.com/...`
4. Configure request parsing

### Step 2: Parse incoming message

```javascript
// Extract relevant fields
{
  "user_id": data.from.id,
  "message": data.message.text,
  "username": data.from.username,
  "first_name": data.from.first_name,
  "has_booking": false  // check from database
}
```

### Step 3: Call OpenAI with INKA system prompt

**HTTP Module Setup:**
- **URL**: `https://api.openai.com/v1/chat/completions`
- **Method**: POST
- **Headers**:
  ```
  Authorization: Bearer {{YOUR_OPENAI_KEY}}
  Content-Type: application/json
  ```
- **Body**:
  ```json
  {
    "model": "gpt-3.5-turbo",
    "messages": [
      {
        "role": "system",
        "content": "[INSERT INKA SYSTEM PROMPT HERE]"
      },
      {
        "role": "user",
        "content": "{{message}}"
      }
    ],
    "temperature": 0.7,
    "max_tokens": 300
  }
  ```

### Step 4: Parse AI response

```javascript
// Extract response text
let response = data.choices[0].message.content;

// If response suggests booking → trigger S2 (slots)
let should_offer_slots = response.includes("свободные") || 
                         response.includes("варианты") ||
                         response.includes("посмотреть");
```

### Step 5: Send to Telegram

**Telegram Bot → Send Message**:
- **Chat ID**: `{{user_id}}`
- **Text**: `{{ai_response}}`

### Step 6: (Optional) If booking ready → trigger S2

If `should_offer_slots = true`:
- Call your S2 Booking Engine
- Pass: `booking_type`, `user_id`, `message`
- Offer available slots

---

## 📊 Classification Examples

### Example 1: Simple Booking Request
```
INPUT:
  message: "когда есть время на тату?"
  has_active_booking: false

OUTPUT:
  route: "booking"
  stage: "offer_slots"
  booking_type: "tattoo"
  intent_summary: "Client wants to book tattoo appointment"
  confidence: 0.85

ACTION: Show available slots (S2)
```

### Example 2: Design Consultation
```
INPUT:
  message: "Хочу тату с совой и луной, есть ли идеи?"
  has_active_booking: false

OUTPUT:
  route: "consultation"
  stage: "none"
  booking_type: "tattoo"
  intent_summary: "Client wants to discuss tattoo idea/design"
  confidence: 0.80

ACTION: Consultant responds, then optionally → booking
```

### Example 3: Info Question
```
INPUT:
  message: "сколько болит обычно? и как ухаживать?"
  has_active_booking: false

OUTPUT:
  route: "info"
  stage: "none"
  booking_type: "none"
  intent_summary: "Client asking for information (pain, care)"
  confidence: 0.75

ACTION: Consultant answers, then optionally → booking
```

### Example 4: Time Selection (Reschedule)
```
INPUT:
  message: "переносите на понедельник 14:00?"
  has_active_booking: true
  active_booking: { date: "2024-12-05", time: "16:00" }

OUTPUT:
  route: "booking_reschedule"
  stage: "offer_slots"
  booking_type: "tattoo"
  intent_summary: "Client wants to reschedule existing booking"
  confidence: 0.90

ACTION: Show available times for reschedule (S2)
```

---

## 🛑 What INKA Will NOT Do

❌ **Never Creates Slots**
```
DON'T: "Свободно 5-го в 14:00, 6-го в 16:00..."
DO: "Могу показать свободные варианты. Хочешь посмотреть?"
```

❌ **Never Invents Prices**
```
DON'T: "Маленькая тату 500 рублей, большая 1500..."
DO: "Стоимость зависит от размера и сложности. Аня обсудит."
```

❌ **Never Makes Medical Claims**
```
DON'T: "Тату безопасна, не волнуйся."
DO: "Ощущения индивидуальны. Аня подберёт место и подготовит."
```

❌ **Never Pressures Booking**
```
DON'T: "Быстро забронируй, мест мало!"
DO: "Хочешь посмотреть свободные варианты?"
```

---

## 🔄 Response Flow Summary

```
CLIENT MESSAGE
    ↓
[Classify Intent]
    ↓
┌─────────────────────────────────────────────┐
│ Route = booking?    → "Want to see slots?"  │
│ Route = consult?    → Consultant responds   │
│ Route = info?       → Consultant responds   │
│ Route = reschedule? → "Let me show options" │
│ Route = other?      → "How can I help?"     │
└─────────────────────────────────────────────┘
    ↓
[Send Response]
    ↓
[IF booking → offer S2 slots]
[ELSE → wait for next message]
```

---

## 📝 Configuration Checklist

- [ ] Copy INKA System Prompt to Make.com (Step 1)
- [ ] Set up OpenAI API key in Make.com
- [ ] Configure Telegram webhook
- [ ] Test with sample messages
- [ ] Verify routes work (booking, consultation, info)
- [ ] Ensure no slots are hardcoded
- [ ] Verify no prices are hardcoded
- [ ] Test reschedule flow (if applicable)
- [ ] Monitor logs for errors

---

## 🔗 Quick Integration Code

### Python: Using INKA in your bot

```python
from src.services.inka_ai import INKA

# Initialize
inka = INKA(api_key="your-openai-key")

# Process client message
result = inka.process(
    message="когда можно записаться?",
    client_context={
        "client_status": "active",
        "has_active_booking": False,
        "last_route": None
    }
)

# Use results
print(result["response"])  # Send to Telegram
if result["next_action"] == "offer_slots":
    # Trigger S2 booking engine
    pass
```

### Make.com: Minimal workflow

```
1. Telegram Webhook Trigger
   ↓
2. Parse message & context
   ↓
3. Call OpenAI (with INKA prompt)
   ↓
4. Parse response
   ↓
5. Send to Telegram
   ↓
6. (If booking ready) → Trigger S2
```

---

## 🆘 Troubleshooting

### Issue: INKA hallucinating slots/prices
**Solution**: Ensure system prompt includes the ЗАПРЕТЫ section

### Issue: Classifications not working
**Solution**: Check keyword lists in `INKAClassifier.__init__`

### Issue: Takes too long
**Solution**: Set `max_tokens: 300` in OpenAI call, use `gpt-3.5-turbo`

### Issue: Wrong language
**Solution**: INKA auto-detects Russian/English/Hebrew. No config needed.

---

## 📞 Support

For issues:
1. Check the **System Prompt** is fully copied
2. Verify **API key** is valid
3. Test with **sample messages** from classification examples
4. Review **Make.com logs** for API errors
5. Ensure **no hardcoded slots/prices** in workflow

---

## ✅ Ready to Deploy

Your INKA system is now ready for:
- ✅ Telegram bot consultation messages
- ✅ Automatic intent classification
- ✅ Professional, warm consultant responses
- ✅ Smooth transition to booking
- ✅ Respect for all constraints (no fake data)

**Next**: Deploy to Make.com and test! 🚀
