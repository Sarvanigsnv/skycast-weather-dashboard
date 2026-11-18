
import os
import logging
from datetime import datetime, timezone, timedelta

import requests
from flask import Flask, render_template, request, jsonify
from flask_caching import Cache

app = Flask(__name__)

# ---------------- CACHE CONFIGURATION ----------------

app.config["CACHE_TYPE"] = "SimpleCache"
app.config["CACHE_DEFAULT_TIMEOUT"] = 600

cache = Cache(app)

# ---------------- OPENWEATHER CONFIGURATION ----------------

API_KEY = os.getenv("OPENWEATHER_API_KEY")

GEOCODING_URL = "https://api.openweathermap.org/geo/1.0/direct"
REVERSE_GEOCODING_URL = "https://api.openweathermap.org/geo/1.0/reverse"
CURRENT_WEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"
FORECAST_URL = "https://api.openweathermap.org/data/2.5/forecast"


# ---------------- API REQUEST FUNCTION ----------------

def get_json(url, params):
    """Request JSON from OpenWeather and handle API errors."""

    if not API_KEY:
        raise RuntimeError("OpenWeather API key is not configured.")

    params = {**params, "appid": API_KEY}

    try:
        response = requests.get(url, params=params, timeout=20)

        if response.status_code == 401:
            raise RuntimeError(
                "OpenWeather rejected the API key. Check your key and activation status."
            )

        if response.status_code == 404:
            raise ValueError("The requested location could not be found.")

        if response.status_code == 429:
            raise requests.HTTPError(
                "OpenWeather rate limit exceeded.",
                response=response
            )

        response.raise_for_status()
        return response.json()

    except requests.Timeout:
        app.logger.exception("OpenWeather request timed out.")
        raise

    except requests.RequestException:
        app.logger.exception("OpenWeather request failed.")
        raise


# ---------------- CITY GEOCODING ----------------

@cache.memoize(timeout=3600)
def find_location(city):
    """Find city coordinates using OpenWeather Geocoding API."""

    results = get_json(
        GEOCODING_URL,
        {
            "q": city,
            "limit": 1
        }
    )

    if not results:
        raise ValueError(
            "We couldn't find that city. Check the spelling and try again."
        )

    return results[0]


# ---------------- WEATHER CODE CONVERSION ----------------

def convert_weather_code(weather_id):
    """Convert OpenWeather condition IDs to WMO codes used by app.js."""

    if 200 <= weather_id <= 232:
        return 95

    if 300 <= weather_id <= 321:
        return 53

    if 500 <= weather_id <= 504:
        return 63 if weather_id < 502 else 65

    if weather_id == 511:
        return 66

    if 520 <= weather_id <= 531:
        return 81 if weather_id < 522 else 82

    if 600 <= weather_id <= 602:
        return 71 if weather_id == 600 else 73 if weather_id == 601 else 75

    if 611 <= weather_id <= 616:
        return 71

    if 620 <= weather_id <= 622:
        return 71 if weather_id == 620 else 73

    if 701 <= weather_id <= 781:
        return 45

    if weather_id == 800:
        return 0

    if weather_id == 801:
        return 1

    if weather_id == 802:
        return 2

    if weather_id in (803, 804):
        return 3

    return 3


# ---------------- WEATHER PAYLOAD ----------------

def build_weather_payload(latitude, longitude, place_name, country=""):
    """Fetch and normalize current weather and forecast data."""

    current_data = get_json(
        CURRENT_WEATHER_URL,
        {
            "lat": latitude,
            "lon": longitude,
            "units": "metric"
        }
    )

    forecast_data = get_json(
        FORECAST_URL,
        {
            "lat": latitude,
            "lon": longitude,
            "units": "metric"
        }
    )

    timezone_offset = current_data.get("timezone", 0)
    local_timezone = timezone(timedelta(seconds=timezone_offset))

    absolute_offset = abs(timezone_offset)
    offset_hours = absolute_offset // 3600
    offset_minutes = (absolute_offset % 3600) // 60
    sign = "+" if timezone_offset >= 0 else "-"

    timezone_label = (
        f"UTC{sign}{offset_hours:02d}:{offset_minutes:02d}"
    )
    # -------- CURRENT WEATHER --------

    main = current_data.get("main", {})
    wind = current_data.get("wind", {})
    weather = (current_data.get("weather") or [{}])[0]

    current = {
        "temperature_2m": main.get("temp"),
        "apparent_temperature": main.get("feels_like"),
        "relative_humidity_2m": main.get("humidity"),
        "surface_pressure": main.get("pressure"),
        "visibility": current_data.get("visibility"),
        "wind_speed_10m": (
            round(wind.get("speed", 0) * 3.6, 1)
            if wind.get("speed") is not None else None
        ),
        "wind_direction_10m": wind.get("deg"),
        "weather_code": convert_weather_code(weather.get("id", 800))
    }

    # -------- FORECAST DATA --------

    forecast_items = forecast_data.get("list", [])

    hourly = {
        "time": [],
        "temperature_2m": [],
        "precipitation_probability": [],
        "weather_code": []
    }

    daily_groups = {}

    for item in forecast_items:
        timestamp = datetime.fromtimestamp(
            item["dt"],
            tz=timezone.utc
        ).astimezone(local_timezone)

        local_time = timestamp.replace(tzinfo=None).isoformat()
        local_date = timestamp.date().isoformat()

        forecast_main = item.get("main", {})
        forecast_weather = (item.get("weather") or [{}])[0]

        temperature = forecast_main.get("temp")
        weather_code = convert_weather_code(
            forecast_weather.get("id", 800)
        )
        rain_probability = round(
            item.get("pop", 0) * 100
        )

        # The API provides forecast records every 3 hours.
        hourly["time"].append(local_time)
        hourly["temperature_2m"].append(temperature)
        hourly["precipitation_probability"].append(rain_probability)
        hourly["weather_code"].append(weather_code)

        # Group forecast records by the location's local date.
        if local_date not in daily_groups:
            daily_groups[local_date] = []

        daily_groups[local_date].append({
            "temperature": temperature,
            "minimum": forecast_main.get("temp_min", temperature),
            "maximum": forecast_main.get("temp_max", temperature),
            "weather_code": weather_code,
            "rain_probability": rain_probability,
            "hour": timestamp.hour
        })

    # -------- DAILY SUMMARY --------

    daily = {
        "time": [],
        "temperature_2m_max": [],
        "temperature_2m_min": [],
        "weather_code": [],
        "precipitation_probability_max": []
    }

    for date, records in daily_groups.items():
        daily["time"].append(date)

        temperatures = [
            r["temperature"] for r in records
            if r["temperature"] is not None
        ]

        daily["temperature_2m_max"].append(
            round(max(temperatures), 1) if temperatures else None
        )

        daily["temperature_2m_min"].append(
            round(min(temperatures), 1) if temperatures else None
        )

        # Use the forecast closest to midday for the daily condition.
        representative = min(
            records,
            key=lambda r: abs(r["hour"] - 12)
        )

        daily["weather_code"].append(
            representative["weather_code"]
        )

        daily["precipitation_probability_max"].append(
            max(r["rain_probability"] for r in records)
        )

    return {
        "location": {
            "name": place_name,
            "country": country,
            "latitude": latitude,
            "longitude": longitude,
            "timezone": timezone_label
        },
        "current": current,
        "hourly": hourly,
        "daily": daily
    }


# ---------------- HOME ROUTE ----------------

@app.get("/")
def home():
    return render_template("index.html")


# ---------------- WEATHER API ROUTE ----------------

@app.get("/api/weather")
@cache.cached(timeout=600, query_string=True)
def weather():
    """Return weather for a searched city or browser coordinates."""

    city = (request.args.get("city") or "").strip()

    lat = request.args.get("lat", type=float)
    lon = request.args.get("lon", type=float)

    try:
        if not API_KEY:
            return jsonify({
                "error": "Weather service is not configured. Please try again later."
            }), 503

        # -------- BROWSER GEOLOCATION --------

        if lat is not None and lon is not None:

            if not (-90 <= lat <= 90 and -180 <= lon <= 180):
                return jsonify({
                    "error": "The coordinates are outside the valid range."
                }), 400

            name = "Your location"
            country = ""

            try:
                places = get_json(
                    REVERSE_GEOCODING_URL,
                    {
                        "lat": lat,
                        "lon": lon,
                        "limit": 1
                    }
                )

                if places:
                    name = places[0].get("name", name)
                    country = places[0].get("country", "")

            except requests.RequestException:
                app.logger.warning(
                    "Reverse geocoding failed. Using coordinates."
                )

            payload = build_weather_payload(
                lat, lon, name, country
            )

        # -------- CITY SEARCH --------

        elif city:

            place = find_location(city)

            payload = build_weather_payload(
                place["lat"],
                place["lon"],
                place["name"],
                place.get("country", "")
            )

        else:
            return jsonify({
                "error": "Enter a city or allow location access."
            }), 400

        return jsonify(payload)

    # -------- ERROR HANDLING --------

    except ValueError as exc:
        return jsonify({"error": str(exc)}), 404

    except RuntimeError as exc:
        app.logger.error("%s", exc)
        return jsonify({
            "error": str(exc)
        }), 503

    except requests.Timeout:
        return jsonify({
            "error": "The weather service took too long to respond. Please try again."
        }), 504

    except requests.HTTPError as exc:
        status_code = (
            exc.response.status_code
            if exc.response is not None else None
        )

        if status_code == 429:
            return jsonify({
                "error": "Weather service is temporarily busy. Please try again later."
            }), 429

        app.logger.exception("OpenWeather returned an HTTP error.")

        return jsonify({
            "error": "The weather service returned an error."
        }), 502

    except requests.RequestException:
        return jsonify({
            "error": "Couldn't reach the weather service. Please try again later."
        }), 502

    except (KeyError, TypeError, IndexError):
        app.logger.exception("Unexpected OpenWeather response.")

        return jsonify({
            "error": "The weather service returned an unexpected response."
        }), 502


# ---------------- HEALTH CHECK ----------------

@app.get("/health")
def health():
    return jsonify({
        "status": "ok",
        "message": "SkyCast backend is running"
    })


# ---------------- LOCAL DEVELOPMENT ----------------

if __name__ == "__main__":
    app.run(debug=True)
