# ┌───────────────┐
# │ Authorization │
# └───────────────┘
import os.path
import json

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

print('Authorizing...')
# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/calendar"]
creds = None
# The file token.json stores the user's access and refresh tokens, and is
# created automatically when the authorization flow completes for the first
# time.
if os.path.exists("token.json"):
    creds = Credentials.from_authorized_user_file("token.json", SCOPES)
# If there are no (valid) credentials available, let the user log in.
if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        flow = InstalledAppFlow.from_client_secrets_file(
            "credentials.json", SCOPES
        )
        creds = flow.run_local_server(port=0)
    # Save the credentials for the next run
    with open("token.json", "w") as token:
        token.write(creds.to_json())

service = build("calendar", "v3", credentials=creds)



from datetime import datetime, timedelta
import logging, traceback

def clean_upcoming_events(calendarID):
    '''Clean upcoming events from previous scrape to avoid duplication'''
    now = (datetime.utcnow()+timedelta(days=0)).isoformat() + "Z"  # 'Z' indicates UTC time
    print("Cleaning upcoming events in calendars...")
    events_result = service.events().list(
        calendarId=calendarID,
        timeMin=now,
        singleEvents=True,
        orderBy="startTime",
    ).execute()
    events = events_result.get("items", [])

    if not events:
        print("No upcoming events found.")

    for event in events:
        print('Cleaning ' + event["summary"])
        service.events().delete(calendarId=calendarID, eventId=event["id"]).execute()

def insert_events(events, calendarID):
    '''Insert events to Google Calendar'''
    for event in events:
        print(event)
        if type(event) is dict:
            event_json = event
        else:
            # event_json = json.dumps(event.gcal(), default=vars)
            event_json = event.gcal().__dict__

        try:
            print(event_json)
            event = service.events().insert(calendarId=calendarID, body=event_json).execute()
            print('Event created: %s\n' % (event.get('htmlLink'))) 
        except:
            logging.error(traceback.format_exc())
            print('Unable to insert event to Google Calendar')
    calendar_name = service.calendarList().get(calendarId=calendarID).execute()['summary'] 
    print(f'All events are inserted to calendar {calendar_name}!')

# ┌──────────┐
# │ Scraping │
# └──────────┘
from ruamel.yaml import YAML
from cowsay import cow                                    #type: ignore
config = YAML().load(open("config.yaml", "r"))

for site_config in config:
    calendarID = site_config['calendarID']
    clean_upcoming_events(calendarID) 
    
for site_config in config:
    sitename = site_config['sitename']
    source = site_config['source']
    calendarID = site_config['calendarID']

    match sitename:
        case 'meetup':
            from modules.meetup import scrape_meetup
            cow(f'Getting {sitename} events...')
            meetup_events = scrape_meetup(source)
            insert_events(meetup_events, calendarID) 
        
        case 'ticketbox':
            cow(f'Getting {sitename} events...')
            from modules.ticketbox import scrape_ticketbox
            ticketbox_events = scrape_ticketbox(source)
            insert_events(ticketbox_events, calendarID) 

        case 'liquipedia':
            cow(f'Getting {sitename} events...')
            from modules.liquipedia import scrape_liquipedia
            liquipedia_events = scrape_liquipedia(source)
            insert_events(liquipedia_events, calendarID) 

        case 'esportapi':
            cow(f'Getting {sitename} events...')
            from modules.esportapi import scrape_esportapi
            esportapi_events = scrape_esportapi()
            print(esportapi_events)
            insert_events(esportapi_events, calendarID) 

print('Done')