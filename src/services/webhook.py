from fastapi import FastAPI, Request

app = FastAPI()

@app.post("/bot/webhook")
async def webhook(request: Request):
    data = await request.json()
    return {"ok": True}
