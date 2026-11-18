# SkyCast – Weather Dashboard

A responsive weather dashboard built using **Python Flask, HTML, CSS, and JavaScript**. Users can search for a city or detect their current location to view weather conditions and forecasts.

**Live Demo:** [SkyCast Weather Dashboard](https://skycast-weather-dashboard-emi7.onrender.com/)

**GitHub:** [skycast-weather-dashboard](https://github.com/Sarvanigsnv/skycast-weather-dashboard)

## Features

- Search for weather information by city name.
- Detect current location using browser geolocation.
- View current weather conditions, including temperature, humidity, wind speed, and pressure.
- View hourly forecasts and a 5-day weather forecast.
- Switch between Celsius and Fahrenheit.
- Access previously searched cities.
- Responsive interface for desktop and mobile devices.
- Loading indicators and error handling for API requests.

## Technologies Used

- **Backend:** Python, Flask
- **Frontend:** HTML5, CSS3, JavaScript
- **API:** OpenWeather API
- **HTTP Requests:** Python Requests
- **Deployment:** Render

## Run Locally

**1. Clone the repository**

```bash
git clone https://github.com/Sarvanigsnv/skycast-weather-dashboard.git
cd skycast-weather-dashboard
```

**2. Create and activate a virtual environment**

```bash
python -m venv venv
```

Windows PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
```

**3. Install dependencies**

```bash
python -m pip install -r requirements.txt
```

**4. Configure your API key**

Get an API key from [OpenWeather](https://openweathermap.org/api).

Set the environment variable in PowerShell:

```powershell
$env:OPENWEATHER_API_KEY="your_api_key"
```

**5. Start the application**

```bash
python app.py
```

Open http://127.0.0.1:5000/ in your browser.

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Loads the weather dashboard |
| GET | `/api/weather?city=Hyderabad` | Retrieves weather information for a city |
| GET | `/api/weather?lat=17.385&lon=78.4867` | Retrieves weather information using geographic coordinates |
| GET | `/health` | Checks the backend health status |

## Author

**Sarvani Gangaraju**

[GitHub](https://github.com/Sarvanigsnv)
