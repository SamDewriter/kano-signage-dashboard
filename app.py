import pandas as pd
import folium
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

# Turn LGA FAGE to F
filtered_data['LGA'] = filtered_data['LGA'].str.replace("FAGE", "FAGGE", regex=False)

# Setup Streamlit
st.title("Kano Signage Dashboard")
st.write("Showing all points on the map. Hover over a point to see details.")

st.sidebar.header("Filter Options")

# Filter by Lat and Long
# Set default lat/lon range to cover all data
lat_min, lat_max = float(filtered_data["lat"].min()), float(filtered_data["lat"].max())
lon_min, lon_max = float(filtered_data["lon"].min()), float(filtered_data["lon"].max())

lat_range = st.sidebar.slider("Latitude", min_value=-90.0, max_value=90.0, value=(lat_min, lat_max))
lon_range = st.sidebar.slider("Longitude", min_value=-180.0, max_value=180.0, value=(lon_min, lon_max))

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


# Installation Summary
st.sidebar.subheader("Installation Summary")
st.sidebar.write(f"Total Points: {filtered_data.shape[0]}")
st.sidebar.write(f"Total Installed: {filtered_data[filtered_data['Installation_Status'] == 'Installed'].shape[0]}")
st.sidebar.write(f"Total Pending: {filtered_data[filtered_data['Installation_Status'] == 'Pending'].shape[0]}")

# Create Folium map centered on mean lat/lon
center_lat = filtered_data["lat"].mean()
center_lon = filtered_data["lon"].mean()
m = folium.Map(location=[center_lat, center_lon], zoom_start=11, height="1000px")

# Add points to the map
for _, row in filtered_data.iterrows():
    popup_html = f"""
    <b>Road Name:</b> {row['ROAD_NAME']}<br>
    <b>LGA:</b> {row['LGA']}<br>
    <b>Lat:</b> {row['lat']}<br>
    <b>Long:</b> {row['lon']}<br>
    <b>Print Count:</b> {row['PRINT_COUNT']}<br>
    <b>Installation Status:</b> {row['Installation_Status']}
    """
    folium.CircleMarker(
        location=[row['lat'], row['lon']],
        radius=6,
        color='#c81e00',
        fill=True,
        fill_color='#c81e00',
        fill_opacity=0.7,
        popup=folium.Popup(popup_html, max_width=300)
    ).add_to(m)

# Display Folium map in Streamlit
from streamlit_folium import st_folium
st_folium(m, width=700, height=1000)
