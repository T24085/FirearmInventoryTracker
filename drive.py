import os
import json
import io
from flask import Blueprint, request, redirect, session, url_for
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload

drive_bp = Blueprint('drive', __name__)
CLIENT_SECRETS_FILE = 'client_secret.json'
SCOPES = ['https://www.googleapis.com/auth/drive.file']
DATA_FILE = 'firearms.json'


@drive_bp.route('/login')
def login():
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        redirect_uri=url_for('drive.oauth2callback', _external=True)
    )
    auth_url, _ = flow.authorization_url(prompt='consent')
    return redirect(auth_url)


@drive_bp.route('/oauth2callback')
def oauth2callback():
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        redirect_uri=url_for('drive.oauth2callback', _external=True)
    )
    flow.fetch_token(authorization_response=request.url)
    creds = flow.credentials
    session['credentials'] = creds_to_dict(creds)
    return redirect('/frontend/index.html')  # You can change this to your actual frontend path


@drive_bp.route('/upload')
def upload_to_drive():
    creds = get_credentials()
    if not creds:
        return redirect('/login')

    service = build('drive', 'v3', credentials=creds)
    file_metadata = {'name': DATA_FILE}
    media = MediaFileUpload(DATA_FILE, mimetype='application/json')

    # Replace existing file if found
    results = service.files().list(q=f"name='{DATA_FILE}'", fields="files(id)").execute()
    files = results.get('files', [])

    if files:
        file_id = files[0]['id']
        service.files().update(fileId=file_id, media_body=media).execute()
    else:
        service.files().create(body=file_metadata, media_body=media).execute()

    return {"message": "Backup uploaded to Google Drive successfully"}


@drive_bp.route('/download')
def download_from_drive():
    creds = get_credentials()
    if not creds:
        return redirect('/login')

    service = build('drive', 'v3', credentials=creds)
    results = service.files().list(q=f"name='{DATA_FILE}'", fields="files(id)").execute()
    files = results.get('files', [])

    if not files:
        return {"error": "No backup file found"}, 404

    file_id = files[0]['id']
    request_drive = service.files().get_media(fileId=file_id)
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request_drive)

    done = False
    while not done:
        status, done = downloader.next_chunk()

    with open(DATA_FILE, 'wb') as f:
        f.write(fh.getvalue())

    return {"message": "Backup downloaded and restored successfully"}


def creds_to_dict(creds):
    return {
        'token': creds.token,
        'refresh_token': creds.refresh_token,
        'token_uri': creds.token_uri,
        'client_id': creds.client_id,
        'client_secret': creds.client_secret,
        'scopes': creds.scopes
    }


def get_credentials():
    if 'credentials' not in session:
        return None
    creds = Credentials(**session['credentials'])
    return creds
