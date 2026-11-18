
from flask import Flask, render_template, request, jsonify
import requests
from flask_caching import Cache

app = Flask(__name__)

# ---------------- CACHE CONFIGURATION ----------------

app.config["CACHE_TYPE"] = "SimpleCache"
app.config["CACHE_DEFAULT_TIMEOUT"] = 600

cache = Cache(app)

# ---------------- API URLS ----------------

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
REVERSE_GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/reverse"


# ---------------- API REQUEST FUNCTION ----------------

def get_json(url, params):
    """Fetch JSON data from an external API with error logging."""

    try:
        app.logger.info("Requesting external API: %s", url)

        response = requests.get(
            url,
            params=params,
            timeout=20
        )
        if response.status_code == 429:
            app.logger.error(
        "Open-Meteo rate-limit response: %s",
        response.text
    )
        response.raise_for_status()

        app.logger.info(
            "External API response: %s",
            response.status_code
        )

        return response.json()

    except requests.RequestException:
        app.logger.exception(
            "External API request failed: %s",
            url
        )
        raise


# ---------------- CITY GEOCODING ----------------

@cache.memoize(timeout=3600)
def find_location(city):
    """Find city coordinates. Cache results for one hour."""

    result = get_json(GEOCODING_URL, {
        "name": city,
        "count": 1,
        "language": "en",
        "format": "json"
    })

    places = result.get("results") or []

    if not places:
        raise ValueError(
            "We couldn't find that city. Check the spelling and try again."
        )

    return places[0]


# ---------------- WEATHER DATA ----------------

def build_weather_payload(
    latitude,
    longitude,
    place_name,
    country="",
    timezone="auto"
):
    """Fetch current, hourly and daily weather information."""

    data = get_json(FORECAST_URL, {
        "latitude": latitude,
        "longitude": longitude,
        "timezone": timezone,
        "forecast_days": 7,

        "current": (
            "temperature_2m,relative_humidity_2m,"
            "apparent_temperature,is_day,precipitation,"
            "weather_code,wind_speed_10m,"
            "wind_direction_10m,surface_pressure,visibility"
        ),

        "hourly": (
            "temperature_2m,precipitation_probability,"
            "weather_code"
        ),

        "daily": (
            "weather_code,temperature_2m_max,"
            "temperature_2m_min,sunrise,sunset,"
            "uv_index_max,precipitation_probability_max"
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


# ---------------- HOME ROUTE ----------------

@app.get("/")
def home():
    return render_template("index.html")


# ---------------- WEATHER API ROUTE ----------------

@app.get("/api/weather")
@cache.cached(
    timeout=600,
    query_string=True
)
def weather():
    """Return weather using city name or browser coordinates."""

    city = (request.args.get("city") or "").strip()

    lat = request.args.get("lat", type=float)
    lon = request.args.get("lon", type=float)

    try:

        # -------- BROWSER GEOLOCATION --------

        if lat is not None and lon is not None:

            if not (-90 <= lat <= 90 and -180 <= lon <= 180):
                return jsonify({
                    "error": "The coordinates are outside the valid range."
                }), 400

            name = "Your location"
            country = ""

            # Reverse geocoding is optional
            try:

                reverse = get_json(
                    REVERSE_GEOCODING_URL,
                    {
                        "latitude": lat,
                        "longitude": lon,
                        "language": "en",
                        "format": "json"
                    }
                )

                place = (reverse.get("results") or [{}])[0]

                name = place.get("name", "Your location")
                country = place.get("country", "")

            except requests.RequestException:

                app.logger.warning(
                    "Reverse geocoding failed. Using coordinates."
                )

            payload = build_weather_payload(
                lat,
                lon,
                name,
                country
            )

        # -------- CITY SEARCH --------

        elif city:

            place = find_location(city)

            payload = build_weather_payload(
                place["latitude"],
                place["longitude"],
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

        return jsonify({
            "error": str(exc)
        }), 404

    except requests.Timeout:

        app.logger.exception("Weather API request timed out")

        return jsonify({
            "error": "The weather service took too long to respond. Please try again."
        }), 504

    except requests.HTTPError as exc:

        status_code = (
            exc.response.status_code
            if exc.response is not None
            else None
        )

        if status_code == 429:

            return jsonify({
                "error": "Weather service is temporarily busy. Please try again later."
            }), 429

        app.logger.exception(
            "Weather API returned HTTP error"
        )

        return jsonify({
            "error": "The weather service returned an error."
        }), 502

    except requests.RequestException:

        app.logger.exception(
            "Weather endpoint failed while fetching external data"
        )

        return jsonify({
            "error": "Couldn't reach the weather service. Please try again later."
        }), 502

    except (KeyError, TypeError):

        app.logger.exception(
            "Unexpected weather API response"
        )

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
