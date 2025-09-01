import pandas as pd
import folium
import streamlit as st
from streamlit_folium import st_folium
from utils import update_existing_data
from folium.plugins import MarkerCluster
import plotly.express as px

# ----------------------------
# Streamlit Page Config
# ----------------------------
st.set_page_config(
    page_title="Kano Signage Dashboard",
    page_icon="🗺️",
    layout="wide"
)

# ----------------------------
# Load Data
# ----------------------------
@st.cache_data(ttl=3600)  # Cache data for 1 hour
def load_data():
    df = pd.read_csv("dashboard.csv")
    return df

df = load_data()

# ----------------------------
# Header
# ----------------------------
st.title("🗺️ Kano Street Name Dashboard")
st.caption("Interactive dashboard showing signage installation progress across Kano.")

# ----------------------------
# Sidebar Filters
# ----------------------------
st.sidebar.header("Filters")

lga_options = ["All"] + sorted(df["LGA"].unique().tolist())
selected_lga = st.sidebar.selectbox("Select LGA", options=lga_options)

status_options = ["All"] + sorted(df["Installation_Status"].unique().tolist())
selected_status = st.sidebar.selectbox("Select Installation Status", options=status_options)

# ----------------------------
# Apply Filters
# ----------------------------
filtered_data = df.copy()

if selected_lga != "All":
    filtered_data = filtered_data[filtered_data["LGA"] == selected_lga]

if selected_status != "All":
    filtered_data = filtered_data[filtered_data["Installation_Status"] == selected_status]

# ----------------------------
# KPI Calculations
# ----------------------------
total_points = filtered_data.shape[0]
total_installed = filtered_data[filtered_data["Installation_Status"] == "Installed"].shape[0]
total_pending = filtered_data[filtered_data["Installation_Status"] == "Pending"].shape[0]
install_rate = (total_installed / total_points * 100) if total_points else 0

# ----------------------------
# KPI Card Function
# ----------------------------
def kpi(label: str, value: str, help: str | None = None):
    st.markdown(
        f"""
        <div style="padding:14px;
                    border-radius:16px;
                    background:#fff;
                    box-shadow:0 1px 3px rgba(0,0,0,.08);
                    border:1px solid #e5e7eb;
                    margin-bottom:20px;">
            <div style="font-size:12px;color:#64748b">{label}</div>
            <div style="font-size:28px;font-weight:700;color:#0f172a;line-height:1.1">{value}</div>
            {f'<div style="font-size:12px;color:#94a3b8;margin-top:6px">{help}</div>' if help else ''}
        </div>
        """,
        unsafe_allow_html=True
    )

# ----------------------------
# KPI Section
# ----------------------------
st.subheader("📊 Installation Summary")

col1, col2, col3, col4 = st.columns(4)

with col1:
    kpi("Total Points", f"{total_points}")

with col2:
    kpi("Installed", f"{total_installed}", help="Completed installations")

with col3:
    kpi("Pending", f"{total_pending}", help="Awaiting completion")

with col4:
    kpi("Installation Rate", f"{install_rate:.1f}%", help="Installed / Total")
    st.progress(int(install_rate))

st.markdown("---")

# ----------------------------
# Charts
# ----------------------------
if not filtered_data.empty:
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📍 Distribution by LGA")
        lga_counts = (
            filtered_data.groupby("LGA")["Installation_Status"]
            .count()
            .sort_values(ascending=False)
        )
        st.bar_chart(lga_counts)

    with col2:
        st.subheader("✅ Status Breakdown")
        status_counts = filtered_data["Installation_Status"].value_counts().reset_index()
        status_counts.columns = ["Status", "Count"]
        fig = px.pie(
            status_counts,
            names="Status",
            values="Count",
            color="Status",
            color_discrete_map={"Installed": "#00c83f", "Pending": "#d51e1e"},
            hole=0.4,
        )
        st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# ----------------------------
# Map Section with Clustering
# ----------------------------
st.subheader("🗺️ Map of Signage Points")

if filtered_data.empty:
    st.warning("No data available for the selected filters.")
else:
    # Center map on mean lat/lon
    center_lat, center_lon = filtered_data[["lat", "lon"]].mean()

    m = folium.Map(location=[center_lat, center_lon], zoom_start=11, tiles="OpenStreetMap")

    # Add points
    for _, row in filtered_data.iterrows():
        popup_html = f"""
        <b>Street Name:</b> {row['Streets']}<br>
        <b>LGA:</b> {row['LGA']}<br>
        <b>Lat:</b> {row['lat']}<br>
        <b>Lon:</b> {row['lon']}<br>
        <b>Print Count:</b> {row['Print_Count']}<br>
        <b>Installation Points:</b> {row['Installation_Points']}<br>
        <b>Installation Status:</b> {row['Installation_Status']}
        """
        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=3,
            color="#00c83f" if row["Installation_Status"] == "Installed" else "#d51e1e",
            fill=True,
            fill_color="#00c83f" if row["Installation_Status"] == "Installed" else "#d51e1e",
            fill_opacity=0.7,
            popup=folium.Popup(popup_html, max_width=300)
        ).add_to(m)

    if len(filtered_data) > 1:
        m.fit_bounds(filtered_data[["lat", "lon"]].values.tolist())

    st_folium(m, width=1000, height=600, key="map", returned_objects=[])

# ----------------------------
# Download & Footer
# ----------------------------
st.markdown("---")

st.download_button(
    "📥 Download Filtered Data",
    filtered_data.to_csv(index=False).encode("utf-8"),
    file_name="filtered_data.csv",
    mime="text/csv",
)

st.caption(f"Last updated: {pd.Timestamp.now().strftime('%d %b %Y %H:%M')}")

if st.button("🔄 Refresh Data"):
    update_existing_data()
    df = load_data()
