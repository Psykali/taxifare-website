import streamlit as st
import requests
import datetime

# App title
st.title("TaxiFareModel Front")

st.markdown('''
Enter the details of your taxi ride below to get a fare prediction.
''')

# Date selection with calendar
date = st.date_input("Select date", value=datetime.date.today())

# Create two columns for hour and minute selection
col1, col2 = st.columns(2)
with col1:
    hour = st.selectbox("Hour", list(range(24)))
with col2:
    minute = st.selectbox("Minute", list(range(0, 60, 5)))  # Step of 5 minutes for convenience

# Combine date and time into a proper format
date_time = f"{date} {hour:02d}:{minute:02d}:00"

# User input fields
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
