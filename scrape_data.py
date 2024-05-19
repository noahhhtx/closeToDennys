import requests
from bs4 import BeautifulSoup
import re
import pandas as pd
from geopy.geocoders import ArcGIS

def getPage(u, h):
    page = requests.get(u, headers=h)
    if page.status_code != 200:
        print("Page could not be accessed.")
        return None
    return page

def extractDigits(s):
    x = ""
    for i in s:
        if i.isdigit():
            x += i
    return x

def getDennys(h, geocoder):
    addresses = []
    urls = []
    url = "https://locations.dennys.com/sitemap.xml"
    sitemap = getPage(url, h)
    if sitemap is None:
        return None
    soup = BeautifulSoup(sitemap.content, "html.parser")
    for a in soup.select("loc"):
        a_text = a.get_text()
        last_page = a_text[a_text.rfind("/")+1:]
        if last_page.isnumeric():
            location = getPage(a_text, h)
            if location is None:
                continue
            try:
                soup2 = BeautifulSoup(location.content, "html.parser")
                add = soup2.find("address", class_="c-address")
                street = add.find("span", class_="c-address-street-1").text
                city = add.find("span", class_="c-address-city").text
                state = add.find("abbr", class_="c-address-state").text
                zip = add.find("span", class_="c-address-postal-code").text
                phone = extractDigits(soup2.find("div", {"id": "phone-main"}).text)
                addr = " ".join([street,city,state,zip])
                loc = geocoder.geocode(addr)
                addresses.append([street,city,state,zip,phone,a_text,loc.latitude,loc.longitude])
                print(street,city,state,zip,phone,loc.latitude,loc.longitude)
            except:
                print("Could not parse", a_text)
    df = pd.DataFrame(addresses, columns=["Street", "City", "State", "ZIP", "Phone", "Website", "Lat", "Long"])
    df.to_csv("./data/dennys_loc.csv", index = False)

def getLaQuinta(h, geocoder):
    addresses = []
    url = "https://www.wyndhamhotels.com/sitemap_en-us_lq_properties_1.xml"
    sitemap = getPage(url, h)
    if sitemap is None:
        return None
    soup = BeautifulSoup(sitemap.content, "html.parser")
    for a in soup.select("loc"):
        a_text = a.get_text()
        last_page = a_text[a_text.rfind("/") + 1:]
        if last_page.startswith("overview"):
            location = getPage(a_text, h)
            if location is None:
                continue
            soup2 = BeautifulSoup(location.content, "html.parser")
            try:
                addr = soup2.find("div", class_ = "property-address hidden-xs").find("span").get_text()[:-4]
                addr = " ".join(addr.split())
                parts = addr.split(",")
                street = parts[0].strip()
                city = parts[1].strip()
                x = parts[2].strip()
                state = x.split()[0]
                zip = x.split()[1].split("-")[0]
                addr = " ".join([street, city, state, zip])
                phone = extractDigits(soup2.find("div", class_="property-phone hidden-xs").find("a").get_text())[1:]
                loc = geocoder.geocode(addr)
                addresses.append([street, city, state, zip, phone, a_text, loc.latitude, loc.longitude])
                print(street, city, state, zip, phone, loc.latitude, loc.longitude)
            except:
                print("Could not parse", a_text)
                continue
    df = pd.DataFrame(addresses, columns=["Street", "City", "State", "ZIP", "Phone", "Website", "Lat", "Long"])
    df.to_csv("./data/laquinta_loc.csv", index=False)



headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
geolocator = ArcGIS()

getDennys(headers, geolocator)
getLaQuinta(headers, geolocator)