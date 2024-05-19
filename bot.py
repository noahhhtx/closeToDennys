import pandas as pd
from geopy.distance import geodesic as gd
from geopy.geocoders import ArcGIS
import folium
import selenium.webdriver as wd
from selenium.webdriver.chrome.options import Options
import os
import time
from datetime import datetime
import sys
import discord
from dotenv import load_dotenv
from discord.ext import commands, tasks

def dist(base, loc):
    return gd(base, loc).miles

def findClosest(base, locs):
    locs['point'] = locs[['Lat', 'Long']].apply(tuple, axis=1)
    locs["dist"] = locs.apply(lambda row: dist(base, row["point"]), axis=1)
    return locs[locs.dist == locs.dist.min()].iloc[0]

load_dotenv()
client = commands.Bot(command_prefix="d!",intents=discord.Intents.all())
TOKEN = os.getenv('DISCORD_TOKEN')

@client.event
async def on_ready():
    print("Logged in as a bot {0.user}".format(client))

@client.command(name = 'locate', brief="Finds closest Denny's and La Quinta locations.", description="Finds closest Denny's and La Quinta locations.")
async def getLocations(ctx, *args):

    geolocator = ArcGIS()
    base_str = " ".join(args)

    now = datetime.now()
    current_time = now.strftime("%Y_%m_%d_%H_%M_%S_%f")
    filename = "map_" + current_time + ".html"

    base_loc = None
    base_point = None

    try:
        base_loc = geolocator.geocode(base_str)
        base_point = (base_loc.latitude, base_loc.longitude)
    except:
        await ctx.send("ERROR: Address could not be geocoded.")
        return

    dennys = pd.read_csv("./data/dennys_loc.csv")
    la_quinta = pd.read_csv("./data/laquinta_loc.csv")

    d = findClosest(base_point, dennys)
    print(d)

    l = findClosest(base_point, la_quinta)
    print(l)

    points = [[base_point[0], base_point[1]], [d["Lat"], d["Long"]], [l["Lat"], l["Long"]]]
    points = pd.DataFrame(points, columns=["Lat", "Long"])

    m = folium.Map(location=base_point)
    folium.CircleMarker(base_point, radius=5, color="blue", fill = True, tooltip=folium.Tooltip("Base Location", permanent=True)).add_to(m)
    folium.CircleMarker(d["point"], radius=5, color="red", fill = True, tooltip=folium.Tooltip("Closest Denny's", permanent=True)).add_to(m)
    folium.CircleMarker(l["point"], radius=5, color="green", fill = True, tooltip=folium.Tooltip("Closest La Quinta", permanent=True)).add_to(m)

    sw = points[['Lat', 'Long']].min().values.tolist()
    ne = points[['Lat', 'Long']].max().values.tolist()

    m.fit_bounds([sw, ne], padding=[5,5])

    m.save(filename)
    path = os.getcwd() + "\\" + filename

    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    driver = wd.Chrome(options=chrome_options)
    driver.set_window_size(1000, 750)
    driver.get(path)
    time.sleep(3)
    ss_filename = "screenshot_" + current_time + ".png"
    driver.save_screenshot(ss_filename)

    img = discord.File(ss_filename)
    att_img = "attachment://" + ss_filename
    title = "Result"
    embed = discord.Embed(title=title, description="")
    embed.set_image(url=att_img)

    base_point_str = str(base_point).replace(" ", "")
    dennys_point_str = str(d["point"]).replace(" ", "")
    dennys_addr = " ".join(str(v) for v in [d["Street"], d["City"], d["State"], d["ZIP"]])
    dennys_tel = str(d["Phone"])
    dir_to_dennys = "https://www.google.com/maps/dir/" + base_point_str + "/" + dennys_point_str
    dennys_info = dennys_addr + "\nTelephone: " + dennys_tel + "\n[Directions](%s)" % dir_to_dennys
    embed.add_field(name="Closest Denny's", value=dennys_info, inline = False)
    lq_point_str = str(l["point"]).replace(" ", "")
    lq_addr = " ".join(str(v) for v in [l["Street"], l["City"], l["State"], l["ZIP"]])
    lq_tel = str(l["Phone"])
    dir_to_lq = "https://www.google.com/maps/dir/" + base_point_str + "/" + lq_point_str
    lq_info = lq_addr + "\nTelephone: " + lq_tel + "\n[Directions](%s)" % dir_to_lq
    embed.add_field(name="Closest La Quinta", value=lq_info, inline = False)

    await ctx.send(file=img, embed=embed)

    os.remove(filename)
    os.remove(ss_filename)

#getLocations(geolocator, base_str)

client.run(TOKEN)
