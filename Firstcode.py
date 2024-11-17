//Step 1: Fetch Leads from HubSpot API
//We'll fetch leads (contacts) from HubSpot using their API and store them in Google Sheets.
import requests
import json

# HubSpot API Key
API_KEY = 'YOUR_HUBSPOT_API_KEY'
HUBSPOT_CONTACTS_URL = f'https://api.hubapi.com/contacts/v1/lists/all/contacts/all?hapikey={API_KEY}'

# Function to fetch leads from HubSpot
def fetch_hubspot_leads():
    # Send GET request to HubSpot API to fetch all contacts
    response = requests.get(HUBSPOT_CONTACTS_URL)
    
    if response.status_code == 200:
        contacts = response.json()['contacts']
        leads = []
        for contact in contacts:
            lead = {
                'first_name': contact['properties'].get('firstname', {}).get('value', ''),
                'last_name': contact['properties'].get('lastname', {}).get('value', ''),
                'email': contact['properties'].get('email', {}).get('value', ''),
                'phone': contact['properties'].get('phone', {}).get('value', '')
            }
            leads.append(lead)
        return leads
    else:
        print(f"Error fetching HubSpot leads: {response.status_code}")
        return []
//Step 2: Update Google Sheets with Lead Data
//Next, we will write a function that updates Google Sheets with the lead data. You need to set up OAuth credentials for the Google Sheets API to authenticate.
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import os

# Google Sheets API setup
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SPREADSHEET_ID = 'YOUR_SPREADSHEET_ID'

# Authenticate and build the Sheets API client
def authenticate_google_sheets():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    service = build('sheets', 'v4', credentials=creds)
    return service

# Write lead data to Google Sheets
def write_to_google_sheets(leads):
    service = authenticate_google_sheets()
    sheet = service.spreadsheets()
    
    # Prepare the data to be inserted into the sheet
    values = [['First Name', 'Last Name', 'Email', 'Phone']]  # Header row
    for lead in leads:
        values.append([lead['first_name'], lead['last_name'], lead['email'], lead['phone']])

    body = {
        'values': values
    }
    
    # Update the Google Sheets with lead data
    sheet.values().update(spreadsheetId=SPREADSHEET_ID, range='A1', valueInputOption='RAW', body=body).execute()

//Step 3: Lead Scoring Logic
//You can add custom logic to score leads based on properties. For simplicity, this example uses a basic scoring function.
# Simple scoring function (customize as needed)
def calculate_lead_score(lead):
    score = 0
    if '@company.com' in lead['email']:
        score += 10
    if lead['phone']:
        score += 5
    return score

# Example usage: Calculate score for each lead
def add_lead_scores(leads):
    for lead in leads:
        lead['score'] = calculate_lead_score(lead)
    return leads
//Step 4: Send Automated Follow-Up Email via Gmail
//We'll use Gmail to send follow-up emails to new leads. For this, you must set up Gmail API credentials.
import base64
from googleapiclient.errors import HttpError
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow

# Gmail API setup
GMAIL_SCOPES = ['https://www.googleapis.com/auth/gmail.send']

# Authenticate Gmail API
def authenticate_gmail():
    creds = None
    if os.path.exists('token_gmail.json'):
        creds = Credentials.from_authorized_user_file('token_gmail.json', GMAIL_SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials_gmail.json', GMAIL_SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token_gmail.json', 'w') as token:
            token.write(creds.to_json())
    service = build('gmail', 'v1', credentials=creds)
    return service

# Function to send email using Gmail API
def send_email(service, to, subject, body):
    message = create_message('your-email@gmail.com', to, subject, body)
    try:
        send_message(service, 'me', message)
    except HttpError as error:
        print(f'An error occurred: {error}')

# Create a message for the email
def create_message(sender, to, subject, body):
    message = MIMEText(body)
    message['to'] = to
    message['from'] = sender
    message['subject'] = subject
    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
    return {'raw': raw_message}

# Send message through Gmail
def send_message(service, sender, message):
    try:
        message = service.users().messages().send(userId=sender, body=message).execute()
        print(f'Sent message to {sender} Message Id: {message["id"]}')
        return message
    except HttpError as error:
        print(f'An error occurred: {error}')
//Step 5: Putting Everything Together
//Now, let's combine all the parts of the solution into a main function:
def main():
    # Step 1: Fetch leads from HubSpot
    leads = fetch_hubspot_leads()
    
    if not leads:
        print("No leads found.")
        return
    
    # Step 2: Calculate lead scores
    leads = add_lead_scores(leads)
    
    # Step 3: Update Google Sheets with lead data
    write_to_google_sheets(leads)
    
    # Step 4: Send follow-up emails to hot leads (e.g., lead score > 15)
    service = authenticate_gmail()
    for lead in leads:
        if lead['score'] > 15:  # Hot lead threshold
            subject = "Thank you for your interest!"
            body = f"Hi {lead['first_name']},\n\nThanks for showing interest in our product. We will reach out soon!"
            send_email(service, lead['email'], subject, body)

if __name__ == "__main__":
    main()
//To deploy this solution, you would need to:

//Set up the HubSpot API key.
//Set up the Google Sheets and Gmail API credentials.
//Schedule this script to run periodically using a task scheduler (e.g., cron) or a cloud function.
