import io
import os
import json

import pandas as pd
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/drive"]


def load_google_credentials(base_dir):
    """Load service account credentials from a JSON file."""
    credentials_path = os.path.join(base_dir, "config/credentials.json")
    with open(credentials_path, "r") as file:
        credentials_data = json.load(file)

    return Credentials.from_service_account_info(credentials_data, scopes=SCOPES)


def create_drive_service(credentials):
    """Create and return a Google Drive service client."""
    return build("drive", "v3", credentials=credentials)


def get_reporte_giros_factoring(service, folder_id, file_name, type_user):
    """Search for the file inside the target folder"""

    if type_user == "CLIENTE":
        column_name = "rut_cliente"
    elif type_user == "DEUDOR":
        column_name = "rut_deudor1"
    else:
        return None

    query = (
        f"name = '{file_name}' " f"and '{folder_id}' in parents " f"and trashed = false"
    )

    results = (
        service.files()
        .list(
            q=query,
            fields="files(id)",
            supportsAllDrives=True,
            includeItemsFromAllDrives=True,
        )
        .execute()
    )

    files = results.get("files", [])

    if not files:
        print(f"File '{file_name}' was not found.")
        return None

    file_id = files[0]["id"]

    file_bytes = service.files().get_media(fileId=file_id).execute()

    df = pd.read_excel(io.BytesIO(file_bytes), engine="openpyxl")
    if column_name == "CLIENTE":
        df[column_name] = df[column_name].astype(str).str.strip()
        df = df[df[column_name].str.len() == 11]
        unique_rucs = df[column_name].dropna().unique().tolist()
    else:
        df[column_name] = df[column_name].astype(str).str.split(r"\s*\|\s*")
        df = df.explode(column_name)
        df[column_name] = df[column_name].str.strip()
        df = df[df[column_name].str.len() == 11]
        unique_rucs = df[column_name].dropna().unique().tolist()

    return unique_rucs
