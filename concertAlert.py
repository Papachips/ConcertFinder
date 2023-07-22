from bandsintown import Client
from plexapi.myplex import MyPlexAccount
from datetime import date, datetime
import smtplib
from email.message import EmailMessage
import calendar
import time
import requests
import urllib

def getMonth():
    month = str(date.today().month + 2)
    if(month == '13'):
        month = '01'
    if(month == '14'):
        month = '02'
    if(int(month) < 10):
        month = '0' + month
    return month

def getYear(month):
    year = str(date.today().year) if month !='12' else str(date.today().year + 1)
    return year

def calculateDates():
    today = str(date.today().strftime('%Y-%m-%d'))
    month = getMonth()
    year = getYear(month)

    monthEnd = str(calendar.monthrange(int(year), int(month))[1])
    formatedDate = year + '-' + month + '-' + monthEnd

    return today, formatedDate

def createEmail():
    endMonth = int(getMonth())
    startMonth = int(endMonth-1)
    year = getYear(endMonth)
    message = EmailMessage()
    to = [EMAIL_ADDRESSES]
    message['Subject']='Concert Alerts for ' + calendar.month_name[startMonth] + '-' + calendar.month_name[endMonth] + ' ' + year
    message['From']='ConcertFinder'
    message['To']=','.join(to)
    return message

def createEmailBody():
    
    body = '''<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.0 Transitional//EN" "http://www.w3.org/TR/REC-html40/loose.dtd">
<html>
<head>

    </head>
<body><table style="width: 100%; border-collapse: collapse; color: #000000; border: 2px solid #ffcc00;" bgcolor="#ffffff">
    <thead style="background-color: #ffcc00;">
        <tr>
        <th style="padding: 3px; border: 2px solid #ffcc00;">Artist</th>
        <th style="padding: 3px; border: 2px solid #ffcc00;">City</th>
        <th style="padding: 3px; border: 2px solid #ffcc00;">State</th>
        <th style="padding: 3px; border: 2px solid #ffcc00;">Date</th>
        <th style="padding: 3px; border: 2px solid #ffcc00;">URL</th>
        <th style="padding: 3px; border: 2px solid #ffcc00;">Venue</th>
        </tr>
    </thead>

''' 
    
    return body

def sendEmail(email):
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(GMAIL_ACCOUNT, GMAIL_SECRET)
        smtp.send_message(email)    

def shorternURL(url):
    tinyUrl = 'http://tinyurl.com/api-create.php'

    shortUrl = tinyUrl + '?' \
        + urllib.parse.urlencode({"url": url})
    return requests.get(shortUrl).text

def kregFlix():
    account = MyPlexAccount(PLEX_USER, PLEX_PW)
    plex = account.resource(PLEX_SERVER).connect()
    music = plex.library.section(PLEX_LIBRARY)
    kregflixMusic = music.search()
    kregflixArtists = []

    for artist in kregflixMusic:
        kregflixArtists.append(artist.title)

    return kregflixArtists

client = Client(BANDSINTOWN_ID)

def getConcerts(locations, startDate, endDate, body, eventCount):
    for artist in kregflixArtists:
        for location in locations:
            events = client.artists_events(artist, date=startDate + ',' + endDate)
            for event in events:
                city = ''
                state = ''
                eventTime = ''
                url = ''
                venue = ''
                if('venue' in event):
                    if(event.get('venue').get('country') == 'United States'):
                        city =  event.get('venue').get('city').lower()
                        state =  event.get('venue').get('region').lower()
                        if(city == location.get('city') and state == location.get('state')):
                            city = city.title()
                            state = state.upper()
                            venue = event.get('venue').get('name')# - venue
                            if('offers' in event):
                                url = event.get('offers')[0].get('url')# - ticket link
                                shortLink = shorternURL(url)
                            if('starts_at' in event):
                                eventTime = datetime.strptime(event.get('starts_at'), '%Y-%m-%dT%H:%M:%S')
                                eventTime = eventTime.strftime("%m-%d-%y %H:%M")# - event start time
                            time.sleep(5)
                            rowColor = '#a1b6d4' if eventCount % 2 == 0 else '#d0dbdf'

                            body += '''
                                    <tr>
                                        <td style="padding: 3px; background-color:''' + rowColor + ''';">''' + artist + '''</td>
                                        <td style="padding: 3px; background-color:''' + rowColor + ''';">''' + city + '''</td>
                                        <td style="padding: 3px; background-color:''' + rowColor + ''';">''' + state + '''</td>
                                        <td style="padding: 3px; background-color:''' + rowColor + ''';">''' + eventTime +'''</td>
                                        <td style="padding: 3px; background-color:''' + rowColor + ''';">''' + shortLink +'''</td>
                                        <td style="padding: 3px; background-color:''' + rowColor + ''';">''' + venue +'''</td>
                            '''
                            eventCount = eventCount + 1
    return body


kregflixArtists = kregFlix()
locations = [{'city' : 'pittsburgh', 'state' : 'pa'},
             {'city' : 'mckees rocks', 'state' : 'pa'},
             {'city' : 'millvale', 'state' : 'pa'},
             {'city' : 'coraopolis', 'state' : 'pa'},
             {'city' : 'warrendale', 'state' : 'pa'},
             {'city' : 'cleveland', 'state' : 'oh'}]

startDate, endDate  = calculateDates()
email = createEmail()
body = createEmailBody()
eventCount = 0

body = getConcerts(locations, startDate, endDate, body, eventCount)

body += '''	    
</tr>
</table></body>
</html>'''

email.set_content(body, subtype='html')

sendEmail(email)
