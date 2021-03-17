import datetime
import json
import os
import re
import time
import traceback
import urllib

import dotenv
import requests
from selenium import webdriver
import selenium
from selenium.webdriver.common.keys import Keys


dotenv.load_dotenv()

TIME_BETWEEN_CHECK = 1
SEARCH_FOR = "rtx 3080"

encoded_filtered = urllib.parse.quote(SEARCH_FOR)
base_url = "https://www.ldlc.com"
post_url = f"{base_url}/v4/fr-fr/form/search/filter/{encoded_filtered}"
referer_url = f"{base_url}/recherche/{encoded_filtered}/"

EXTRACT_LISTING_ITEM = r"<li id=\"pdt-[A-Z\d]+\" class=\"pdt-item\" data-id=\"[A-Z\d]+\" data-position=\"\d+\">\s*(?:<span class=\"mention\">\s*<span class=\"top-pdt\">Top des ventes</span>\s*</span>)?\s*<div class=\"pic\">.*?\s*</div>\s*<div class=\"dsp-cell-right\">.*?<h3 class =\"title-3\"><a href=\"(\/fiche\/[A-Z\d]+\.html)\">(.*?)</a></h3>\s*<p class=\"desc\">(.*?)</p>\s*</div>.*?<div class=\"stock-title\">Dispos</div>.*?<strong>Web</strong>\s*<div class=\"modal-stock-web pointer stock stock-(\d)\" data-stock-web=\"\d\"><span>(.*?)<\/span><\/div>\s*<\/div>"

opened_drivers = {}


def is_dead(driver):
    try:
        _ = driver.window_handles
        return False
    except selenium.common.exceptions.WebDriverException:
        return True


def get_status(driver):
    try:
        driver.execute(webdriver.remote.command.Command.STATUS)
        return "Alive"
    except:
        traceback.print_exc()
        return "Dead"

        
def wait_loaded():
    while driver.execute_script('return document.readyState;') != "complete":
        time.sleep(0.1)

        
def wait_displayed(element):
    while not element.is_displayed():
        time.sleep(0.1)


def go(url):
    driver.get(url)
    wait_loaded()


while True:
    print(f"\n\ntime is {datetime.datetime.now()}")
    
    response = requests.post(post_url, data={
        "filter[searchText]:": "",
        "filter[sort]:": "",
        "filter[fp][fp_l]:": "703",
        "filter[fp][fp_h]:": 1478,
    }, headers={
        "authority": "www.ldlc.com",
        "content-length": "0",
        "x-requested-with": "XMLHttpRequest",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36",
        "origin": "https://www.ldlc.com",
        "referer": "https://www.ldlc.com/recherche/rtx%203080/",
    })
    
    json_response = json.loads(response.text)
    html_listing = json_response["listing"]
    
    for match in re.finditer(EXTRACT_LISTING_ITEM, html_listing, re.MULTILINE | re.DOTALL):
        sub_url = match.group(1)
        title = match.group(2)
        description = match.group(3)
        availability = match.group(4)
        availability_display = match.group(5).replace("/", "").replace("<em>", "").strip()
        
        full_url = base_url + sub_url
        
        print(full_url, availability, availability_display, title)
        
        if availability == "1":
            if sub_url in opened_drivers:
                driver = opened_drivers[sub_url]
                
                if is_dead(driver):
                    try:
                        driver.close()
                    except:
                        traceback.print_exc()
                else:
                    continue
            
            chrome_options = webdriver.chrome.options.Options()
            chrome_options.add_experimental_option("detach", True)
            driver = webdriver.Chrome(options=chrome_options)
            
            opened_drivers[sub_url] = driver

            go("https://secure2.ldlc.com/fr-fr/Login/Login?returnUrl=%2Ffr-fr%2FAccount")
            
            dom_element = driver.find_element_by_id("Email")
            dom_element.send_keys(os.getenv("LDLC_EMAIL"))
            
            dom_element = driver.find_element_by_id("Password")
            dom_element.send_keys(os.getenv("LDLC_PASSWORD"))
            
            dom_element = driver.find_element_by_xpath("//button[contains(text(),'Connexion')]")
            dom_element.click()
            
            wait_loaded()
            
            go(full_url)
                
    time.sleep(TIME_BETWEEN_CHECK)
