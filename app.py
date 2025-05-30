import os
import streamlit as st
import requests
import folium
from streamlit_folium import folium_static
from datetime import datetime, date
from pytz import country_names  # For country list

# Configuration
API_URL = "https://taxifare.lewagon.ai/predict"
USD_TO_EUR = 0.92  # Exchange rate
BASE_FARE = 3.50  # Base fare in EUR
FARE_PER_KM = 1.50  # Per km rate in EUR

# Country list for selection
COUNTRIES = sorted(list(country_names.values()))

# Simplified holiday check (since we removed 'holidays' package)
def is_holiday(date_obj, country):
    """Simple holiday check - can be expanded with specific dates"""
    # Add specific holiday dates for different countries here
    if country == "France":
        # Example: Bastille Day (July 14)
        if date_obj.month == 7 and date_obj.day == 14:
            return True
    elif country == "United States":
        # Example: July 4th
        if date_obj.month == 7 and date_obj.day == 4:
            return True
    return False

def get_car_type(passengers):
    """Returns appropriate vehicle type based on passenger count"""
    if passengers <= 4:
        return "City Car (Max: 4)", "photos/berline.png"
    elif passengers <= 6:
        return "SUV/Break (Max: 6)", "photos/suv.png"
    else:
        return "Mini Bus (Max: 12)", "photos/minibus.png"

def get_coordinates(street, location, country):
    """Geocoding using OpenStreetMap Nominatim API"""
    address = f"{street}, {location}, {country}"
    url = f"https://nominatim.openstreetmap.org/search?format=json&q={address}"
    headers = {"User-Agent": "TaxiFareApp"}

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200 and response.json():
            location = response.json()[0]
            return float(location["lat"]), float(location["lon"])
    except Exception as e:
        st.error(f"Geocoding error: {str(e)}")
    return None, None

def get_route_geometry(from_lat, from_lon, to_lat, to_lon):
    """Get full route geometry from OSRM"""
    url = f"https://router.project-osrm.org/route/v1/driving/{from_lon},{from_lat};{to_lon},{to_lat}?overview=full&geometries=geojson"

    try:
        response = requests.get(url)
        if response.status_code == 200 and response.json().get("routes"):
            route = response.json()["routes"][0]
            distance_km = round(route["distance"] / 1000, 2)
            duration_min = round(route["duration"] / 60, 2)
            geometry = route["geometry"]
            return distance_km, duration_min, geometry
    except Exception as e:
        st.error(f"Routing error: {str(e)}")
    return None, None, None

def get_time_multiplier(trip_datetime, country):
    """Calculate time-based fare multiplier"""
    hour = trip_datetime.hour
    weekday = trip_datetime.weekday()  # Monday=0, Sunday=6

    # Night hours (10pm to 6am)
    is_night = hour >= 22 or hour < 6

    # Weekend (Saturday or Sunday)
    is_weekend = weekday >= 5

    # Holiday check (using our simplified function)
    is_holiday_date = is_holiday(trip_datetime.date(), country)

    # Apply multipliers
    multiplier = 1.0
    if is_night:
        multiplier *= 1.3  # 30% night surcharge
    if is_weekend:
        multiplier *= 1.2  # 20% weekend surcharge
    if is_holiday_date:
        multiplier *= 1.5  # 50% holiday surcharge

    return multiplier

def calculate_fare(distance_km, passenger_count, currency, trip_datetime, country):
    """Calculate fare with passenger-based and time-based pricing"""
    # Base fare + distance fare
    fare_eur = BASE_FARE + (distance_km * FARE_PER_KM)

    # Passenger multiplier (non-linear increase)
    if passenger_count <= 4:
        passenger_mult = 1.0 + (passenger_count - 1) * 0.05  # 5% per additional passenger
    elif passenger_count <= 6:
        passenger_mult = 1.15 + (passenger_count - 4) * 0.10  # 10% for larger vehicles
    else:
        passenger_mult = 1.35 + (passenger_count - 6) * 0.15  # 15% for minibus

    # Time-based multiplier
    time_mult = get_time_multiplier(trip_datetime, country)

    # Apply all multipliers
    fare_eur *= passenger_mult * time_mult

    # Convert currency if needed
    if currency == "USD ($)":
        return round(fare_eur / USD_TO_EUR, 2)
    return round(fare_eur, 2)

# Streamlit App Layout
st.title("🚖 DS1992_TaxiFare_Calculator")

# Main columns layout
col_left, col_right = st.columns([2, 1])

with col_left:
    # Date & Time selection
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        trip_date = st.date_input("Date", value=datetime.now())
    with col2:
        hour = st.selectbox("Hour", options=range(24), format_func=lambda x: f"{x:02d}")
    with col3:
        minute = st.selectbox("Minute", options=range(0, 60, 5), format_func=lambda x: f"{x:02d}")

    trip_datetime = datetime.combine(trip_date, datetime.min.time()).replace(hour=hour, minute=minute)
    pickup_datetime = trip_datetime.strftime("%Y-%m-%d %H:%M:%S")

    # Location inputs
    st.subheader("Trip Details")

    # Pickup Location
    st.markdown("### Pickup Location")
    col1, col2, col3 = st.columns([2, 1, 1])
    pickup_street = col1.text_input("Street", key="pickup_street")
    pickup_location = col2.text_input("City or ZIP", key="pickup_location")
    pickup_country = col3.selectbox("Country", COUNTRIES, index=COUNTRIES.index("France") if "France" in COUNTRIES else 0, key="pickup_country")

    if pickup_street and pickup_location and pickup_country:
        pickup_lat, pickup_lon = get_coordinates(pickup_street, pickup_location, pickup_country)
    else:
        pickup_lat, pickup_lon = None, None

    # Dropoff Location
    st.markdown("### Dropoff Location")
    col1, col2, col3 = st.columns([2, 1, 1])
    dropoff_street = col1.text_input("Street", key="dropoff_street")
    dropoff_location = col2.text_input("City or ZIP", key="dropoff_location")
    dropoff_country = col3.selectbox("Country", COUNTRIES, index=COUNTRIES.index("France") if "France" in COUNTRIES else 0, key="dropoff_country")

    if dropoff_street and dropoff_location and dropoff_country:
        dropoff_lat, dropoff_lon = get_coordinates(dropoff_street, dropoff_location, dropoff_country)
    else:
        dropoff_lat, dropoff_lon = None, None

    # Display coordinates when available
    if pickup_lat and pickup_lon:
        st.info(f"Pickup Coordinates: Latitude: {pickup_lat:.6f}, Longitude: {pickup_lon:.6f}")
    if dropoff_lat and dropoff_lon:
        st.info(f"Dropoff Coordinates: Latitude: {dropoff_lat:.6f}, Longitude: {dropoff_lon:.6f}")

with col_right:
    # Vehicle and fare options
    st.subheader("Fare Options")

    col1, col2 = st.columns(2)
    with col1:
        passenger_count = st.number_input("Passengers", min_value=1, max_value=12, value=1)
    with col2:
        currency = st.radio("Currency", ["EUR (€)", "USD ($)"], index=0)

    # Display vehicle type and image
    car_type, car_image_path = get_car_type(passenger_count)
    st.markdown(f"**Vehicle Type:** {car_type}")
    if os.path.exists(car_image_path):
        st.image(car_image_path, width=150)
    else:
        st.warning("Vehicle image not available")

# Calculate button and results
if st.button("Calculate Fare"):
    if None in [pickup_lat, pickup_lon, dropoff_lat, dropoff_lon]:
        st.error("Please enter valid pickup and dropoff locations")
    else:
        # Calculate distance, time, and get route geometry
        distance_km, duration_min, geometry = get_route_geometry(pickup_lat, pickup_lon, dropoff_lat, dropoff_lon)

        if distance_km and duration_min and geometry:
            # Calculate fare with all pricing factors
            fare = calculate_fare(distance_km, passenger_count, currency, trip_datetime, pickup_country)

            # Get time-based pricing details
            time_mult = get_time_multiplier(trip_datetime, pickup_country)
            hour = trip_datetime.hour
            is_night = hour >= 22 or hour < 6
            is_weekend = trip_datetime.weekday() >= 5
            is_holiday_date = is_holiday(trip_datetime.date(), pickup_country)

            # Display results
            st.subheader("Trip Summary")
            col1, col2, col3 = st.columns(3)
            col1.metric("Distance", f"{distance_km:.2f} km")
            col2.metric("Duration", f"{duration_min:.2f} min")
            col3.metric("Estimated Fare", f"{fare:.2f} {currency.split()[0]}")

            # Display pricing details
            st.markdown("**Pricing Details**")
            pricing_info = []
            if passenger_count > 1:
                pricing_info.append(f"Passengers: {passenger_count} (surcharge applied)")
            if is_night:
                pricing_info.append("Night time (30% surcharge)")
            if is_weekend:
                pricing_info.append("Weekend (20% surcharge)")
            if is_holiday_date:
                pricing_info.append("Holiday (50% surcharge)")

            if pricing_info:
                st.info(" | ".join(pricing_info))
            else:
                st.info("Standard rate (no surcharges)")

            # Show map with actual route
            st.subheader("Route Map")
            m = folium.Map(location=[(pickup_lat + dropoff_lat)/2, (pickup_lon + dropoff_lon)/2], zoom_start=12)

            # Add actual route geometry
            if geometry:
                folium.GeoJson(
                    geometry,
                    name="Route",
                    style_function=lambda x: {"color": "blue", "weight": 3}
                ).add_to(m)

            folium.Marker([pickup_lat, pickup_lon], tooltip="Pickup", icon=folium.Icon(color="green")).add_to(m)
            folium.Marker([dropoff_lat, dropoff_lon], tooltip="Dropoff", icon=folium.Icon(color="red")).add_to(m)
            folium_static(m)
        else:
            st.error("Could not calculate route information")
