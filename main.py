# -----------------------------------------
# 🗂️ Imports
# -----------------------------------------
import asyncio
import json
import re
import random
import httpx
import urllib.parse
from datetime import datetime
from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
from dotenv import load_dotenv
import os

try:
    from fuzzywuzzy import fuzz
    FUZZY_AVAILABLE = True
except ImportError:
    FUZZY_AVAILABLE = False

load_dotenv()

# -----------------------------------------
# 🔧 Config
# -----------------------------------------
app = FastAPI()

VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "DEMO_TOKEN")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
WORQNOW_API_URL = os.getenv("WORQNOW_API_URL", "https://api.worqnow.ai").rstrip("/")

WHATSAPP_API_URL = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages" if PHONE_NUMBER_ID else None

# -----------------------------------------
# 🧠 In-Memory Storage (demo — swap with MongoDB in production)
# -----------------------------------------
demo_users = {}       # wa_id -> { location }
demo_states = {}      # wa_id -> state string
demo_sessions = {}    # wa_id -> CV session
demo_user_jobs = {}   # wa_id -> [job, ...]  (current page)
demo_known_users = set()

# -----------------------------------------
# 🔤 Intent Map
# -----------------------------------------
intent_map = {
    "appreciation": [
        "thanks", "thank you", "thank u", "tnx", "i appreciate",
        "nice one", "good job", "well done"
    ],
    "profile":          ["profile", "my profile", "my settings", "show profile"],
    "help":             ["help", "menu", "options", "what can you do", "commands"],
    "learn":            ["learn", "learning", "learn something"],
    "tips":             ["tip", "tips", "career tip", "career advice"],
    "location":         ["my location is", "i am in", "set location", "change location", "i live in"],
    "job_search":       ["search", "find", "job", "jobs", "vacancy", "openings", "hiring"],
    "generate_cv":      ["cv", "resume", "write cv", "generate resume", "create cv", "build my cv"],
    "feedback":         ["feedback", "suggestion", "i have a suggestion"],
}

cv_questions = [
    "👤 What's your full name?",
    "💼 What is your professional title?",
    "📝 Write a short summary about yourself.",
    "🏢 List your past work experience (Company, Role, Duration).",
    "🎓 List your education (Degree, Institution, Year).",
    "🛠️ List your key skills (comma separated).",
    "📫 What's your email address?",
    "📞 Phone number?",
]

APPRECIATION_REPLIES = [
    "You're welcome! 😊",
    "Anytime! How else can I assist you?",
    "Always here to help — Team WorqNow 🤝",
    "No worries at all! 😊",
    "You're welcome! More wins ahead for you. 🌟",
]


# -----------------------------------------
# 🔍 Intent Matching
# -----------------------------------------
def match_intent(text: str):
    text_lower = text.lower()
    for intent, phrases in intent_map.items():
        for phrase in phrases:
            if FUZZY_AVAILABLE:
                if fuzz.partial_ratio(phrase.lower(), text_lower) > 85:
                    return intent
            else:
                if phrase in text_lower:
                    return intent
    return None


def extract_keywords(msg: str) -> str:
    msg = re.sub(
        r"\b(i'm|looking|searching|for|in|a|an|any|to|get|find|of|with|want|need|jobs|job)\b",
        "", msg, flags=re.IGNORECASE
    )
    return " ".join(msg.split())


# -----------------------------------------
# 🌐 WorqNow API Job Fetch (Free — no key required)
# -----------------------------------------
async def fetch_worqnow_jobs(query: str) -> list:
    url = f"{WORQNOW_API_URL}/api/v1/search"
    params = {"query": query, "page": 1, "num_pages": 1, "date_posted": "all"}

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            res = await client.get(url, params=params)
            res.raise_for_status()
            data = res.json().get("data", [])

        jobs = []
        for j in data:
            if not j.get("job_apply_link"):
                continue

            location_parts = []
            if j.get("job_city"):
                location_parts.append(j["job_city"])
            if j.get("job_country"):
                location_parts.append(j["job_country"])
            location = ", ".join(location_parts) if location_parts else ("Remote" if j.get("job_is_remote") else "")

            jobs.append({
                "title": j.get("job_title", ""),
                "company": j.get("employer_name", "Unknown"),
                "location": location,
                "url": j.get("job_apply_link"),
            })

        return jobs

    except Exception as e:
        print(f"❌ WorqNow API error: {e}")
        return []


# -----------------------------------------
# 🧹 URL Cleaner
# -----------------------------------------
def clean_job_url(url: str) -> str:
    try:
        parsed = urllib.parse.urlparse(url)
        if not parsed.query:
            return url
        params = urllib.parse.parse_qs(parsed.query)
        clean_params = {k: v for k, v in params.items() if not k.startswith("utm_")}
        query = urllib.parse.urlencode(clean_params, doseq=True)
        return urllib.parse.urlunparse((
            parsed.scheme, parsed.netloc, parsed.path,
            parsed.params, query, parsed.fragment
        ))
    except Exception:
        return url


# -----------------------------------------
# 💼 Job Message Formatter
# -----------------------------------------
def format_job_message(jobs: list, title: str) -> str:
    if not jobs:
        return "⚠️ No jobs found."

    lines = [f"🔥 *{title}*\n\n"]

    for i, job in enumerate(jobs, 1):
        clean_url = clean_job_url(job.get("url", ""))
        lines.append(f"{i}. 💼 *{job.get('title', 'Untitled')}*\n")
        lines.append(f"   🏢 {job.get('company', 'Unknown')}\n")
        if job.get("location"):
            lines.append(f"   📍 {job['location']}\n")
        lines.append(f"   👉 Apply: {clean_url}\n\n")

    lines.append("━━━━━━━━━━━━━━━\n")
    lines.append("💡 Type *HELP* to see all options")

    return "".join(lines)


# -----------------------------------------
# ✉️ Send WhatsApp Message
# -----------------------------------------
async def send_whatsapp_message(to: str, message: str):
    if not ACCESS_TOKEN or not WHATSAPP_API_URL:
        print(f"\n📨 [DEMO] To {to}:\n{message}\n")
        return

    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": message}
    }
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            res = await client.post(WHATSAPP_API_URL, headers=headers, json=payload)
            res.raise_for_status()
    except Exception as e:
        print(f"❌ Failed to send message: {e}")


async def send_typing_then_message(to: str, message: str, delay: float = 1.5):
    await asyncio.sleep(delay)
    await send_whatsapp_message(to, message)


# -----------------------------------------
# ✅ Webhook Verification
# -----------------------------------------
@app.get("/webhook")
async def verify_webhook(request: Request):
    params = dict(request.query_params)
    if params.get("hub.verify_token") == VERIFY_TOKEN:
        return PlainTextResponse(params.get("hub.challenge", ""), status_code=200)
    return PlainTextResponse("Wrong verify token", status_code=403)


# -----------------------------------------
# 📩 Main Webhook Handler
# -----------------------------------------
@app.post("/webhook")
async def handle_message(request: Request):
    body = await request.json()

    try:
        message = (
            body.get("entry", [{}])[0]
                .get("changes", [{}])[0]
                .get("value", {})
                .get("messages", [{}])[0]
        )
    except (IndexError, KeyError):
        return {"status": "ok"}

    wa_id = message.get("from")
    if not wa_id:
        return {"status": "ok"}

    text = (message.get("text", {}) or {}).get("body", "").strip()
    text_lower = text.lower().strip()

    # -----------------------------------------
    # ✅ New User Onboarding
    # -----------------------------------------
    if wa_id not in demo_known_users:
        demo_known_users.add(wa_id)
        demo_states[wa_id] = "awaiting_location"
        await send_typing_then_message(
            wa_id,
            "👋 Welcome to *WorqNow* – your personal job assistant!\n\n"
            "To get started, please tell me your preferred job location.\n\n"
            "📍 *Examples:*\n"
            "• Lagos\n• Sheffield\n• Toronto\n• Remote\n\n"
            "_Just type the city or country_"
        )
        return {"status": "ok"}

    # -----------------------------------------
    # 🚀 State Machine
    # -----------------------------------------
    state = demo_states.get(wa_id)

    if state == "awaiting_location":
        location = text.strip().title()
        if not location or len(location.split()) > 5:
            await send_typing_then_message(wa_id, "❗ Please enter just a city or country.\n\nExample: *Lagos* or *Remote*")
            return {"status": "ok"}
        demo_users[wa_id] = {"location": location}
        del demo_states[wa_id]
        await send_typing_then_message(
            wa_id,
            f"📍 Location set to *{location}*! 🎉\n\n"
            "Now type what job you're looking for.\n\n"
            "💼 *Examples:*\n"
            "• *Search frontend jobs*\n"
            "• *Search marketing remote*\n"
            "• *Jobs*\n\n"
            "Or type *HELP* to see all options."
        )
        return {"status": "ok"}

    if state == "awaiting_feedback":
        print(f"📝 Feedback from {wa_id}: {text}")
        await send_typing_then_message(wa_id, "✅ Thanks for your feedback! We really appreciate it. 💙")
        del demo_states[wa_id]
        return {"status": "ok"}

    # -----------------------------------------
    # 📝 CV Session Flow
    # -----------------------------------------
    if wa_id in demo_sessions:
        session = demo_sessions[wa_id]
        session["answers"].append(text.strip())
        session["step"] += 1

        if session["step"] >= len(cv_questions):
            cv = build_demo_cv(session["answers"])
            await send_typing_then_message(wa_id, cv)
            del demo_sessions[wa_id]
        else:
            await send_typing_then_message(wa_id, cv_questions[session["step"]])
        return {"status": "ok"}

    # -----------------------------------------
    # 🎯 Command Handlers
    # -----------------------------------------

    # JOBS
    if text_lower in ["jobs", "job"]:
        location = (demo_users.get(wa_id) or {}).get("location", "Remote")
        await send_typing_then_message(wa_id, f"🔍 Finding jobs for *{location}*...")
        results = await fetch_worqnow_jobs(f"jobs in {location}")
        if not results:
            await send_typing_then_message(wa_id, "⚠️ No jobs found right now. Try again shortly or search a keyword.")
            return {"status": "ok"}
        demo_user_jobs[wa_id] = results
        await send_typing_then_message(wa_id, format_job_message(results[:6], f"Top Jobs in {location}"))
        return {"status": "ok"}

    # SEARCH
    if text_lower.startswith(("search ", "find ")):
        query = text.split(" ", 1)[1].strip() if " " in text else ""
        if not query:
            await send_typing_then_message(wa_id, "❗ Example: *Search remote UI/UX*")
            return {"status": "ok"}
        await send_typing_then_message(wa_id, f"🔍 Searching for *{query}*...")
        results = await fetch_worqnow_jobs(query)
        if not results:
            await send_typing_then_message(wa_id, f"⚠️ No results for: *{query}*\n\nTry a different keyword.")
            return {"status": "ok"}
        demo_user_jobs[wa_id] = results
        await send_typing_then_message(wa_id, format_job_message(results[:6], f"Results: {query}"))
        return {"status": "ok"}

    # -----------------------------------------
    # 🎯 Intent Handlers
    # -----------------------------------------
    intent = match_intent(text)

    if text_lower in {"help", "menu", "options"}:
        intent = "help"
    elif text_lower in {"hi", "hello", "hey"}:
        await send_typing_then_message(
            wa_id,
            "👋 Hi! Welcome back to *WorqNow*.\n\n"
            "• Type *JOBS* to see jobs\n"
            "• Type *Search frontend* to search by keyword\n"
            "• Type *HELP* to see all options"
        )
        return {"status": "ok"}

    if intent == "help":
        await send_typing_then_message(
            wa_id,
            "👋 *WorqNow – Job Assistant*\n\n"
            "🔍 *Search Frontend* – Search jobs by keyword\n"
            "📌 *JOBS* – Browse jobs by your location\n"
            "🧾 *Build My CV* – Create your CV\n"
            "📍 *Set Location Lagos* – Update your location\n"
            "👤 *Profile* – View your preferences\n"
            "📘 *Learn* – Free learning resources\n"
            "💡 *Tips* – Career tips\n"
            "💬 *Feedback* – Share ideas\n\n"
            "💡 You can also just say what you want e.g.\n"
            "*Software jobs in London* or *Remote marketing jobs*"
        )

    elif intent == "profile":
        user = demo_users.get(wa_id, {})
        loc = user.get("location", "Not set")
        await send_typing_then_message(wa_id, f"👤 *Your Profile*\n\n📍 Location: {loc}")

    elif intent == "location":
        location = extract_keywords(text).title()
        demo_users[wa_id] = {"location": location}
        await send_typing_then_message(wa_id, f"📍 Location updated to *{location}*.")

    elif intent == "job_search":
        query = extract_keywords(text)
        if not query.strip():
            await send_typing_then_message(wa_id, "❗ Example: *Web developer remote*")
            return {"status": "ok"}
        await send_typing_then_message(wa_id, f"🔍 Searching for *{query}*...")
        results = await fetch_worqnow_jobs(query)
        if not results:
            await send_typing_then_message(wa_id, f"⚠️ No jobs found for: *{query}*\n\nTry a different keyword.")
            return {"status": "ok"}
        demo_user_jobs[wa_id] = results
        await send_typing_then_message(wa_id, format_job_message(results[:6], f"Results: {query}"))

    elif intent == "generate_cv":
        demo_sessions[wa_id] = {"step": 0, "answers": []}
        await send_typing_then_message(wa_id, cv_questions[0])

    elif intent == "learn":
        await send_typing_then_message(
            wa_id,
            "📚 *Learn Something New:*\n\n"
            "📘 Python – https://bit.ly/python-crash\n"
            "📗 HTML/CSS – https://bit.ly/html-css-learn\n"
            "📙 FreeCodeCamp – https://www.freecodecamp.org/"
        )

    elif intent == "tips":
        tips = [
            "Tailor your CV to each role — show results, not just duties.",
            "Apply within 24 hours of a posting — 3x higher callback rate!",
            "Follow up 5-7 days after applying — it shows initiative.",
            "Network referrals increase interview chances by 40%.",
            "Quality over quantity — 3 great apps beat 10 rushed ones.",
        ]
        await send_typing_then_message(wa_id, f"💡 *Career Tip:*\n\n{random.choice(tips)}")

    elif intent == "feedback":
        demo_states[wa_id] = "awaiting_feedback"
        await send_typing_then_message(wa_id, "🙏 We'd love your thoughts!\n\nSend your suggestion or feedback.")

    elif intent == "appreciation":
        await send_typing_then_message(wa_id, random.choice(APPRECIATION_REPLIES))

    else:
        await send_typing_then_message(
            wa_id,
            "Hmm, I'm not sure I got that 🤔\n\n"
            "Try:\n"
            "• *Search frontend jobs*\n"
            "• *Jobs*\n"
            "• *Build my CV*\n"
            "• Type *HELP* to see all options"
        )

    return {"status": "ok"}


# -----------------------------------------
# 📝 CV Builder (text-based demo)
# -----------------------------------------
def build_demo_cv(answers: list) -> str:
    fields = ["Name", "Title", "Summary", "Experience", "Education", "Skills", "Email", "Phone"]
    cv = "📄 *Your CV*\n\n"
    for label, value in zip(fields, answers):
        cv += f"*{label}:* {value}\n"
    cv += (
        "\n━━━━━━━━━━━━━━━\n"
        "💡 This is a text CV. Visit *worqnow.ai* for a full PDF version!"
    )
    return cv
