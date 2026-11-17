from flask import Flask, render_template, request, jsonify
import requests

app = Flask(__name__)

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"



def get_json(url, params):
    """Request JSON from an external API and log useful errors."""
    try:
        app.logger.info("Requesting external API: %s", url)

        response = requests.get(url, params=params, timeout=20)
        response.raise_for_status()

        app.logger.info("External API response: %s", response.status_code)
        return response.json()

    except requests.RequestException:
        app.logger.exception("External API request failed: %s", url)
        raise


def find_location(city):
    result = get_json(GEOCODING_URL, {
        "name": city,
        "count": 1,
        "language": "en",
        "format": "json"
    })
    places = result.get("results") or []
    if not places:
        raise ValueError("We couldn't find that city. Check the spelling and try again.")
    return places[0]


def build_weather_payload(latitude, longitude, place_name, country="", timezone="auto"):
    data = get_json(FORECAST_URL, {
        "latitude": latitude,
        "longitude": longitude,
        "timezone": timezone,
        "forecast_days": 7,
        "current": (
            "temperature_2m,relative_humidity_2m,apparent_temperature,"
            "is_day,precipitation,weather_code,wind_speed_10m,"
            "wind_direction_10m,surface_pressure,visibility"
        ),
        "hourly": "temperature_2m,precipitation_probability,weather_code",
        "daily": (
            "weather_code,temperature_2m_max,temperature_2m_min,"
            "sunrise,sunset,uv_index_max,precipitation_probability_max"
        )
    })

    return {
        "location": {
            "name": place_name,
            "country": country,
            "latitude": latitude,
            "longitude": longitude,
            "timezone": data.get("timezone", "Local time")
        },
        "current": data.get("current", {}),
        "current_units": data.get("current_units", {}),
        "hourly": data.get("hourly", {}),
        "daily": data.get("daily", {}),
        "daily_units": data.get("daily_units", {})
    }


@app.get("/")
def home():
    return render_template("index.html")


@app.get("/api/weather")
def weather():
    """Return weather for a city, or coordinates supplied by browser geolocation."""
    city = (request.args.get("city") or "").strip()
    lat = request.args.get("lat", type=float)
    lon = request.args.get("lon", type=float)

    try:
        if lat is not None and lon is not None:
            if not (-90 <= lat <= 90 and -180 <= lon <= 180):
                return jsonify({"error": "The coordinates are outside the valid range."}), 400
            # Reverse-geocoding is optional; keep the experience working if it fails.
            try:
                reverse = get_json("https://geocoding-api.open-meteo.com/v1/reverse", {
                    "latitude": lat, "longitude": lon, "language": "en", "format": "json"
                })
                place = (reverse.get("results") or [{}])[0]
                name = place.get("name", "Your location")
                country = place.get("country", "")
            except requests.RequestException:
                name, country = "Your location", ""
            payload = build_weather_payload(lat, lon, name, country)
        elif city:
            place = find_location(city)
            payload = build_weather_payload(
                place["latitude"], place["longitude"],
                place["name"], place.get("country", "")
            )
        else:
            return jsonify({"error": "Enter a city or allow location access."}), 400

        return jsonify(payload)

    except ValueError as exc:
        return jsonify({"error": str(exc)}), 404
    except requests.Timeout:
        return jsonify({"error": "The weather service took too long to respond. Please try again."}), 504
    except requests.RequestException:
        app.logger.exception("Weather endpoint failed while fetching external data")
        return jsonify({"error": "Couldn't reach the weather service. Check your internet connection."}), 502
    except (KeyError, TypeError):
        app.logger.exception("Unexpected weather API response")
        return jsonify({"error": "The weather service returned an unexpected response."}), 502


@app.get("/health")
def health():
    return jsonify({"status": "ok", "message": "SkyCast backend is running"})


if __name__ == "__main__":
    app.run(debug=True)
