import os
import asyncio
import logging
import aiohttp
from datetime import datetime

# Load.env file if it exists (local development only)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "").strip()
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY", "").strip()
BASE_URL = "https://api.openweathermap.org/data/2.5"

if not TELEGRAM_TOKEN:
    raise RuntimeError("TELEGRAM_TOKEN environment variable is not set!")
if not WEATHER_API_KEY:
    raise RuntimeError("WEATHER_API_KEY environment variable is not set!")

WEATHER_EMOJIS = {
    "Clear": "☀️", "Clouds": "☁️", "Rain": "🌧️",
    "Drizzle": "🌦️", "Thunderstorm": "⛈️", "Snow": "❄️",
    "Mist": "🌫️", "Fog": "🌫️", "Haze": "🌫️",
    "Smoke": "💨", "Dust": "🌪️", "Sand": "🌪️",
    "Tornado": "🌪️", "Squall": "💨",
}

def get_weather_emoji(condition: str) -> str:
    return WEATHER_EMOJIS.get(condition, "🌡️")

def format_wind_direction(degrees: float) -> str:
    dirs = ["N","NE","E","SE","S","SW","W","NW"]
    return dirs[round(degrees / 45) % 8]

def celsius_to_fahrenheit(c: float) -> float:
    return round(c * 9/5 + 32, 1)

async def fetch_weather(city: str) -> dict | None:
    url = f"{BASE_URL}/weather"
    params = {"q": city, "appid": WEATHER_API_KEY, "units": "metric"}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as resp:
                if resp.status == 200:
                    return await resp.json()
                return None
    except Exception as e:
        logger.error(f"Error fetching weather: {e}")
        return None

async def fetch_forecast(city: str) -> dict | None:
    url = f"{BASE_URL}/forecast"
    params = {"q": city, "appid": WEATHER_API_KEY, "units": "metric", "cnt": 24}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as resp:
                if resp.status == 200:
                    return await resp.json()
                return None
    except Exception as e:
        logger.error(f"Error fetching forecast: {e}")
        return None

async def fetch_weather_by_coords(lat: float, lon: float) -> dict | None:
    url = f"{BASE_URL}/weather"
    params = {"lat": lat, "lon": lon, "appid": WEATHER_API_KEY, "units": "metric"}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as resp:
                if resp.status == 200:
                    return await resp.json()
                return None
    except Exception as e:
        logger.error(f"Error fetching weather by coords: {e}")
        return None

def format_current_weather(data: dict) -> str:
    city = data["name"]
    country = data["sys"]["country"]
    condition = data["weather"][0]["main"]
    description = data["weather"][0]["description"].title()
    emoji = get_weather_emoji(condition)
    temp_c = round(data["main"]["temp"], 1)
    temp_f = celsius_to_fahrenheit(temp_c)
    feels_c = round(data["main"]["feels_like"], 1)
    feels_f = celsius_to_fahrenheit(feels_c)
    humidity = data["main"]["humidity"]
    pressure = data["main"]["pressure"]
    visibility = data.get("visibility", 0) / 1000
    wind_speed = round(data["wind"]["speed"] * 3.6, 1)
    wind_deg = data["wind"].get("deg", 0)
    wind_dir = format_wind_direction(wind_deg)
    clouds = data["clouds"]["all"]
    sunrise = datetime.fromtimestamp(data["sys"]["sunrise"]).strftime("%H:%M")
    sunset = datetime.fromtimestamp(data["sys"]["sunset"]).strftime("%H:%M")
    updated = datetime.fromtimestamp(data["dt"]).strftime("%d %b %Y, %H:%M")

    return (
        f"{emoji} *Weather in {city}, {country}*\n"
        f"_{description}_\n\n"
        f"🌡️ *Temperature:* {temp_c}°C / {temp_f}°F\n"
        f"🤔 *Feels Like:* {feels_c}°C / {feels_f}°F\n"
        f"💧 *Humidity:* {humidity}%\n"
        f"🌬️ *Wind:* {wind_speed} km/h {wind_dir}\n"
        f"👁️ *Visibility:* {visibility:.1f} km\n"
        f"🌫️ *Pressure:* {pressure} hPa\n"
        f"☁️ *Cloud Cover:* {clouds}%\n"
        f"🌅 *Sunrise:* {sunrise} | 🌇 *Sunset:* {sunset}\n\n"
        f"🕐 _Updated: {updated}_"
    )

def format_forecast(data: dict) -> str:
    city = data["city"]["name"]
    country = data["city"]["country"]
    lines = [f"📅 *5-Day Forecast — {city}, {country}*\n"]

    seen_dates = {}
    for item in data["list"]:
        dt = datetime.fromtimestamp(item["dt"])
        date_str = dt.strftime("%A, %d %b")
        if date_str not in seen_dates:
            seen_dates[date_str] = []
        seen_dates[date_str].append(item)

    for date_str, items in list(seen_dates.items())[:5]:
        temps = [i["main"]["temp"] for i in items]
        min_t = round(min(temps), 1)
        max_t = round(max(temps), 1)
        condition = items[len(items)//2]["weather"][0]["main"]
        desc = items[len(items)//2]["weather"][0]["description"].title()
        emoji = get_weather_emoji(condition)
        rain_chance = max((i.get("pop", 0) * 100) for i in items)
        lines.append(
            f"{emoji} *{date_str}*\n"
            f" 🌡️ {min_t}°C – {max_t}°C | _{desc}_\n"
            f" 🌧️ Rain chance: {rain_chance:.0f}%\n"
        )

    return "\n".join(lines)

async def main():
    # Import telegram stuff HERE, after event loop exists
    from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
    from telegram.ext import (
        Application, CommandHandler, MessageHandler,
        CallbackQueryHandler, ContextTypes, filters
    )

    # ── Handlers ──────────────────────────────────────────────────────────────
    async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
        keyboard = [
            [InlineKeyboardButton("🌍 Share Location", callback_data="share_location")],
            [InlineKeyboardButton("🔍 Search City", callback_data="search_city")],
            [InlineKeyboardButton("ℹ️ Help", callback_data="help")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "👋 *Welcome to WeatherBot!*\n\n"
            "I provide accurate, real-time weather forecasts worldwide.\n\n"
            "Simply *send a city name* or *share your location* to get started!",
            parse_mode="Markdown",
            reply_markup=reply_markup,
        )

    async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        text = (
            "🤖 *WeatherBot Help*\n\n"
            "*Commands:*\n"
            "• /start — Welcome message\n"
            "• /weather `<city>` — Current weather\n"
            "• /forecast `<city>` — 5-day forecast\n"
            "• /help — Show this message\n\n"
            "*Quick Search:*\n"
            "Just type any city name to get instant weather!\n\n"
            "*Location:*\n"
            "Share your GPS location using the 📎 attachment button.\n\n"
            "*Examples:*\n"
            "`Lagos` • `/weather Abuja` • `/forecast London`"
        )
        await (update.message or update.callback_query.message).reply_text(
            text, parse_mode="Markdown"
        )

    async def weather_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not context.args:
            await update.message.reply_text(
                "❌ Please provide a city name.\nExample: `/weather Lagos`",
                parse_mode="Markdown"
            )
            return
        city = " ".join(context.args)
        await send_weather(update, city)

    async def forecast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not context.args:
            await update.message.reply_text(
                "❌ Please provide a city name.\nExample: `/forecast Abuja`",
                parse_mode="Markdown"
            )
            return
        city = " ".join(context.args)
        await send_forecast(update, city)

    async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
        city = update.message.text.strip()
        await send_weather(update, city)

    async def handle_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
        loc = update.message.location
        msg = await update.message.reply_text("📍 Fetching weather for your location...")
        data = await fetch_weather_by_coords(loc.latitude, loc.longitude)
        if data:
            city = data["name"]
            text = format_current_weather(data)
            keyboard = [[InlineKeyboardButton(
                "📅 5-Day Forecast", callback_data=f"forecast:{city}"
            )]]
            await msg.edit_text(text, parse_mode="Markdown",
                                reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            await msg.edit_text("❌ Couldn't fetch weather for your location. Try again.")

    async def send_weather(update: Update, city: str):
        msg = await update.message.reply_text(f"🔍 Fetching weather for *{city}*...",
                                              parse_mode="Markdown")
        data = await fetch_weather(city)
        if data:
            text = format_current_weather(data)
            keyboard = [[InlineKeyboardButton(
                "📅 5-Day Forecast", callback_data=f"forecast:{city}"
            ), InlineKeyboardButton(
                "🔄 Refresh", callback_data=f"refresh:{city}"
            )]]
            await msg.edit_text(text, parse_mode="Markdown",
                                reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            await msg.edit_text(
                f"❌ City *{city}* not found. Check the spelling and try again.",
                parse_mode="Markdown"
            )

    async def send_forecast(update: Update, city: str):
        msg = await update.message.reply_text(f"📅 Fetching forecast for *{city}*...",
                                              parse_mode="Markdown")
        data = await fetch_forecast(city)
        if data:
            await msg.edit_text(format_forecast(data), parse_mode="Markdown")
        else:
            await msg.edit_text(
                f"❌ City *{city}* not found.",
                parse_mode="Markdown"
            )

    async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()

        if query.data == "help":
            await help_command(update, context)
            return
        if query.data in ("share_location", "search_city"):
            hint = ("📍 Use the 📎 button → Location to share your GPS."
                    if query.data == "share_location"
                    else "🔍 Just type a city name, e.g. `Nairobi`")
            await query.message.reply_text(hint, parse_mode="Markdown")
            return

        action, _, city = query.data.partition(":")
        if action == "forecast":
            data = await fetch_forecast(city)
            if data:
                await query.message.reply_text(format_forecast(data), parse_mode="Markdown")
            else:
                await query.message.reply_text("❌ Forecast unavailable.")
        elif action == "refresh":
            data = await fetch_weather(city)
            if data:
                keyboard = [[InlineKeyboardButton(
                    "📅 5-Day Forecast", callback_data=f"forecast:{city}"
                ), InlineKeyboardButton(
                    "🔄 Refresh", callback_data=f"refresh:{city}"
                )]]
                await query.message.edit_text(
                    format_current_weather(data), parse_mode="Markdown",
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )

    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("weather", weather_command))
    app.add_handler(CommandHandler("forecast", forecast_command))
    app.add_handler(MessageHandler(filters.LOCATION, handle_location))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(CallbackQueryHandler(button_handler))

    logger.info("🤖 WeatherBot is running...")
    await app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    asyncio.run(main())
