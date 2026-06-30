# 📱 WorqNow – WhatsApp AI Job Assistant (Open Source)

A **fully working** WhatsApp-based AI Job Assistant built with **FastAPI**.  
Clone it, add your WhatsApp credentials, and it works instantly - with **real job results**.

---

## ✨ Features

- 🔗 WhatsApp Webhook Handler  
- 🧠 Fuzzy Intent Recognition (fuzzywuzzy)  
- 🔍 Real Job Search via WorqNow API (free, no key required)  
- 📝 CV Builder (Q&A flow, text output)  
- 👋 Onboarding Flow (location setup)  
- 💬 Typing Indicator simulation  
- 💡 Career Tips  
- 📚 Learning Resources  
- 💬 Feedback Collection  
- ⚡ FastAPI Backend - single file, clean structure  

---

## 🗂 Project Structure

```
worqnow-whatsapp-bot/
│
├── main.py               # Full bot logic (single file)
├── requirements.txt      # Dependencies
├── .env.example          # Environment variable template
├── README.md             # Documentation
│
├── modules/
│   └── university_advisor/  # University info for students
│
└── templates/
    └── cv_demo.html         # Sample CV layout
```

---

## 🚀 Getting Started

### 1️⃣ Clone the Repository

```bash
git clone https://github.com/ibrahimpelumi6142/WhatsApp-AI-Job-Assistant-Bot
cd WhatsApp-AI-Job-Assistant-Bot
```

### 2️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

### 3️⃣ Set Up Environment

```bash
cp .env.example .env
```

Fill in your `.env`:

```
VERIFY_TOKEN=your_webhook_verify_token
ACCESS_TOKEN=your_whatsapp_access_token
PHONE_NUMBER_ID=your_phone_number_id
WORQNOW_API_URL=https://api.worqnow.ai
```

> Get your WhatsApp credentials from [Meta for Developers](https://developers.facebook.com/apps/)

### 4️⃣ Run the Server

```bash
uvicorn main:app --reload --port=8000
```

### 5️⃣ Expose with ngrok (for WhatsApp webhook)

```bash
ngrok http 8000
```

Set your webhook URL in Meta dashboard to:
```
https://your-ngrok-url.ngrok.io/webhook
```

---

## 🧪 Test Without WhatsApp

Send a POST request via Postman or curl:

```json
{
  "entry": [{
    "changes": [{
      "value": {
        "messages": [{
          "from": "2348010000000",
          "id": "msg_001",
          "text": { "body": "search frontend jobs" }
        }]
      }
    }]
  }]
}
```

Without WhatsApp credentials set, responses print to terminal automatically.

---

## 🎯 Supported Commands

| Command | What It Does |
|---|---|
| **JOBS** | Browse jobs based on your location |
| **Search frontend** | Search real jobs by keyword |
| **Build my CV** | Start the CV builder flow |
| **Set location Lagos** | Update your job location |
| **Profile** | View your saved preferences |
| **Learn** | Free learning resources |
| **Tips** | Get a career tip |
| **Feedback** | Send feedback |
| **Help** | See all commands |

---

## 🌐 WorqNow Job API

This bot uses the **WorqNow Job Search API** - free for developers, no API key required.

```
https://api.worqnow.ai/api/v1/search?query=frontend+jobs
```

---

## 🏆 About WorqNow

WorqNow is an AI-powered job assistant delivered via WhatsApp.  
This open-source version is a working foundation - the production app includes additional features kept private.

🌍 Visit [worqnow.ai](https://worqnow.ai) for the full experience.

---

## 📝 License

MIT License - free to use, modify, and build on.
