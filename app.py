import streamlit as st
import requests

# Function to get latitude & longitude from an address (using OpenStreetMap)
def get_coordinates(address):
    url = f"https://nominatim.openstreetmap.org/search?format=json&q={address}"
    response = requests.get(url)
    if response.status_code == 200 and response.json():
        location = response.json()[0]
        return float(location["lat"]), float(location["lon"])
    return None, None

# App title
st.title("TaxiFareModel Front")

st.markdown('''
Enter the details of your taxi ride below to get a fare prediction.
''')

# Date selection with calendar
date = st.date_input("Select date")

# Time selection with dropdown
col1, col2 = st.columns(2)
with col1:
    hour = st.selectbox("Hour", list(range(0, 24)), format_func=lambda x: f"{x:02d}")
with col2:
    minute = st.selectbox("Minute", list(range(0, 60, 5)), format_func=lambda x: f"{x:02d}")

# Format datetime properly for API request
date_time = f"{date} {hour:02d}:{minute:02d}:00"

# Pickup & Dropoff inputs
st.subheader("Enter pickup & dropoff locations")
col1, col2 = st.columns(2)

# Pickup inputs
with col1:
    pickup_address = st.text_input("Pickup Address")
    pickup_lon_input = st.text_input("Pickup Longitude", value="")
    pickup_lat_input = st.text_input("Pickup Latitude", value="")

    # Automatically fetch coordinates if address is entered
    if pickup_address and not pickup_lon_input and not pickup_lat_input:
        pickup_lat, pickup_lon = get_coordinates(pickup_address)
    else:
        pickup_lat = float(pickup_lat_input) if pickup_lat_input else None
        pickup_lon = float(pickup_lon_input) if pickup_lon_input else None

# Dropoff inputs
with col2:
    dropoff_address = st.text_input("Dropoff Address")
    dropoff_lon_input = st.text_input("Dropoff Longitude", value="")
    dropoff_lat_input = st.text_input("Dropoff Latitude", value="")

    # Automatically fetch coordinates if address is entered
    if dropoff_address and not dropoff_lon_input and not dropoff_lat_input:
        dropoff_lat, dropoff_lon = get_coordinates(dropoff_address)
    else:
        dropoff_lat = float(dropoff_lat_input) if dropoff_lat_input else None
        dropoff_lon = float(dropoff_lon_input) if dropoff_lon_input else None

passenger_count = st.number_input("Passenger count", min_value=1, value=1)

# API URL
url = "https://taxifare.lewagon.ai/predict"

# Prepare request
if st.button("Predict Fare"):
    if (pickup_lat and pickup_lon) and (dropoff_lat and dropoff_lon):
        params = {
            "pickup_datetime": date_time,
            "pickup_longitude": pickup_lon,
            "pickup_latitude": pickup_lat,
            "dropoff_longitude": dropoff_lon,
            "dropoff_latitude": dropoff_lat,
            "passenger_count": passenger_count,
        }

        # API call
        response = requests.get(url, params=params)

        if response.status_code == 200:
            prediction = response.json()["fare"]
            st.success(f"Predicted fare: ${prediction:.2f}")
        else:
            st.error("Error retrieving prediction. Please check your inputs.")
    else:
        st.error("Please provide a valid pickup and dropoff location.")
