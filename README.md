# 🌙 DreamPatternWeb

> *Your dreams are more than memories — they're patterns waiting to be understood.*

DreamPatternWeb is an AI-powered dream journaling platform where you can log, analyze, and explore your dreams through intelligent insights, interactive visualizations, and even a little fun along the way.

---

## ✨ Features

### 📖 Dream Journal
Record your dreams in rich detail — describe what you saw, felt, and experienced. Tag your entries with **themes** and **categories** to build a personalized dream library over time.

### 🤖 AI Dream Analysis
Let artificial intelligence decode the hidden meanings behind your dreams. Each dream entry can be analyzed instantly, surfacing patterns, emotions, and symbolic interpretations you might have missed.

### 💬 Interactive Dream Chatbot
Have a conversation *about* your dream. Ask questions, explore details, and dive deeper into what your subconscious might be telling you — all through a natural AI-powered chat experience.

> 🔒 AI Chat and AI Analysis require an **active subscription**.

### 🔍 Dream Search
Looking for that dream you had last month about flying? Use the powerful search feature to filter and find any dream by keyword, theme, emotion, or category.

### 📊 Analytics Dashboard
Visualize your dream data — track recurring emotions, most common themes, dream frequency over time, and personal patterns. Your dream history, beautifully charted.

### 🗓️ Timeline & History
Browse your dreams chronologically through an interactive calendar timeline. Travel through months and rediscover forgotten nights.

### 🕹️ Flappy Bird Mini-Game
Because sometimes your brain just needs a break. Play a built-in Flappy Bird game to unwind — with a leaderboard to compete with other dreamers.

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python, Flask |
| Database | MySQL |
| AI / Chat | Groq API |
| Frontend | HTML, CSS, JavaScript |
| Deployment | Heroku (Gunicorn) |

---

## 🚀 Getting Started

### 1. Clone the repository
```bash
git clone https://github.com/abbass-aoun/DreamPatternWeb.git
cd DreamPatternWeb
```

### 2. Create and activate virtual environment
```bash
python -m venv venv
venv\Scripts\activate      # Windows
source venv/bin/activate   # Mac/Linux
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Set up environment variables
Create a `.env` file in the root directory:
```
SECRET_KEY=your_secret_key
GROQ_API_KEY=your_groq_api_key
```

### 5. Set up the database
Run the SQL files in order:
```
ProjectDB.sql
GAME_SYSTEM_DATABASE.sql
DREAM_FEATURES_DATABASE.sql
GAMES_LEADERBOARD_DATABASE.sql
```

### 6. Run the app
```bash
python appl.py
```

Visit `http://127.0.0.1:5000` in your browser.

---

## 📁 Project Structure

```
DreamPatternWeb/
├── routes/          # Flask route handlers
├── templates/       # HTML templates
├── static/          # CSS, JS, assets
├── database/        # Database helpers
├── appl.py          # App entry point
├── requirements.txt
└── Procfile         # For deployment
```

---

## 👤 Author

**Abbass Aoun**  
Built with 💙 as a full-stack web development project.

---

*Sweet dreams.* 🌠
