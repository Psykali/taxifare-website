import streamlit as st
import requests

# App title
st.title("TaxiFareModel Front")

st.markdown('''
Enter the details of your taxi ride below to get a fare prediction.
''')

# User input fields
date_time = st.text_input("Enter date and time (YYYY-MM-DD HH:MM:SS)")
pickup_longitude = st.number_input("Pickup longitude", value=0.0)
pickup_latitude = st.number_input("Pickup latitude", value=0.0)
dropoff_longitude = st.number_input("Dropoff longitude", value=0.0)
dropoff_latitude = st.number_input("Dropoff latitude", value=0.0)
passenger_count = st.number_input("Passenger count", min_value=1, value=1)

# API URL
url = "https://taxifare.lewagon.ai/predict"

# Prepare request
if st.button("Predict Fare"):
    params = {
        "pickup_datetime": date_time,
        "pickup_longitude": pickup_longitude,
        "pickup_latitude": pickup_latitude,
        "dropoff_longitude": dropoff_longitude,
        "dropoff_latitude": dropoff_latitude,
        "passenger_count": passenger_count,
    }

    # API call
    response = requests.get(url, params=params)

    if response.status_code == 200:
        prediction = response.json()["fare"]
        st.success(f"Predicted fare: ${prediction:.2f}")
    else:
        st.error("Error retrieving prediction. Please check your inputs.")
