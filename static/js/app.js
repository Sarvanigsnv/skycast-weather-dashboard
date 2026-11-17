const $ = (id) => document.getElementById(id);
const state = { weather: null, unit: "C", lastCity: "Hyderabad" };

const weatherDescriptions = {
  0:["Clear sky","☀️"],1:["Mainly clear","🌤️"],2:["Partly cloudy","⛅"],3:["Overcast","☁️"],
  45:["Foggy","🌫️"],48:["Rime fog","🌫️"],51:["Light drizzle","🌦️"],53:["Drizzle","🌦️"],55:["Heavy drizzle","🌧️"],
  56:["Freezing drizzle","🌧️"],57:["Freezing drizzle","🌧️"],61:["Light rain","🌦️"],63:["Rain","🌧️"],65:["Heavy rain","🌧️"],
  66:["Freezing rain","🌧️"],67:["Freezing rain","🌧️"],71:["Light snow","🌨️"],73:["Snow","🌨️"],75:["Heavy snow","❄️"],
  77:["Snow grains","🌨️"],80:["Rain showers","🌦️"],81:["Rain showers","🌧️"],82:["Heavy showers","⛈️"],
  85:["Snow showers","🌨️"],86:["Heavy snow showers","❄️"],95:["Thunderstorm","⛈️"],96:["Thunderstorm with hail","⛈️"],99:["Thunderstorm with hail","⛈️"]
};
function describe(code){ return weatherDescriptions[code] || ["Conditions unavailable","🌡️"]; }
function convertTemp(value){ return state.unit === "F" ? value * 9/5 + 32 : value; }
function roundedTemp(value){ return `${Math.round(convertTemp(value))}°`; }
function setStatus(message){ $("statusText").textContent = message; }
function showError(message){ $("errorBox").textContent = message; $("errorBox").hidden = false; $("weatherContent").hidden = true; $("emptyState").hidden = true; }
function hideError(){ $("errorBox").hidden = true; }
function formatHour(iso){ const d = new Date(iso); return d.toLocaleTimeString([], {hour:"numeric"}); }
function formatDay(iso,index){ if(index===0)return "Today"; if(index===1)return "Tomorrow"; return new Date(iso+"T12:00:00").toLocaleDateString([], {weekday:"short"}); }
function windDirection(degrees){
  if(degrees == null) return "Near surface";
  return ["N","NE","E","SE","S","SW","W","NW"][Math.round(degrees/45)%8] + " direction";
}
function render(){
  const w = state.weather, c = w.current, daily = w.daily, hourly = w.hourly;
  const [description,icon] = describe(c.weather_code);
  $("placeName").textContent = w.location.name;
  $("placeMeta").textContent = [w.location.country,w.location.timezone].filter(Boolean).join(" · ");
  $("currentIcon").textContent = icon;
  $("temperature").textContent = Math.round(convertTemp(c.temperature_2m));
  $("unitLabel").textContent = state.unit;
  $("condition").textContent = description;
  $("feelsLike").textContent = `Feels like ${roundedTemp(c.apparent_temperature)}`;
  $("humidity").textContent = `${c.relative_humidity_2m ?? "--"}%`;
  $("wind").textContent = `${c.wind_speed_10m ?? "--"} km/h`;
  $("windDirection").textContent = windDirection(c.wind_direction_10m);
  $("pressure").textContent = c.surface_pressure == null ? "--" : `${Math.round(c.surface_pressure)} hPa`;
  $("visibility").textContent = c.visibility == null ? "--" : `${(c.visibility/1000).toFixed(1)} km`;
  $("todayRange").textContent = `H ${roundedTemp(daily.temperature_2m_max[0])} / L ${roundedTemp(daily.temperature_2m_min[0])}`;
  $("hourlyList").innerHTML = "";
  const now = new Date();
  let start = hourly.time.findIndex(t => new Date(t) >= now);
  if(start < 0) start = 0;
  for(let i=start; i<Math.min(start+8,hourly.time.length); i++){
    const [desc,emoji] = describe(hourly.weather_code[i]);
    const item = document.createElement("div"); item.className = "hour-item";
    item.innerHTML = `<div class="hour-time">${i===start?"Now":formatHour(hourly.time[i])}</div><div class="hour-icon" title="${desc}">${emoji}</div><div class="hour-temp">${roundedTemp(hourly.temperature_2m[i])}</div><div class="hour-rain">💧 ${hourly.precipitation_probability[i] ?? 0}%</div>`;
    $("hourlyList").appendChild(item);
  }
  $("dailyList").innerHTML = "";
  daily.time.forEach((date,i)=>{
    const [desc,emoji] = describe(daily.weather_code[i]);
    const row=document.createElement("div"); row.className="day-item";
    row.innerHTML=`<div class="day-name">${formatDay(date,i)}</div><div class="day-weather"><span class="day-icon">${emoji}</span>${desc}</div><div class="day-rain">💧 ${daily.precipitation_probability_max[i] ?? 0}% rain</div><div class="day-temps">${roundedTemp(daily.temperature_2m_max[i])}<span>${roundedTemp(daily.temperature_2m_min[i])}</span></div>`;
    $("dailyList").appendChild(row);
  });
  $("weatherContent").hidden=false; $("emptyState").hidden=true; hideError();
  $("updatedText").textContent = `Updated ${new Date().toLocaleTimeString([], {hour:"numeric",minute:"2-digit"})}`;
}
async function loadWeather(query){
  const params = new URLSearchParams(query);
  $("searchBtn").disabled=true; document.body.classList.add("loading");
  setStatus("Fetching the latest conditions…"); hideError();
  try{
    const response=await fetch(`/api/weather?${params.toString()}`);
    const data=await response.json();
    if(!response.ok) throw new Error(data.error || "Unable to load weather.");
    state.weather=data; state.lastCity=data.location.name; render();
    setStatus("Showing the latest available forecast");
    try{ localStorage.setItem("skycast-last-city",state.lastCity); }catch(e){}
  }catch(error){
    showError(error.message || "Something went wrong. Please try again.");
    setStatus("Weather couldn't be loaded");
  }finally{
    $("searchBtn").disabled=false; document.body.classList.remove("loading");
  }
}
function searchCity(){
  const city=$("cityInput").value.trim();
  if(!city){showToast("Enter a city name first.");$("cityInput").focus();return;}
  loadWeather({city});
}
function showToast(message){
  $("toast").textContent=message;$("toast").classList.add("show");
  clearTimeout(showToast.timer);showToast.timer=setTimeout(()=>$("toast").classList.remove("show"),2400);
}
$("searchBtn").addEventListener("click",searchCity);
$("cityInput").addEventListener("keydown",e=>{if(e.key==="Enter")searchCity();});
$("cityInput").addEventListener("input",()=>{$("clearSearch").style.display=$("cityInput").value?"block":"none";});
$("clearSearch").addEventListener("click",()=>{$("cityInput").value="";$("clearSearch").style.display="none";$("cityInput").focus();});
$("locationBtn").addEventListener("click",()=>{
  if(!navigator.geolocation){showToast("Geolocation isn't supported by this browser.");return;}
  setStatus("Finding your location…");
  navigator.geolocation.getCurrentPosition(
    pos=>loadWeather({lat:pos.coords.latitude,lon:pos.coords.longitude}),
    ()=>{setStatus("Location unavailable");showToast("Allow location access, or search for a city.");},
    {enableHighAccuracy:false,timeout:10000}
  );
});
$("unitToggle").addEventListener("click",()=>{
  state.unit=state.unit==="C"?"F":"C";
  $("unitToggle").innerHTML=state.unit==="C"?"°C <span class='toggle-slash'>/</span> °F":"°F <span class='toggle-slash'>/</span> °C";
  if(state.weather)render();
});
document.querySelectorAll("[data-city]").forEach(button=>button.addEventListener("click",()=>{
  $("cityInput").value=button.dataset.city;loadWeather({city:button.dataset.city});
}));
(async()=>{
  let last="Hyderabad";
  try{last=localStorage.getItem("skycast-last-city")||last;}catch(e){}
  $("cityInput").value=last;
  await loadWeather({city:last});
})();
