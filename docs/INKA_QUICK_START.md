# 🚀 INKA Quick Start - Integration Guide

## For Developers

This guide shows how to integrate INKA AI into your tattoo bot.

---

## 1️⃣ Installation

The INKA module is already created at:
```
src/services/inka_ai.py
```

No additional packages needed beyond `openai`:
```bash
pip install openai
```

---

## 2️⃣ Basic Usage

### Import INKA

```python
from src.services.inka_ai import INKA, INKAClassifier

# Initialize with OpenAI API key
inka = INKA(api_key="your-openai-api-key-here")
```

### Process a Client Message

```python
result = inka.process(
    message="когда можно записаться на тату?",
    client_context={
        "client_status": "new",
        "has_active_booking": False,
    }
)

# Result structure:
# {
#   "classification": {
#       "route": "booking",
#       "stage": "offer_slots",
#       "booking_type": "tattoo",
#       "intent_summary": "Client wants to book tattoo appointment",
#       "confidence": 0.85,
#       "requires_human_review": False
#   },
#   "response": "Хорошо, могу показать свободные варианты. Хочешь посмотреть время?",
#   "booking_context": {...},
#   "next_action": "offer_slots",
#   "timestamp": "2024-12-03T..."
# }
```

---

## 3️⃣ Integration Patterns

### Pattern A: In Message Handler (Telegram Bot)

```python
from aiogram import types, Router
from src.services.inka_ai import INKA
from src.config.config import Config

router = Router()
inka = None  # Initialize in startup

@router.startup()
async def on_startup():
    global inka
    cfg = Config.from_env()
    inka = INKA(api_key=cfg.OPENAI_API_KEY)

@router.message()
async def handle_client_message(message: types.Message):
    """Handle any client message with INKA"""
    try:
        # Get client context from database
        client_context = await get_client_context(message.from_user.id)
        
        # Process with INKA
        result = inka.process(message.text, client_context)
        
        # Send response
        await message.answer(result["response"])
        
        # If booking ready, trigger next flow
        if result["next_action"] == "offer_slots":
            await handle_booking_flow(message, result["booking_context"])
        
    except Exception as e:
        logger.exception(f"INKA error: {e}")
        await message.answer("Извините, давайте попробуем еще раз.")
```

### Pattern B: In Admin Chat Service

```python
from src.services.inka_ai import INKAConsultant

consultant = INKAConsultant(api_key="your-key")

# For consultation/info routes
response = consultant.respond_to_consultation(
    message="Больно ли делать тату?",
    context={"booking_type": "tattoo"}
)
# "Ощущения индивидуальны - зависит от места..."
```

### Pattern C: Classification Only (No AI calls)

```python
from src.services.inka_ai import INKAClassifier

classifier = INKAClassifier()

# Fast, rule-based classification (no API cost)
classification = classifier.classify(
    message="переносите на понедельник?",
    has_active_booking=True,
    active_booking_info={"date": "2024-12-05"}
)

# Use classification to route to appropriate handler
if classification["route"] == "booking_reschedule":
    # Handle reschedule
    pass
```

---

## 4️⃣ Common Scenarios

### Scenario 1: New Client Booking

```python
message = "хочу записаться на тату"

result = inka.process(message)
# route: "booking"
# response: "Хорошо, могу показать свободные варианты..."
# next_action: "offer_slots"

# → Trigger booking slots display (S2 engine)
```

### Scenario 2: Design Consultation

```python
message = "Хочу тату с совой. Где лучше сделать?"

result = inka.process(message)
# route: "consultation"
# response: "Звучит красиво! Сова - интересный выбор. Мне нравится..."
# next_action: "continue_consultation"

# → Show more options or suggest booking
```

### Scenario 3: Info Question

```python
message = "Сколько времени займет? Больно ли?"

result = inka.process(message)
# route: "info"
# response: "Время зависит от размера. Ощущения индивидуальны..."
# next_action: "continue_consultation"

# → Offer to book after answering
```

### Scenario 4: Reschedule

```python
message = "Перенесите запись на среду"

result = inka.process(
    message,
    client_context={
        "has_active_booking": True,
        "active_booking_info": {"date": "2024-12-04"}
    }
)
# route: "booking_reschedule"
# response: "Хорошо, могу показать варианты на другие дни..."
# next_action: "offer_slots"

# → Show reschedule options
```

---

## 5️⃣ Getting System Prompts

For Make.com integration, get ready-made prompts:

```python
prompts = inka.consultant.get_system_prompts()

# Returns dict:
# {
#   "consultation_prompt": "Ты — ИНКА...",
#   "info_prompt": "Ты — ИНКА...",
#   "communication_prompt": "Ты — ИНКА...",
#   "general_prompt": "Ты — ИНКА..."
# }

# Copy "consultation_prompt" to Make.com System Prompt field
```

---

## 6️⃣ Classification Reference

### Routes

- **booking**: Client wants to book appointment → offer_slots
- **booking_confirm**: Client selecting specific time → confirm
- **booking_reschedule**: Client reschedule existing → offer_slots
- **consultation**: Client discussing design idea → consultant_response
- **info**: Client asking questions → consultant_response
- **other**: Unclear intent → clarify

### Booking Types

- **tattoo**: Full tattoo (default)
- **walk-in**: Quick session (2hr max)
- **consultation**: Design discussion only
- **none**: Not booking-related

### Stages

- **offer_slots**: Ready to show available times
- **waiting_client_choice**: Client reviewing options
- **confirming_choice**: Client confirmed selection
- **completed**: Booking confirmed
- **error**: Something went wrong
- **none**: Not applicable

---

## 7️⃣ Database Integration

Store classification results for context:

```python
# After processing message
result = inka.process(message, client_context)

# Save to database
await save_client_interaction(
    user_id=user_id,
    message=message,
    route=result["classification"]["route"],
    booking_type=result["classification"]["booking_type"],
    response=result["response"],
    timestamp=result["timestamp"]
)

# Next message uses this context
next_context = await get_client_context(user_id)
# Returns: last_route, last_stage, last_interaction, etc.
```

---

## 8️⃣ Error Handling

```python
try:
    result = inka.process(message, client_context)
except OpenAIError as e:
    logger.error(f"OpenAI API error: {e}")
    # Fallback to rule-based response
    result = inka.process(message)  # Uses _rule_based_response
except Exception as e:
    logger.exception(f"Unexpected error: {e}")
    # Send friendly message
    await message.answer("Извините, давайте попробуем еще раз.")
```

---

## 9️⃣ Testing

### Test Classification

```python
from src.services.inka_ai import INKAClassifier

classifier = INKAClassifier()

test_cases = [
    ("хочу записаться на тату", "booking"),
    ("идея тату с совой", "consultation"),
    ("больно ли?", "info"),
    ("перенесите запись", "booking_reschedule"),
    ("привет", "other"),
]

for message, expected_route in test_cases:
    result = classifier.classify(message)
    assert result["route"] == expected_route, f"Failed: {message}"
    print(f"✓ {message} → {result['route']}")
```

### Test Consultant

```python
from src.services.inka_ai import INKAConsultant

consultant = INKAConsultant()  # Without API key = fallback

response = consultant.respond_to_consultation(
    "Больно ли делать тату?",
    context={"booking_type": "tattoo"}
)
assert "индивидуально" in response.lower()
print(f"✓ Consultant response: {response}")
```

---

## 🔟 Configuration

### Environment Variables

Add to `.env`:
```dotenv
# Already in .env, verify it's set:
OPENAI_API_KEY=sk-...

# Optional: Override default model
INKA_MODEL=gpt-4  # default: gpt-3.5-turbo
```

### Customize Behavior

```python
# Create classifier with custom keywords
classifier = INKAClassifier()

# Add more booking keywords for your language
classifier.booking_keywords.extend([
    "запишите меня",
    "хочу",
    "назначить",
])

# All keywords are case-insensitive (converted to lowercase)
```

---

## 1️⃣1️⃣ Constraints (Do Not Violate)

INKA respects these HARD constraints:

### ❌ Never:
- Invent slot times (only suggest "show available")
- Hardcode prices/costs
- Give medical advice
- Pressure customers to book
- Write long lectures (keep responses 1-2 sentences)
- Promise things that don't exist
- Judge client's tattoo ideas

### ✅ Always:
- Ask clarifying questions (1-2 max)
- Be warm and professional
- Explain in simple terms
- Defer to master's expertise ("Аня обсудит...")
- Route to booking when client is ready
- Use client's language

---

## 1️⃣2️⃣ Next Steps

1. **Test locally** with `test_inka_classification()` examples above
2. **Integrate into handlers** using Pattern A/B/C
3. **Deploy to Make.com** using system prompts from step 5️⃣
4. **Monitor** classification confidence and adjust keywords if needed
5. **Iterate** based on real user conversations

---

## 📚 Full Module Documentation

For detailed API docs, see docstrings in:
```
src/services/inka_ai.py
```

Classes:
- `INKA`: Main orchestrator
- `INKAClassifier`: Intent classification
- `INKAConsultant`: Warm responses
- `INKABookingAssistant`: Booking preparation

---

## 🎯 You're Ready!

Your bot now has:
✅ Automatic intent classification  
✅ Professional consultant responses  
✅ Smooth booking transitions  
✅ Constraint enforcement (no fake data)  
✅ Multi-language support  

Deploy and test! 🚀
