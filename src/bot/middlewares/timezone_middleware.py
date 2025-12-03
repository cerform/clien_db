from aiogram import BaseMiddleware

class TimezoneMiddleware(BaseMiddleware):
    def __init__(self, default_tz: str):
        super().__init__()
        self.default_tz = default_tz

    async def __call__(self, handler, event, data):
        data["timezone"] = self.default_tz
        return await handler(event, data)
