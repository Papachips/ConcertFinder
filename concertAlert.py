import ticketpy
from plexapi.myplex import MyPlexAccount
from datetime import date
import smtplib
from email.message import EmailMessage
import calendar

def getMonth():
    month = str(date.today().month + 2)
    #since we get 2 months ahead, we need to account for edge cases of running the script in November and December and adjust accordingly.
    if(month == '13'):
        month = '01'
    if(month == '14'):
        month = '02'
    if(int(month) < 10):
        month = '0' + month
    return month

def getYear(month):
    #we need to set the year ahead if we are running in December since we go 2 months out.
    year = str(date.today().year) if month is not '12' else str(date.today().year + 1)
    return year

def createEmail():
    endMonth = int(getMonth())
    startMonth = int(endMonth-1)
    year = getYear(endMonth)
    message = EmailMessage()
    to = ['EMAIL_ADDRESS', 'EMAIL_ADDRESS]
    message['Subject']='Concert Alerts for ' + calendar.month_name[startMonth] + '-' + calendar.month_name[endMonth] + ' ' + year
    message['From']='EMAIL_ADDRESS'
    message['To']=','.join(to)
    return message

def createEmailBody():
    #the best way i could find to embed html and styling into an email body in python
    body = '''<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.0 Transitional//EN" "http://www.w3.org/TR/REC-html40/loose.dtd">
<html>
<head>

    </head>
<body><table style="width: 100%; border-collapse: collapse; color: #000000; border: 2px solid #ffcc00;" bgcolor="#ffffff">
    <thead style="background-color: #ffcc00;">
        <tr>
        <th style="padding: 3px; border: 2px solid #ffcc00;">Event</th>
        <th style="padding: 3px; border: 2px solid #ffcc00;">City</th>
        <th style="padding: 3px; border: 2px solid #ffcc00;">Status</th>
        <th style="padding: 3px; border: 2px solid #ffcc00;">Date</th>
        <th style="padding: 3px; border: 2px solid #ffcc00;">Price</th>
        <th style="padding: 3px; border: 2px solid #ffcc00;">URL</th>
        <th style="padding: 3px; border: 2px solid #ffcc00;">Venue</th>
        <th style="padding: 3px; border: 2px solid #ffcc00;">State</th>
        </tr>
    </thead>

''' 
    
    return body

def sendEmail(email):
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login('EMAIL_ADDRESS', 'SECRET')
        smtp.send_message(email)    

def calculateDates():
    today = str(date.today().strftime('%Y-%m-%d')) + 'T20:00:00Z'
    month = getMonth()
    year = getYear(month)

    monthEnd = str(calendar.monthrange(int(year), int(month))[1])
    formatedDate = year + '-' + month + '-' + monthEnd + 'T20:00:00Z'

    return today, formatedDate

#connect to a plex account with a music library to get an always up to date and curated list of artists i am interested in
def plexServer():
    account = MyPlexAccount('PLEX_ACCOUNT_NAME', 'PLEX_PASSWORD')
    plex = account.resource('PLEX_SERVER_NAME').connect()
    music = plex.library.section('PLEX_LIBRARY_NAME')
    musicLib = music.search()
    musicArtists = []

    for artist in musicLib:
        musicArtists.append(artist.title)

    return musicArtists

def getConcerts(state, cities, genre, body, eventCount):

    pages = client.events.find(
        classification_name=genre,
        state_code=state,
        start_date_time=today,
        end_date_time= formatedDate
    )

    events = []
    for page in pages:
        for event in page:
            for venue in event.venues:
                if(venue.city in cities):
                    for artist in musicArtists:
                        if(artist in event.name and event.name not in events):
                            events.append(event.name)
                            price = ''
                            if(len(event.price_ranges) == 0):
                                price = 'N/A'
                            else:
                                min = str(event.price_ranges[0].get('min'))
                                if(min == '0.0'):
                                    price = 'N/A'
                                else:
                                    price = '$' + min

                            rowColor = '#a1b6d4' if eventCount % 2 == 0 else '#d0dbdf'

                            body += '''
                                    <tr>
                                        <td style="padding: 3px; background-color:''' + rowColor + ''';">''' + event.name + '''</td>
                                        <td style="padding: 3px; background-color:''' + rowColor + ''';">''' + venue.city + '''</td>
                                        <td style="padding: 3px; background-color:''' + rowColor + ''';">''' + event.status + '''</td>
                                        <td style="padding: 3px; background-color:''' + rowColor + ''';">''' + event.local_start_date + '''</td>
                                        <td style="padding: 3px; text-align:center; background-color:''' + rowColor + ''';">''' + price + '''</td>
                                        <td style="padding: 3px; background-color:''' + rowColor + ''';">''' + event.json.get('url') +'''</td>
                                        <td style="padding: 3px; background-color:''' + rowColor + ''';">''' + event.venues[0].name +'''</td>
                                        <td style="padding: 3px; background-color:''' + rowColor + ''';">'''+ state +'''</td>
                            '''
                            eventCount = eventCount + 1
    return body

client = ticketpy.ApiClient('TICKET_MASTER_KEY')

musicArtists = plexServer()
today, formatedDate = calculateDates()
email = createEmail()
body = createEmailBody()

eventCount = 0

#finishing the email body with the table of concerts and closing tags
body = getConcerts(state='PA', cities=['Millvale', 'Pittsburgh'], genre='rock', body=body, eventCount=eventCount)
body = getConcerts(state='OH', cities=['Cleveland'], genre='rock', body=body, eventCount=eventCount+1)

body += '''	    
</tr>
</table></body>
</html>'''

email.set_content(body, subtype='html')

sendEmail(email)
