import pandas as pd
import folium
import streamlit as st
import math
from streamlit_folium import st_folium
import os
from dotenv import load_dotenv
load_dotenv()
from folium.plugins import MarkerCluster

api_key = os.getenv("GOOGLE_API_KEY")

@st.cache_data(ttl=3600)  # Cache data for 1 hour
def load_data():
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

    # Turn LGA FAGE to FAGGE
    filtered_data['LGA'] = filtered_data['LGA'].str.replace("FAGE", "FAGGE", regex=False)

    return filtered_data

df = load_data()

# Setup Streamlit
st.title("Kano Signage Dashboard")
st.write("Showing signage points on the map. Hover over a point to see details.")

st.sidebar.header("Filters")

# Sidebar Filters
lga_options = ["All"] + sorted(df["LGA"].unique().tolist())
selected_lga = st.sidebar.selectbox("Select LGA", options=lga_options)

status_options = ["All"] + sorted(df["Installation_Status"].unique().tolist())
selected_status = st.sidebar.selectbox("Select Installation Status", options=status_options)

# Start with all data
filtered_data = df.copy()

# Apply LGA filter
if selected_lga != "All":
    filtered_data = filtered_data[filtered_data["LGA"] == selected_lga]

# Apply Status filter
if selected_status != "All":
    filtered_data = filtered_data[filtered_data["Installation_Status"] == selected_status]

# Installation Summary
st.sidebar.subheader("Installation Summary")
st.sidebar.write(f"Total Points: {filtered_data.shape[0]}")
st.sidebar.write(f"Total Installed: {filtered_data[filtered_data['Installation_Status'] == 'Installed'].shape[0]}")
st.sidebar.write(f"Total Pending: {filtered_data[filtered_data['Installation_Status'] == 'Pending'].shape[0]}")

# Show map
if filtered_data.empty:
    st.warning("No data available for the selected filters.")
else:
    # Center map on mean lat/lon of current filtered data
    center_lat, center_lon = filtered_data[["lat", "lon"]].mean()

    m = folium.Map(location=[center_lat, center_lon], zoom_start=11, tiles="OpenStreetMap", height="1000px")
    # marker_cluster = MarkerCluster().add_to(m)

    # Add points
    for _, row in filtered_data.iterrows():
        popup_html = f"""
        <b>Road Name:</b> {row['ROAD_NAME']}<br>
        <b>LGA:</b> {row['LGA']}<br>
        <b>Lat:</b> {row['lat']}<br>
        <b>Lon:</b> {row['lon']}<br>
        <b>Print Count:</b> {row['PRINT_COUNT']}<br>
        <b>Installation Status:</b> {row['Installation_Status']}
        """
        folium.CircleMarker(
            location=[row['lat'], row['lon']],
            radius=6,
            color="#00c83f" if row['Installation_Status'] == 'Installed' else "#d51e1e",
            fill=True,
            fill_color='#00c83f' if row['Installation_Status'] == 'Installed' else '#d51e1e',
            fill_opacity=0.7,
            popup=folium.Popup(popup_html, max_width=300)
        ).add_to(m)

    # Fit map to bounds of points if there are at least 2 points
    if len(filtered_data) > 1:
        m.fit_bounds(filtered_data[["lat", "lon"]].values.tolist())

    st_data = st_folium(m, width=700, height=1000, key="map", returned_objects=[])