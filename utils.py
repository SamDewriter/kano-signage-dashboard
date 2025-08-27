import os
import pandas as pd
from google.oauth2 import service_account
from googleapiclient.discovery import build
import io
from googleapiclient.http import MediaIoBaseDownload
import streamlit as st
import pandas as pd


SCOPES = ['https://www.googleapis.com/auth/drive.readonly']


def get_drive_service():
    """Authenticate using service account and return Drive API client."""
    creds = service_account.Credentials.from_service_account_info(
        st.secrets["gcp-service-account"], 
        scopes=SCOPES
    )
    return build("drive", "v3", credentials=creds)


def fetch_updated_data():
    """Download the latest Excel file from Google Drive."""
    drive_service = get_drive_service()
    file_id = st.secrets["gcp-service-account"]["file_id"]
    file_name = "latest_installation_data.xlsx"
    folder_name = "downloads"
    os.makedirs(folder_name, exist_ok=True)
    file_path = os.path.join(folder_name, file_name)

    request = drive_service.files().export_media(
        fileId=file_id,
        mimeType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    fh = io.FileIO(file_path, "wb")
    downloader = MediaIoBaseDownload(fh, request)

    done = False
    while not done:
        status, done = downloader.next_chunk()
        if status:
            print(f"Download {int(status.progress() * 100)}%.")
    print(f"Downloaded to {file_path}")
    return file_path


def load_latest_data(filepath: str, sheet_name: str = "Copy of Responses") -> pd.DataFrame:
    """Load the latest installation data and clean headers/columns."""
    df = pd.read_excel(filepath, sheet_name=sheet_name)

    # Set first row as header, drop it from data
    df.columns = df.iloc[0]
    df = df[1:]

    # Keep relevant columns only
    return df[['Streets', 'LATITUDE', 'LONGITUDE', 'Installation Points']]


def aggregate_installation_data(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate installation points by street with mean coordinates."""
    grouped = (
        df.groupby('Streets')
          .agg({
              "LATITUDE": "mean",
              "LONGITUDE": "mean",
              "Installation Points": "count"
          })
          .reset_index()
          .rename(columns={
              "LATITUDE": "Mean Latitude",
              "LONGITUDE": "Mean Longitude"
          })
    )
    return grouped


def merge_with_old_data(new_data: pd.DataFrame, old_data_path: str) -> pd.DataFrame:
    """Merge new aggregated data with old harmonized cluster data."""
    old_df = pd.read_csv(old_data_path)

    merged = old_df.merge(new_data, on='Streets', how='left')

    # Fill coordinates with new ones if available
    merged['lat'] = merged['Mean Latitude'].combine_first(merged['lat'])
    merged['lon'] = merged['Mean Longitude'].combine_first(merged['lon'])

    # Installation status
    merged['Installation_Status'] = merged.apply(
        lambda row: 'Installed' if row['Streets'] in new_data['Streets'].values else 'Pending',
        axis=1
    )

    # Handle missing installation points
    merged['Installation Points'] = merged['Installation Points'].fillna(0).astype(int)

    return merged


def save_dashboard(merged_df: pd.DataFrame, output_path: str = "dashboard.csv"):
    """Save final dashboard-ready dataframe."""
    final_df = merged_df[[
        'Code', 'Streets', 'LGA', 'lat', 'lon', 'Print_Count',
        'Installation_Status', 'Installation Points'
    ]].rename(columns={'Installation Points': 'Installation_Points'})

    final_df.to_csv(output_path, index=False)


def update_existing_data():
    """Pipeline to update harmonized cluster data and save dashboard."""
    latest_df = load_latest_data('downloads/latest_installation_data.xlsx')
    aggregated_df = aggregate_installation_data(latest_df)
    merged_df = merge_with_old_data(aggregated_df, "Harmonized_Street_Cluster.csv")
    save_dashboard(merged_df)
    print("Dashboard data updated and saved to dashboard.csv")
