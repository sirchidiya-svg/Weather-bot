# 🌦️ WeatherBot — Telegram Weather Bot

A real-time Telegram weather bot built with Python. Get current conditions and 5-day forecasts for any city worldwide, or share your GPS location for instant results.

---

## Features

- 🌡️ Current weather with temperature, humidity, wind, visibility, and more
- 📅 5-day forecast with daily high/low and rain probability
- 📍 Location-based weather via GPS sharing
- 🔄 Inline refresh button to update weather on demand
- 🌍 Supports any city worldwide

---

## Project Structure

```
weatherbot/
├── bot.py               # Main bot logic
├── requirements.txt     # Python dependencies
├── .env                 # API keys (never commit this!)
├── .gitignore           # Keeps secrets out of Git
└── README.md            # This file
```

---

## Local Setup

### 1. Clone the repo
```bash
git clone https://github.com/YOUR_USERNAME/weatherbot.git
cd weatherbot
```

### 2. Create a virtual environment
```bash
python -m venv venv
source venv/bin/activate      # On Windows: venv\Scripts\activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure environment variables
Copy `.env` and fill in your keys:
```bash
cp .env .env.local   # optional, or just edit .env directly
```

Set your values:
```
TELEGRAM_TOKEN=your_telegram_bot_token_here
WEATHER_API_KEY=your_openweathermap_api_key_here
```

### 5. Load .env in bot.py
Add this near the top of `bot.py` (after imports):
```python
from dotenv import load_dotenv
load_dotenv()
```

### 6. Run the bot
```bash
python bot.py
```

---

## Getting API Keys

### Telegram Bot Token
1. Open Telegram and search for **@BotFather**
2. Send `/newbot` and follow the prompts
3. Copy the token provided

### OpenWeatherMap API Key
1. Sign up at [openweathermap.org](https://openweathermap.org/api)
2. Go to **API keys** in your dashboard
3. Copy your default key (or generate a new one)
> Free tier supports up to 1,000 calls/day — more than enough.

---

## Deployment

See the [Railway Deployment](#railway-deployment) section or the hosting guide in this repo.

---

## Bot Commands

| Command | Description |
|---|---|
| `/start` | Welcome message & menu |
| `/weather <city>` | Current weather for a city |
| `/forecast <city>` | 5-day forecast for a city |
| `/help` | Show help message |

You can also just **type any city name** directly — no command needed.

---

## License

MIT — free to use and modify.
