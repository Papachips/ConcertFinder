from requests import get
from plexapi.myplex import MyPlexAccount
from datetime import date, datetime
import smtplib
from email.message import EmailMessage
import calendar
import time
import requests
import urllib
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

clientID = SEATGEEK_CLIENT_ID
appSecret = SEATGEEK_APP_SECRET
params = {
    'client_id': clientID,
    'client_secret': appSecret,
}
sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id=SPOTIFY_CLIENT_ID,client_secret=SPOTIFY_CLIENT_SECRET))

def getMonth():
    month = date.today().month + 2
    if(month == '13'):
        month = '01'
    if(month == '14'):
        month = '02'
    if(int(month) < 10):
        month = '0' + month
    return int(month)

def getYear(month):
    year = date.today().year if month !='12' else date.today().year + 1
    return year

def calculateDates():
    startDate = date.today()
    month = getMonth()
    year = getYear(month)
    monthEnd = int(calendar.monthrange(int(year), int(month))[1])
    endDate = date(year, month, monthEnd)

    return startDate, endDate

def createEmail():
    endMonth = int(getMonth())
    startMonth = int(endMonth-1)
    year = getYear(endMonth)
    message = EmailMessage()
    to = EMAIL_LIST
    message['Subject']='Concert Alerts for ' + calendar.month_name[startMonth] + '-' + calendar.month_name[endMonth] + ' ' + str(year)
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
        <th style="padding: 3px; border: 2px solid #ffcc00;">Spotify</th>
        </tr>
    </thead>

''' 
    
    return body

def sendEmail(email):
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(GMAIL, PASSWORD)
        smtp.send_message(email)    

def shorternURL(url):
    tinyUrl = 'http://tinyurl.com/api-create.php'

    shortUrl = tinyUrl + '?' \
        + urllib.parse.urlencode({"url": url})
    return requests.get(shortUrl).text

def kregFlix():
    account = MyPlexAccount(PLEX_USER, PLEX_PASSWORD)
    plex = account.resource(PLEX_SERVER).connect()
    music = plex.library.section(MUSIC_LIBRARY)
    kregflixMusic = music.search()
    kregflixArtists = []

    for artist in kregflixMusic:
        kregflixArtists.append(artist.title)

    return kregflixArtists

def getSpotifyLink(artist):
    uri = sp.search(q=artist, type='artist')['artists']['items'][0]['uri']
    spotifyURL = sp.artist(uri)['external_urls']['spotify']
    return spotifyURL

def parseEventDate(eventDate):
    yearMonthDay = eventDate.split('-')
    year = int(yearMonthDay[0])
    month = int(yearMonthDay[1])
    day = int(yearMonthDay[2].split('T')[0])
    parsedEventDate = date(year, month, day)

    return parsedEventDate

def getConcerts(locations, startDate, endDate, body, eventCount):
    for artist in kregflixArtists:
        artistFormatted = artist.replace(' ','-')
        url = f'https://api.seatgeek.com/2/events?per_page=100&performers.slug='+artistFormatted
        response = get(url=url, params=params)
        #dont really wanna fight with how seatgeek handles random special characters that might be in names
        try:
            events = response.json()['events']
        except:
            pass

        for event in events:
            city = ''
            state = ''
            eventTime = ''
            url = ''
            venue = ''
            spotify = ''
            if('venue' in event):
                if(event['venue']['country'] == 'US'):
                    city =  event['venue']['city'].lower()
                    state =  event['venue']['state'].lower()
                    if(any(tempDict['city'] == city for tempDict in locations)):
                        for location in locations:
                            if(city == location['city'] and state == location['state']):
                                city = city.title()
                                state = state.upper()
                                venue = event['venue']['name']
                                url =  event['venue']['url']# - ticket link
                                shortLink = shorternURL(url)
                                spotify = shorternURL(getSpotifyLink(artist))
                                eventTime = datetime.strptime(event['datetime_local'], '%Y-%m-%dT%H:%M:%S')
                                parsedEventDate = parseEventDate(event['datetime_local'])
                                formattedEventTime = eventTime.strftime("%m-%d-%y %H:%M")# - event start time
                                time.sleep(.25)
                                if(startDate <= parsedEventDate <= endDate):
                                    rowColor = '#a1b6d4' if eventCount % 2 == 0 else '#d0dbdf'

                                    body += '''
                                            <tr>
                                                <td style="padding: 3px; background-color:''' + rowColor + ''';">''' + artist + '''</td>
                                                <td style="padding: 3px; background-color:''' + rowColor + ''';">''' + city + '''</td>
                                                <td style="padding: 3px; background-color:''' + rowColor + ''';">''' + state + '''</td>
                                                <td style="padding: 3px; background-color:''' + rowColor + ''';">''' + formattedEventTime +'''</td>
                                                <td style="padding: 3px; background-color:''' + rowColor + ''';">''' + shortLink +'''</td>
                                                <td style="padding: 3px; background-color:''' + rowColor + ''';">''' + venue +'''</td>
                                                <td style="padding: 3px; background-color:''' + rowColor + ''';">''' + spotify +'''</td>
                                    '''
                                    eventCount = eventCount + 1
    return body


kregflixArtists = kregFlix()
locations = [{'city' : 'pittsburgh', 'state' : 'pa'},
             {'city' : 'mckees rocks', 'state' : 'pa'},
             {'city' : 'millvale', 'state' : 'pa'},
             {'city' : 'coraopolis', 'state' : 'pa'},
             {'city' : 'warrendale', 'state' : 'pa'},
             {'city' : 'burgettstown', 'state' : 'pa'},
             {'city' : 'erie', 'state' : 'pa'},
             {'city' : 'moon twp', 'state' : 'pa'},
             {'city':  'cuyahoga falls', 'state': 'oh'},
             {'city':  'lakewood', 'state': 'oh'},
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
