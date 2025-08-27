import gdown
import os
import pandas as pd
from google.oauth2.credentials import Credentials
from google.oauth2 import service_account
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import io
from googleapiclient.http import MediaIoBaseDownload
from google.auth.transport.requests import Request
import streamlit as st
import json


def fetch_updated_data():
    SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

    client_config = {
        "web": {
            "client_id": st.secrets["web-google-drive"]["client_id"],
            "project_id": st.secrets["web-google-drive"]["project_id"],
            "auth_uri": st.secrets["web-google-drive"]["auth_uri"],
            "token_uri": st.secrets["web-google-drive"]["token_uri"],
            "auth_provider_x509_cert_url": st.secrets["web-google-drive"]["auth_provider_x509_cert_url"],
            "client_secret": st.secrets["web-google-drive"]["client_secret"],
        }
    }

    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    drive_service = build('drive', 'v3', credentials=creds)

    file_id = st.secrets["web-google-drive"]["file_id"]
    file_name = 'latest_installation_data.xlsx'
    folder_name = 'downloads'
    os.makedirs(folder_name, exist_ok=True)
    file_path = os.path.join(folder_name, file_name)

    request = drive_service.files().export_media(
        fileId=file_id,
        mimeType='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    fh = io.FileIO(file_path, 'wb')
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while not done:
        status, done = downloader.next_chunk()
        print(f"Download {int(status.progress() * 100)}%.")
    print(f"Downloaded to {file_path}")



def update_existing_data():
    d_filepath = 'downloads/latest_installation_data.xlsx'
    df = pd.read_excel(d_filepath, sheet_name=  "Copy of Responses")

    # Make the first row the column headers
    df.columns = df.iloc[0]
    df = df[1:]

    # Select columns
    df = df[['Streets', 'LATITUDE', 'LONGITUDE', 'Installation Points']]


    grouped_df = df.groupby('Streets').agg({
        "LATITUDE": "mean",
        "LONGITUDE": "mean",
        "Installation Points": "count"
    }).reset_index()


    grouped_df = grouped_df.rename(columns={
        "LATITUDE": "Mean Latitude",
        "LONGITUDE": "Mean Longitude",
    })

    old_df = pd.read_csv("Harmonized_Street_Cluster.csv")

    merged = old_df.merge(grouped_df, on='Streets', how='left')
    merged['lat'] = merged['Mean Latitude'].combine_first(merged['lat'])
    merged['lon'] = merged['Mean Longitude'].combine_first(merged['lon'])


    merged['Installation_Status'] = merged.apply(
        lambda row: 'Installed' if row['Streets'] in grouped_df['Streets'].values else 'Pending',
        axis=1  
    )

    merged['Installation Points'] = merged['Installation Points'].fillna(0)

    final_df = merged[['Code', 'Streets', 'LGA', 'lat', 'lon', 'Print_Count', 'Installation_Status', 'Installation Points']]


    final_df['Installation Points'] = final_df['Installation Points'].astype(int)
    final_df.rename(columns={'Installation Points': 'Installation_Points'}, inplace=True)
    final_df.to_csv('dashboard.csv', index=False)


fetch_updated_data()
update_existing_data()