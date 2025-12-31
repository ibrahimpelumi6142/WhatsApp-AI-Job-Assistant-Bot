# 📱 WorqNow – WhatsApp AI Job Assistant (Public Demo)

A clean **public demo** of a WhatsApp-based AI Job Assistant built using **FastAPI**.  
This demo showcases:

- WhatsApp webhook handling  
- Intent recognition  
- Job search example (mocked)  
- CV builder example (mocked)  
- Structured conversation flow  
- Clean single-file architecture  

⚠️ **NOTE:**  
This is a **safe demo version**. The real production WorqNow bot contains:

- Real job APIs (Remotive / JSearch)  
- MongoDB user storage  
- PDF CV generator  
- WhatsApp media uploads  
- Daily alerts scheduler  
- Advanced NLU + fuzzy matching  
- Onboarding & subscription engine  
- User preference tracking  
- Business logic  

Those features are **intentionally removed** from this public demo.

---

## ✨ Features (Demo Version)

- 🔗 WhatsApp Webhook Receiver  
- 🧠 Simple Intent Detection  
- 🔍 Mock Job Search Flow  
- 📝 Mock CV Builder (Q&A Flow)  
- 💬 Typing Indicator (simulated)  
- 🗂 Clean Structure  
- ⚡ FastAPI Backend  
- 🛡 Safe and GitHub-friendly  

---

## 🗂 Project Structure

```
worqnow-demo/
│
├── main.py               # Full demo logic (single file)
├── README.md             # Project documentation
├── .env.example          # Demo verify token
├── module
|   └── university-advisor # Various university details for students that want to study more
|
├── sample_payloads/
│   ├── incoming_message.json
│   └── status_update.json
│
└── templates/
    └── cv_demo.html      # Minimal CV layout (demo)
```

---

## 🚀 Getting Started

### 1️⃣ Clone the Repository

```bash
git clone https://github.com/<your-username>/worqnow-demo
cd worqnow-demo
```

### 2️⃣ Install Dependencies

```bash
pip install fastapi uvicorn python-multipart
```

*(No databases or external APIs needed for this demo.)*

---

## 🔧 Environment Setup

Create your `.env` file:

```bash
cp .env.example .env
```

`.env` content:

```
VERIFY_TOKEN=DEMO_TOKEN
```

Used only for webhook verification.

---

## ▶️ Run the Server

```bash
uvicorn main:app --reload --port=8000
```

Visit:

```
http://localhost:8000/webhook?hub.verify_token=DEMO_TOKEN&hub.challenge=123
```

If everything works, you’ll see:

```
123
```

---

## 🧪 Testing Incoming Messages

Send this JSON using Postman/curl:

```json
{
  "entry": [{
    "changes": [{
      "value": {
        "messages": [{
          "from": "234801000000",
          "text": { "body": "search frontend jobs" }
        }]
      }
    }]
  }]
}
```

Your terminal will print the simulated job results.

---

## 🎯 Supported Demo Commands

| Command | What It Does |
|--------|-----------------------------|
| **search UI/UX** | Returns mock job listings |
| **create cv** | Starts CV builder demo |
| **profile** | Shows demo profile |
| **help** | Shows available demo commands |
| **feedback** | Records mock feedback |

---

## 🧩 Additional Demo Files

### `templates/cv_demo.html`  
A minimal HTML CV layout (demo only).

### `sample_payloads/`  
Realistic WhatsApp payloads for learning how Webhooks work.

---

## 🏆 Purpose of This Demo

This repository is designed to:

- Demonstrate WhatsApp automation with FastAPI  
- Serve as a **safe open-source portfolio project**  
- Show my architecture skills  
- Help others learn how WhatsApp Cloud API works  

The real production WorqNow bot remains private.

---

## 📝 License

MIT License — free to use, modify, and learn from.
