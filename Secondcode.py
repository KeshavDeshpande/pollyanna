import os
import base64
import smtplib
from email.mime.text import MIMEText
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

# Google Sheets and Gmail API setup
SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/gmail.send']
SHEET_ID = 'your-google-sheet-id'
SHEET_NAME = 'Sheet1'  # or the name of your sheet
SHEET_NURTURE_ID = 'your-nurture-sheet-id'
GMAIL_SENDER = 'your-email@gmail.com'

# Function to authenticate and get the Google Sheets API service
def authenticate_google_service(api_scope, creds_filename):
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', api_scope)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(creds_filename, api_scope)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return build('sheets', 'v4', credentials=creds)

# Function to fetch leads from Google Sheets
def get_leads_from_sheet(service):
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=SHEET_ID, range=SHEET_NAME).execute()
    return result.get('values', [])

# Lead scoring system
def calculate_lead_score(company_size, budget, industry, urgency):
    score = 0
    # Company Size
    size_points = {'1-50': 5, '51-200': 10, '201-1000': 15, '1000+': 20}
    score += size_points.get(company_size, 0)
    
    # Annual Budget
    budget_points = {'<10000': 5, '10000-50000': 10, '50001-100000': 15, '>100000': 20}
    score += budget_points.get(budget, 0)
    
    # Industry
    industry_points = {'Technology': 20, 'Finance': 15, 'Healthcare': 10, 'Retail': 5, 'Other': 0}
    score += industry_points.get(industry, 0)
    
    # Urgency
    urgency_points = {'Immediate': 20, 'Short-term': 15, 'Medium-term': 10, 'Long-term': 5}
    score += urgency_points.get(urgency, 0)
    
    return score

# Function to send email via Gmail API
def send_email(service, to, subject, body):
    message = MIMEText(body)
    message['to'] = to
    message['from'] = GMAIL_SENDER
    message['subject'] = subject
    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')

    try:
        service.users().messages().send(userId="me", body={'raw': raw_message}).execute()
        print(f"Email sent to {to}")
    except Exception as error:
        print(f"An error occurred: {error}")

# Function to store leads in Google Sheets (either high-priority or nurture)
def store_lead_to_sheet(service, lead_data, is_high_priority=True):
    sheet = service.spreadsheets()
    sheet_id = SHEET_ID if is_high_priority else SHEET_NURTURE_ID
    range_name = 'Sheet1!A1:D1' if is_high_priority else 'Sheet1!A1:D1'
    
    body = {
        'values': [lead_data]
    }
    
    result = sheet.values().append(spreadsheetId=sheet_id, range=range_name, 
                                   valueInputOption="RAW", body=body).execute()
    print(f"Lead added to sheet: {result}")

# Main function to process the leads
def main():
    # Authenticate Google Sheets and Gmail API
    sheets_service = authenticate_google_service(SCOPES, 'credentials.json')
    gmail_service = authenticate_google_service([SCOPES[1]], 'credentials.json')  # Only Gmail scope for email sending
    
    # Get leads from Google Sheets
    leads = get_leads_from_sheet(sheets_service)

    for lead in leads:
        if len(lead) < 4:
            print(f"Skipping incomplete lead: {lead}")
            continue  # Skip leads with missing data
        
        # Lead information
        company_size, budget, industry, urgency = lead[:4]
        
        # Calculate lead score
        score = calculate_lead_score(company_size, budget, industry, urgency)
        print(f"Lead score for {lead}: {score}")
        
        # Store lead based on score
        lead_data = lead + [score]
        if score > 70:
            # Send welcome email
            subject = "Welcome to TechNova!"
            body = f"Hi {lead[0]},\n\nThank you for your interest in our solutions. We'll be in touch soon."
            send_email(gmail_service, lead[3], subject, body)
            store_lead_to_sheet(sheets_service, lead_data, is_high_priority=True)
        else:
            store_lead_to_sheet(sheets_service, lead_data, is_high_priority=False)

if __name__ == "__main__":
    main()
//You will need to replace your-google-sheet-id with the actual ID of your Google Sheets.
//The Gmail API requires OAuth credentials, which you can set up through Google's API Console.
//This script handles incomplete data (by skipping rows with fewer than 4 entries), categorizes leads into high and low priority based on score, and sends a personalized email to the high-priority leads.
