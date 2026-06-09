from flask import Flask, jsonify, request, render_template
import requests
import os
from dotenv import load_dotenv
import time

load_dotenv()

app = Flask(__name__)

LAT = 37.4323
LON = -121.8996

# Cache for weather and air quality data
weather_cache = {"data": None, "time": 0}
air_cache = {"data": None, "time": 0}
CACHE_DURATION = 300  # 5 minutes


# -----------------------------
# HELPERS
# -----------------------------

def fetch_weather():
    global weather_cache
    current_time = time.time()
    
    # Return cached data if still fresh
    if weather_cache["data"] and (current_time - weather_cache["time"]) < CACHE_DURATION:
        print(f"[WEATHER] Using cached data")
        return weather_cache["data"]
    
    try:
        url = (
            "https://api.open-meteo.com/v1/forecast"
            f"?latitude={LAT}&longitude={LON}&current_weather=true"
        )
        data = requests.get(url, timeout=10).json()
        cw = data["current_weather"]
        cel_temp = cw["temperature"]
        real_windspeed = cw["windspeed"]
        farenheit = round((cel_temp * 9/5) + 32)
        mph = real_windspeed * 0.621371
        real_mph = round(mph)
        result = {
            "temperature": farenheit,
            "windspeed": real_mph
        }
        weather_cache["data"] = result
        weather_cache["time"] = current_time
        print(f"[WEATHER] Success: {result}")
        return result
    except Exception as e:
        print(f"[WEATHER] Error: {str(e)}")
        # Return cached data even if stale
        if weather_cache["data"]:
            return weather_cache["data"]
        return {"temperature": "N/A", "windspeed": "N/A"}


def fetch_air_quality():
    global air_cache
    current_time = time.time()
    
    # Return cached data if still fresh
    if air_cache["data"] and (current_time - air_cache["time"]) < CACHE_DURATION:
        print(f"[AIR QUALITY] Using cached data")
        return air_cache["data"]
    
    try:
        url = (
            "https://air-quality-api.open-meteo.com/v1/air-quality"
            f"?latitude={LAT}&longitude={LON}&hourly=us_aqi"
        )
        response = requests.get(url, timeout=10)
        data = response.json()
        
        aqi_list = data.get("hourly", {}).get("us_aqi", [])
        
        if not aqi_list:
            return {"aqi": "N/A", "category": "Could not load AQI"}

        aqi = aqi_list[0]

        # AQI categories
        if aqi <= 50:
            category = "Good: The air quality is satisfactory."
        elif aqi <= 100:
            category = "Moderate: A small risk for sensitive individuals."
        elif aqi <= 150:
            category = "Unhealthy for Sensitive Groups: Some may feel effects."
        elif aqi <= 200:
            category = "Unhealthy: Everyone may begin to feel health effects."
        elif aqi <= 300:
            category = "Very Unhealthy: Health risks increase significantly."
        else:
            category = "Hazardous: Emergency conditions for everyone."

        result = {"aqi": aqi, "category": category}
        air_cache["data"] = result
        air_cache["time"] = current_time
        print(f"[AIR QUALITY] Success: {result}")
        return result
    except Exception as e:
        print(f"[AIR QUALITY] Error: {str(e)}")
        # Return cached data even if stale
        if air_cache["data"]:
            return air_cache["data"]
        return {"aqi": "N/A", "category": "Could not load AQI"}


def fetch_events():
    # Static events (you can replace with a real API later)
    return [
        {"name": "Milpitas Farmers Market", "time": "Saturday 9 AM"},
        {"name": "Library Teen Coding Club", "time": "Friday 4 PM"},
        {"name": "Community Cleanup", "time": "Sunday 10 AM"},
        {"name": "Cardoza Park Pickup Basketball", "time": "All week 4 PM"},
        {"name": "Cardoza Park Soccer & Volleyball", "time": "Sat & Sun 9 AM–12 PM"},
        {"name": "Milpitas Sports Center Outdoor Track", "time": "Open daily"},
        {"name": "Gill Park Skate Sessions", "time": "Open daily"},
    ]


def fetch_joke():
    url = "https://official-joke-api.appspot.com/random_joke"
    data = requests.get(url).json()
    return {"setup": data["setup"], "punchline": data["punchline"]}


# -----------------------------
# ROUTES FOR DASHBOARD CARDS
# -----------------------------

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/weather")
def weather():
    return jsonify(fetch_weather())


@app.route("/air")
def air():
    return jsonify(fetch_air_quality())


@app.route("/events")
def events():
    return jsonify(fetch_events())


@app.route("/joke")
def joke():
    return jsonify(fetch_joke())



# -----------------------------
# AI PERSONAL ASSISTANT
# -----------------------------

@app.route("/assistant", methods=["POST"])
def assistant():
    try:
        body = request.get_json()
        question = body.get("question", "")

        if not question:
            return jsonify({"error": "Question is required"}), 400

        # Pull live data
        weather = fetch_weather()
        air = fetch_air_quality()
        events = fetch_events()

        # Build context for assistant
        context = f"""
You are LocalLens, a friendly local assistant for a teen in Milpitas, CA.
Use the data below to give practical, clear, encouraging answers.

Weather:
- Temperature: {weather['temperature']} °F
- Wind: {weather['windspeed']} mph

Air Quality:
- AQI: {air['aqi']}
- Category: {air['category']}

Local Events:
{chr(10).join(f"- {e['name']} — {e['time']}" for e in events)}

User question:
{question}
"""

        # Call Ollama locally
        response = requests.post(
            "http://localhost:11434/api/chat",
            json={
                "model": "mistral",
                "messages": [
                    {
                        "role": "system",
                        "content": "You are LocalLens, a helpful, positive local assistant. Give short, clear answers.",
                    },
                    {"role": "user", "content": context},
                ],
                "stream": False,
            },
            timeout=120,
        )

        if response.status_code != 200:
            return jsonify({"error": "Ollama service not running. Make sure Ollama is started."}), 503

        data = response.json()
        answer = data.get("message", {}).get("content", "No response")
        return jsonify({"answer": answer})

    except requests.exceptions.ConnectionError:
        return jsonify({"error": "Ollama not running. Please start Ollama first."}), 503
    except Exception as e:
        error_msg = str(e)
        print(f"[ERROR] {error_msg}")
        return jsonify({"error": f"Error: {error_msg}"}), 500


# -----------------------------
# MAIN
# -----------------------------

if __name__ == "__main__":
    fetch_weather()
    fetch_air_quality()
    app.run(debug=True)
