import pandas as pd
import pydeck as pdk
import streamlit as st
import math
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")

data = pd.read_excel("Harmonized Street Cluster.xlsx", sheet_name="Sheet1")

# Filter out the data that has From Longitude and From latitude
filtered_data = data.dropna(subset=["FROM LATITUDE", "FROM LONGITUDE"])
filtered_data['Installation Status'] = "Pending"

filtered_data.rename(columns={
    "ROAD NAMES": "ROAD_NAME",
    "PRINT COUNT": "PRINT_COUNT",
    "FROM LATITUDE": "lat",
    "FROM LONGITUDE": "lon",
    "Installation Status": "Installation_Status"
}, inplace=True)


# Setup Streamlit
st.title("Kano Signage Dashboard")
st.write("Showing all points on the map. Hover over a point to see details.")

st.sidebar.header("Filter Options")

# Filter by Lat and Long
lat_range = st.sidebar.slider("Latitude", min_value=-90.0, max_value=90.0, value=(-10.0, 10.0))
lon_range = st.sidebar.slider("Longitude", min_value=-180.0, max_value=180.0, value=(8.0, 15.0))
filtered_data = filtered_data[
    (filtered_data["lat"] >= lat_range[0]) & (filtered_data["lat"] <= lat_range[1]) &
    (filtered_data["lon"] >= lon_range[0]) & (filtered_data["lon"] <= lon_range[1])
]

# Filter by LGA
lga_filter = st.sidebar.multiselect("Select LGA", options=filtered_data["LGA"].unique())
if lga_filter:
    filtered_data = filtered_data[filtered_data["LGA"].isin(lga_filter)]

# Filter by Installation Status
installation_status_filter = st.sidebar.selectbox("Select Installation Status", options=filtered_data["Installation_Status"].unique())
if installation_status_filter:
    filtered_data = filtered_data[filtered_data["Installation_Status"] == installation_status_filter]

# # Add widget to select a point
# point_select = st.sidebar.selectbox("Select a Point", options=filtered_data["ROAD_NAME"].unique())
# if point_select:
#     filtered_data = filtered_data[filtered_data["ROAD_NAME"] == point_select]
#     lat, lon = filtered_data["lat"].values[0], filtered_data["lon"].values[0]
#     print(lat)
#     print(lon)
#     street_view_url = f"https://www.google.com/maps/embed/v1/streetview?location={lat},{lon}&key={api_key}&heading=210&pitch=10&fov=80"
#     st.components.v1.iframe(street_view_url, width=700, height=500)


# Define PyDeck Layer
scatter_layer = pdk.Layer(
    "ScatterplotLayer",
    data=filtered_data,
    get_position=["lon", "lat"],
    get_color=[200, 30, 0, 100],
    get_radius=56,
    pickable=True,
)

tooltip = {
    "html": "<b>Road Name:</b> {ROAD_NAME}<br>"
    "<b>LGA:</b> {LGA}<br>"
    "<b>Lat:</b> {lat}<br>"
    "<b>long:</b> {lon}<br>"
    "<b>Print Count:</b> {PRINT_COUNT}<br> "
    "<b>Installation Status:</b> {Installation_Status}",
    "style": {
        "color": "white",
        "backgroundColor": "rgba(0, 0, 0, 0.7)",
        "padding": "10px",
        "borderRadius": "5px"
    }
}

view_state = pdk.ViewState(
    latitude=filtered_data["lat"].mean(),
    longitude=filtered_data["lon"].mean(),
    zoom=11,
    pitch=0
)

r = pdk.Deck(
    layers=[scatter_layer],
    initial_view_state=view_state,
    tooltip=tooltip,
    width="100%"
)

st.pydeck_chart(r)
