# SkyCast – Smart Weather Dashboard

SkyCast is a responsive weather dashboard developed using **Python Flask, HTML, CSS, and JavaScript**. It allows users to search for weather information by city or use their current location to view weather conditions and forecasts.

The application uses the **Open-Meteo API** for weather forecasting, city geocoding, and reverse geocoding.

## Features

- **City Search:** Search for weather information by entering a city name.
- **Current Weather:** View temperature, feels-like temperature, humidity, wind speed, wind direction, pressure, visibility, and precipitation.
- **Hourly Forecast:** View the upcoming 8-hour weather forecast.
- **7-Day Forecast:** Check daily weather predictions, including maximum and minimum temperatures.
- **Location Detection:** Use browser geolocation to retrieve weather information for your current location.
- **Temperature Conversion:** Switch between Celsius and Fahrenheit.
- **Responsive Design:** Access the dashboard on desktop, tablet, and mobile devices.
- **Last Searched City:** Remembers the previously searched city using browser local storage.
- **Loading and Error States:** Provides feedback while retrieving weather data and when errors occur.
- **API Error Handling:** Handles request timeouts, unsuccessful HTTP responses, invalid locations, and unexpected API responses.
- **Input Validation:** Validates geographic coordinates before requesting weather information.

## Technologies Used

| Technology | Purpose |
|---|---|
| Python | Backend programming |
| Flask | Web framework and API development |
| HTML5 | Page structure |
| CSS3 | Styling and responsive design |
| JavaScript | Frontend functionality and API integration |
| Requests | Making HTTP requests to external APIs |
| Open-Meteo API | Weather forecasting and geocoding |

## Project Structure

```text
skycast_weather_dashboard/
│
├── app.py
├── requirements.txt
├── README.md
│
├── templates/
│   └── index.html
│
└── static/
    ├── css/
    │   └── style.css
    │
    └── js/
        └── app.js
```

## Getting Started

Follow these steps to run the project locally.

### 1. Clone the Repository

```bash
git clone https://github.com/Sarvanigsnv/skycast-weather-dashboard.git
```

### 2. Navigate to the Project Directory

```bash
cd skycast-weather-dashboard
```

### 3. Create a Virtual Environment

```bash
python -m venv venv
```

### 4. Activate the Virtual Environment

**Windows – PowerShell:**

```powershell
.\venv\Scripts\Activate.ps1
```

**Windows – Git Bash:**

```bash
source venv/Scripts/activate
```

### 5. Install Dependencies

```bash
python -m pip install -r requirements.txt
```

### 6. Run the Application

```bash
python app.py
```

Open your browser and visit:

```text
http://127.0.0.1:5000/
```

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Loads the weather dashboard |
| GET | `/api/weather?city=Hyderabad` | Retrieves weather information for a city |
| GET | `/api/weather?lat=17.385&lon=78.4867` | Retrieves weather information using geographic coordinates |
| GET | `/health` | Checks the backend health status |

## How It Works

1. The user searches for a city or allows browser location access.
2. The Flask backend receives the request.
3. For city searches, the application uses Open-Meteo geocoding to obtain geographic coordinates.
4. For location-based searches, the application uses the coordinates provided by browser geolocation.
5. The backend retrieves weather information from the Open-Meteo forecast API.
6. The retrieved data is organized into a JSON response.
7. JavaScript consumes the response and dynamically updates the dashboard.

## Error Handling and Validation

- Uses a 12-second timeout for external API requests.
- Handles unsuccessful HTTP responses using `raise_for_status()`.
- Validates latitude and longitude ranges.
- Handles invalid city searches and missing input.
- Handles API timeouts and connection errors.
- Provides a fallback location name if reverse geocoding fails.
- Handles unexpected API response structures.

## Future Improvements

- Add automated tests for Flask routes and API responses.
- Implement caching to reduce repeated API requests.
- Improve application performance and error handling.
- Deploy the application so it can be accessed online.

## Author

**Sarvani Gangaraju**

[GitHub Repository](https://github.com/Sarvanigsnv/skycast-weather-dashboard)