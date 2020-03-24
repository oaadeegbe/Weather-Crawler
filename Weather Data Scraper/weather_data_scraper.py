'''
we are importing weather updates from a website.
To do that we find the website in question and inspect the respective element
so as to check the details i.e <div> tags of information we need.
'''

#import the required modules
from bs4 import BeautifulSoup
import pandas as pd
import requests
from datetime import date
import os, re
import zipcodes as z
import yagmail as ym


def fetch_data(zip_code = 72204):
    '''
    This function uses the input zipcode to generate city location and also
    create the url where the weather data will be fetched from.
    The weather data is then fetched from this url using the date generated.
        zipcode = 5 digit US zipcode only.
    '''
    
    #Get today's date
    today = date.today()
    todays_date = today.strftime("%a %#m/%d/%Y").replace('x0', '')
    year = today.strftime("%Y")


    #Generate url using zipcode
    city = z.matching(zip_code)[0]['city']
    state = z.matching(zip_code)[0]['state']
    city_state = city.replace(' ', '-').lower() + '/' + zip_code
    state_url = 'https://www.accuweather.com/en/browse-locations/nam/us/' + state.lower()


    #Generate url specific location id
    agent = {"User-Agent":'Chrome/80.0.3987.132'}
    res = requests.get(state_url, headers = agent)
    s = BeautifulSoup(res.text, features="lxml")
    # Getting the specific location of the url_location_id requires looking through the text extracted from the url
    text_list = s.findAll('script')
    city_id = text_list[2].get_text().strip()
    pattern = '"' + city + '","id":"(.+?)","localizedName":"' + city + '"'
    url_location_id = re.search(pattern, city_id).group(1)
    location_url = 'https://www.accuweather.com/en/us/' + city_state + '/daily-weather-forecast/' + url_location_id


    #Extract entire data from location_url
    res = requests.get(location_url, headers = agent)
    soup = BeautifulSoup(res.content, features="lxml")

    return soup, year, location_url, todays_date, city


def extract_data(attribute, s, y):
    '''
    This function extracts the essential weather data from the fetched data.
        attribute = The reference attribute to be used for extracting the required data.
        s = soup; the lxml content extracted from the url
        y = year
    '''
    #Create lists to store the extracted weather data
    dates = []
    temperatures = []
    summary = []
    precipitation = []
    todays_weather = []
    
    today = s.find('a', attrs = {'class': 'recent-location-display'})
    for a in today.stripped_strings:
        todays_weather.append(a)

    for a in s.findAll('a', href = True, attrs = {'class': attribute}):
        date = a.find('div', attrs = {'class':'date'})
        temps = a.find('div', attrs = {'class':'temps'})
        phrase = a.find('span', attrs = {'class':'phrase'})
        precipitation_info = a.find('div', attrs = {'class':'info precip'})

        weather_data_list = []
        for each in [date, temps, phrase, precipitation_info]:
            for string in each.stripped_strings:
                weather_data_list.append(string)
        
        dates.append(weather_data_list[0] + ' ' + weather_data_list[1] + '/' + y)
        temperatures.append(weather_data_list[2] + 'F ' + weather_data_list[3] + 'F')
        summary.append(weather_data_list[4])
        precipitation.append(weather_data_list[6])
    
    return dates, temperatures, summary, precipitation, todays_weather


def build_dataframe(d, t, s, p):
    '''
    This function saves the extracted data into a dataframe, and exports it into a CSV file.
    Extracted data from extract_data function is used as input;
        d = dates list
        t = temperatures list
        s = summary list
        p = precipotation list
    '''
    dataframe = pd.DataFrame({'Date': d, 'High/Low Temperature': t, 'Summary': s, 'Precipitation': p})

    if os.path.exists('weather.csv'):
        os.remove('weather.csv')
    dataframe.to_csv('weather.csv', index = False, encoding = 'utf-8')

    return dataframe


def send_mail(d, td, frame, l):
    '''
    This function sends the weather notification to email address(es).
        d = dates list
        td = today's date
        frame = dataframe
        l = today's weather list
    '''
    #The receiver can also be set up for user input, just like the zipcode.
    receiver = ['styccs@gmail.com', 'oaadeegbe@ualr.edu']
    subject = "Daily Weather Updates"
    today = d.index(td)

    body = frame.iloc[today]
    email_body = {'Location' : l[0], 'Current Temp' : l[1], 'Date' : body[0],
        'High/Low Temperatures': body[1],'Weather Summary': body[2], 'Precipitation': body[3]}

    email = ['Top of the Morning to You,',  '\n']
    for k, v in email_body.items():
        kv = k + ': ' + v
        email.append(kv)

    email.append('\n Thank You! \n Oluwamuyiwa Adeegbe \n (Python Enthusiast, Data Analyst)')
    email.append('weather1.gif')
    email = pd.Series(email)

    if True:
        ym.SMTP("oaadeegbe@ualr.edu").send(to = receiver, subject = subject, contents = email)
        print('Email Sent!')
    else:
        print("Email didn't go through.")

    return d, td, frame, l


def main():
    #list of soup, year, location_url, now_date, city
    weather_list = list(fetch_data(zip_code = input('Enter Zip Code: ')))
    general_attribute = 'forecast-list-card forecast-card'

    for i in range(2):
        #range is just two: 0 for today and 1 for other days.
        if i == 0:
            attribute_class = general_attribute + ' today'
            todays_data = list(extract_data(attribute_class, s = weather_list[0], y = weather_list[1]))
        
        elif i == 1:
            attribute_class = general_attribute
            other_data = list(extract_data(attribute_class, s = weather_list[0], y = weather_list[1]))
            del other_data[4]
    
    for i in range(len(todays_data)):
        if i < len(other_data):
            other_data[i].insert(0, todays_data[i][0])
            continue
        else:
            break

    frame = build_dataframe(other_data[0], other_data[1], other_data[2], other_data[3])
    sm = send_mail(other_data[0], other_data[0][0], frame, todays_data[4])


if __name__ == '__main__':
    main()
