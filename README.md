# 🤖 Notes Submission Bot

A Telegram bot that automates the collection of academic notes and PYQs for LibraryHub.

---

## 🚀 Live Bot

👉 [LibraryHub Bot](https://telegram.me/LibraryhandlerBot)

---

## 🚀 Purpose

This bot acts as the **submission layer** of the system, allowing students to contribute notes without needing to create accounts.

---

## ⚙️ Workflow

1. User uploads notes via Telegram
2. Submission goes to moderation queue
3. Admin reviews the content
4. Approved files are stored in the central database
5. Instantly available on the website

---

## ✨ Features

* 📤 Easy file uploads (PDF, Docs, Images)
* 🧾 Metadata collection (subject, semester)
* 🛡️ Admin moderation system
* 🔄 Direct database integration
* ❌ No login/signup required

---

## 🧠 Why Telegram?

* Zero friction onboarding
* Already used by students
* Faster than building upload UI
* Reduces backend + auth complexity

---

## 🛠️ Tech Stack

* Python
* Telebot (pyTelegramBotAPI)
* Telegram Bot API
* Shared Database

---

## ⚙️ Setup

```bash id="bt1"
git clone https://github.com/ChikuX/notes-sharing-bot.git
cd notes-sharing-bot
pip install -r requirements.txt
```

```python id="bt2"
BOT_TOKEN = "your_token_here"
```

```bash id="bt3"
python bot.py
```

---

## 🔐 Moderation

All submissions are reviewed before publishing to ensure quality.

---

## 🔗 Related

👉 Website: [Click Here](https://campusvault.xyz/)   
👉 Repo: [Click Here](https://github.com/ChikuX/LibraryHub)

---

## 👨‍💻 Author
> Developed by Ankit  
> GitHub: [Click Here](https://github.com/ChikuX)    
> LinkedIn: [Click Here](https://www.linkedin.com/in/ankit1706/)
