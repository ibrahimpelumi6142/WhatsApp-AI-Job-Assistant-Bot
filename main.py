import json
import re
from fastapi import FastAPI, Request

app = FastAPI()

# -----------------------------------------
# Mock Storage (demo only — no database)
# -----------------------------------------
demo_users = {}
demo_states = {}
demo_sessions = {}

# -----------------------------------------
# Intent map (real structure preserved)
# -----------------------------------------
intent_map = {
    "profile": ["profile", "my profile", "my settings"],
    "subscribe": ["subscribe", "start alerts"],
    "unsubscribe": ["unsubscribe", "stop alerts"],
    "help": ["help", "hi", "hello", "menu"],
    "learn": ["learn", "learning"],
    "tips": ["tips", "career tip"],
    "location": ["location", "set location", "i live in"],
    "personalized_jobs": ["my jobs", "recommended jobs"],
    "job_search": ["search", "find", "job", "jobs"],
    "generate_cv": ["cv", "resume", "create cv"],
    "feedback": ["feedback", "suggestion"],
}

cv_questions = [
    "👤 What's your full name?",
    "💼 What is your professional title?",
    "📝 Write a short summary about yourself.",
    "🏢 Your work experience?",
    "🎓 Your education?",
    "🛠️ Skills (comma separated)?",
    "📫 Email?",
    "📞 Phone number?",
]


# -----------------------------------------
# Intent matcher (safe, simplified)
# -----------------------------------------
def match_intent(text):
    text = text.lower()
    for intent, phrases in intent_map.items():
        for p in phrases:
            if p in text:
                return intent
    return None


# -----------------------------------------
# Typing indicator (demo)
# -----------------------------------------
async def send_typing(to, msg=None):
    print(f"\n💬 [Typing to {to}] {msg or ''}")


# -----------------------------------------
# WhatsApp send (demo only)
# -----------------------------------------
async def send_message(to, message):
    print(f"\n📨 Sending to {to}:\n{message}\n")


# -----------------------------------------
# Mock job search (no API calls)
# -----------------------------------------
def demo_job_search(query):
    return [
        {
            "title": "Frontend Developer (Demo)",
            "company": "DemoCorp",
            "location": "Remote",
            "url": "https://example.com/frontend",
        },
        {
            "title": "UI/UX Designer (Demo)",
            "company": "DesignStudio",
            "location": "Remote",
            "url": "https://example.com/uiux",
        },
    ]


# -----------------------------------------
# Format job list nicely
# -----------------------------------------
def format_job_list(jobs, title="Top Jobs"):
    msg = f"🔥 *{title}*\n\n"
    for i, j in enumerate(jobs, 1):
        msg += (
            f"{i}. 💼 *{j['title']}*\n"
            f"🏢 {j['company']} | 🌍 {j['location']}\n"
            f"🔗 {j['url']}\n\n"
        )
    return msg


# -----------------------------------------
# Demo CV (NO PDF generation)
# -----------------------------------------
def build_demo_cv(answers):
    return (
        "📝 *Your CV (Demo)*\n\n"
        f"👤 Name: {answers[0]}\n"
        f"💼 Title: {answers[1]}\n"
        f"📄 Summary: {answers[2]}\n"
        f"🏢 Experience: {answers[3]}\n"
        f"🎓 Education: {answers[4]}\n"
        f"🛠 Skills: {answers[5]}\n"
        f"📧 Email: {answers[6]}\n"
        f"📞 Phone: {answers[7]}\n"
    )


# -----------------------------------------
# Webhook Verification
# -----------------------------------------
@app.get("/webhook")
async def verify(request: Request):
    params = dict(request.query_params)
    if params.get("hub.verify_token") == "DEMO_TOKEN":
        return int(params.get("hub.challenge", 0))
    return "Invalid token"


# -----------------------------------------
# Webhook Post Handler
# -----------------------------------------
@app.post("/webhook")
async def webhook(request: Request):
    body = await request.json()
    print("\n📩 Incoming Webhook:")
    print(json.dumps(body, indent=2))

    message = (
        body.get("entry", [{}])[0]
            .get("changes", [{}])[0]
            .get("value", {})
            .get("messages", [{}])[0]
    )

    wa_id = message.get("from")
    text = message.get("text", {}).get("body", "").strip()
    intent = match_intent(text)

    # -----------------------------------------
    # CV FLOW (demo)
    # -----------------------------------------
    if wa_id in demo_sessions:
        session = demo_sessions[wa_id]
        step = session["step"]
        session["answers"].append(text)
        step += 1

        if step >= len(cv_questions):
            cv = build_demo_cv(session["answers"])
            await send_message(wa_id, cv)
            del demo_sessions[wa_id]
            return {"status": "ok"}

        demo_sessions[wa_id]["step"] = step
        await send_message(wa_id, cv_questions[step])
        return {"status": "ok"}

    # -----------------------------------------
    # INTENT HANDLERS (demo only)
    # -----------------------------------------
    if intent == "help":
        await send_message(
            wa_id,
            "👋 *WorqNow Demo*\n\n"
            "Try:\n"
            "🔍 Search UI/UX\n"
            "📝 Create CV\n"
            "📍 Set location\n"
            "👤 Profile"
        )
        return {"status": "ok"}

    if intent == "job_search":
        jobs = demo_job_search(text)
        msg = format_job_list(jobs, "Demo Job Results")
        await send_message(wa_id, msg)
        return {"status": "ok"}

    if intent == "generate_cv":
        demo_sessions[wa_id] = {"step": 0, "answers": []}
        await send_message(wa_id, cv_questions[0])
        return {"status": "ok"}

    if intent == "profile":
        await send_message(wa_id, "👤 *Demo Profile*\n📍 Location: Not saved in demo\n🔔 Subscription: None")
        return {"status": "ok"}

    if intent == "location":
        loc = text.replace("location", "").strip().title()
        await send_message(wa_id, f"📍 Location set to: *{loc}* (demo)")
        return {"status": "ok"}

    if intent == "feedback":
        await send_message(wa_id, "🙏 Thanks! Your feedback has been recorded (demo).")
        return {"status": "ok"}

    # Default fallback
    await send_message(wa_id, "🤖 I didn’t understand. Type *help*.")
    return {"status": "ok"}
