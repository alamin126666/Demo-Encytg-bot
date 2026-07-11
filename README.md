# 🔐 HTML Obfuscator Telegram Bot

HTML / CSS / JS কোড obfuscate করার Telegram Bot।  
Render-এ host করা যাবে, GitHub থেকে auto-deploy।

---

## ✨ Features

- HTML / CSS / JS → hex + random pattern obfuscation
- Output: `<script>...</script>` ব্লকে
- `.html` ফাইল upload সাপোর্ট
- বড় output → `.html` ফাইলে পাঠানো হয়
- Render-ready (webhook mode)

---

## 🚀 Deploy করার পদ্ধতি

### Step 1 — Telegram Bot তৈরি করুন

1. [@BotFather](https://t.me/BotFather) তে যান
2. `/newbot` command দিন
3. Bot name ও username দিন
4. **BOT_TOKEN** কপি করে রাখুন

---

### Step 2 — GitHub-এ Push করুন

```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/html-obf-bot.git
git push -u origin main
```

---

### Step 3 — Render-এ Deploy করুন

1. [render.com](https://render.com) → **New → Web Service**
2. GitHub repo connect করুন
3. Settings:
   - **Runtime:** Python
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python bot.py`
4. **Environment Variables** যোগ করুন:

| Key | Value |
|-----|-------|
| `BOT_TOKEN` | আপনার BotFather token |
| `WEBHOOK_URL` | `https://your-app-name.onrender.com` |
| `PORT` | `10000` |

5. **Deploy** করুন → URL নোট করুন
6. `WEBHOOK_URL` এ Render app URL বসান

---

## 🧪 Local Test

```bash
pip install -r requirements.txt
export BOT_TOKEN="your_token_here"
python bot.py   # polling mode চালু হবে (WEBHOOK_URL না থাকলে)
```

---

## 📂 Project Structure

```
html-obf-bot/
├── bot.py            # Main bot
├── requirements.txt  # Dependencies
├── render.yaml       # Render config
├── .gitignore
└── README.md
```

---

## ⚙️ কীভাবে Obfuscation কাজ করে

1. HTML কে character-by-character `\xHH` hex-এ convert করা হয়
2. Random chunk size-এ array-এ ভাগ করা হয়
3. Random variable name generate হয়
4. Noise / dummy variable যোগ হয়
5. `document['wri'+'te'](decoder(array.join('')))` pattern ব্যবহার হয়
6. Output: একটি self-contained `<script>` ব্লক
