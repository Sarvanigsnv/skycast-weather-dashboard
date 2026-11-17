# SkyCast — Smart Weather Dashboard

A responsive weather dashboard built with Python, Flask, HTML, CSS and vanilla JavaScript. Weather data and geocoding are provided by Open-Meteo; no API key is required.

## Features
- City search with geocoding
- Browser geolocation (requires permission; localhost is allowed)
- Current conditions, feels-like temperature, humidity, wind, pressure and visibility
- Next 8 hourly forecast entries
- 7-day forecast
- Celsius/Fahrenheit display toggle
- Responsive dark glassmorphism UI, subtle motion and loading/error states
- Remembers the last searched city in browser local storage
- Flask backend with request timeouts and API error handling

## Setup on Windows (VS Code)

Open the project folder in VS Code. In the terminal:

```powershell
py -m venv venv
.\venv\Scripts\python.exe -m pip install -r requirements.txt
.\venv\Scripts\python.exe app.py
```

If PowerShell blocks `Activate.ps1`, you do not need to activate the environment. Calling `venv\Scripts\python.exe` directly (as above) works.

Open http://127.0.0.1:5000

## Project structure

```text
skycast_weather_dashboard/
├── app.py
├── requirements.txt
├── README.md
├── templates/
│   └── index.html
└── static/
    ├── css/style.css
    └── js/app.js
```

## API endpoints
- `GET /` — dashboard page
- `GET /api/weather?city=Hyderabad` — weather by city name
- `GET /api/weather?lat=17.385&lon=78.4867` — weather by coordinates
- `GET /health` — backend health check

## Interview explanation
"SkyCast is a full-stack weather dashboard. Flask serves the frontend and exposes a JSON endpoint. The backend resolves city names to coordinates using Open-Meteo geocoding, requests current/hourly/daily forecast data, and returns a normalized JSON response. The JavaScript frontend consumes that endpoint asynchronously and renders the dashboard. I added timeouts, HTTP error handling, input validation, geolocation, responsive styling and a temperature-unit toggle."

## Good next improvements
- Add automated tests for `/health` and `/api/weather` using Flask's test client and mocked API calls.
- Add caching to reduce repeated upstream requests.
- Add an LLM assistant that answers questions using the weather payload as context. Keep API keys on the server in environment variables; never put secrets in browser JavaScript.
