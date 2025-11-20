from fastapi import FastAPI, Request
from utils import detect_intent
from job_api import mock_job_search

app = FastAPI()

# -------------------------------
# Webhook Verification
# -------------------------------
@app.get("/webhook")
async def verify_webhook(request: Request):
    params = dict(request.query_params)
    if params.get("hub.verify_token") == "your_verify_token":
        return int(params.get("hub.challenge", "0"))
    return "Invalid verification token"


# -------------------------------
# Handle Webhook Messages
# -------------------------------
@app.post("/webhook")
async def handle_webhook(request: Request):
    data = await request.json()
    print("📩 Incoming webhook:", data)

    message = (
        data.get("entry", [{}])[0]
           .get("changes", [{}])[0]
           .get("value", {})
           .get("messages", [{}])[0]
    )

    text = message.get("text", {}).get("body", "").lower().strip()

    # Basic intent detection
    intent = detect_intent(text)

    if intent == "job":
        jobs = mock_job_search(text)
        response = "🔍 *Demo Job Results:*\n\n"
        for j in jobs:
            response += f"💼 {j['title']}\n🏢 {j['company']}\n🔗 {j['url']}\n\n"
        print(response)
        return {"status": "ok"}

    elif intent == "cv":
        return {"status": "ok", "message": "CV builder demo page: templates/cv_demo.html"}

    else:
        print("🤖 Default reply: help or commands")
        return {"status": "ok"}
