from http.cookies import SimpleCookie
import json
from os import name
import os
from urllib.request import Request, urlopen
import attr

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

from bs4 import BeautifulSoup


COOKIE_SAVE_LOC = "./cookies.json"


#  This can be found by going into chrome on the webpage and copying a network request
#  to fetch or curl
HEADERS = {
    # "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    # "accept-language": "en-US,en;q=0.9",
    # "cache-control": "no-cache",
    # "pragma": "no-cache",
    # "sec-ch-ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
    # "sec-ch-ua-mobile": "?0",
    # "sec-ch-ua-platform": '"macOS"',
    # "sec-fetch-dest": "document",
    # "sec-fetch-mode": "navigate",
    # "sec-fetch-site": "none",
    # "sec-fetch-user": "?1",
    # "upgrade-insecure-requests": "1",
    "cookie": 'ubid-main=134-1736527-7232709; session-id=131-0220222-6997031; isFirstVisitAdbl=false; userType=amzn; adobeujs-optin=%7B%22aam%22%3Atrue%2C%22adcloud%22%3Atrue%2C%22aa%22%3Atrue%2C%22campaign%22%3Atrue%2C%22ecid%22%3Atrue%2C%22livefyre%22%3Atrue%2C%22target%22%3Atrue%2C%22mediaaa%22%3Atrue%7D; RoktRecogniser=6cacb17e-3f62-4b10-a67f-021461a658d2; lopAdbl=en_US; amznLopSignal={"A190M73E51S05J":{"lopAmzn":"en_US"}}; session-id-time=2332348433l; x-main=Sb2c1VTc8LdKxUKzyeCe3AiWCphmsQ2h; at-main=Atza|IwEBIL0o71OcNkfpoUlPG2iB3Ql4q96oHngLh-E8O7z5bI3ywYoQEbnEXYfQWi2wTPVN3m4fqKXdl1wS3TkkigvO1PyFb2reyiLZH8LxuiXu0l5Ooymr9pHfkj9m_aDk8w0r77GsW-1p1IviLtxVnVIsWsqgUXkL3RMrOXMCEcj_hX5QcL_xMUHISGgPgCKvolPHYFjBUdGPBH3l9Mb4SB1SPC9Bhu2J7TIH7_oUtRcT67KUQg; sess-at-main="2Pih9oHQqZ6o1MjlemU0ObM5RzZupLW7TSKRAr48NiA="; originalSourceCode="AUDOR6281128239YHO_12/03/2023 18:33"; AMCVS_165958B4533AEE5B0A490D45%40AdobeOrg=1; at_check=true; s_cc=true; currentSourceCode="ANONAUDW0378WS010202_12/14/2023 17:12"; s_plt=0.66; s_pltp=WebPlayer; mbox=PC#550e98c8d7854d6b9740cb05761ab580.35_0#1765818732|session#c5ae21526dc646e48a82accea6ed4d72#1702575792; session-token=OE45OZ3HxNeAgI21AxBlaw/V8LWFafZyDVS8ChUZ6xeEgwcXkpHfNBzb06yv37qvoVZo43gBNtKU8eYtc1/qSZ740EE6H8kxfKDFNxE9b27nDG22v67o01nZ2o1UKni6jd1QqKR2ZWjmuAgWIY/Sir2sLVgcm8Wo/TZB228YGLUt0ZUUMhnQanBx90e+2b0vp5yd7oyzh8GpAOj/QSVN1cYcdlpDQY2S6mcH6IdUJ6mR2DHHnFxNf35tMwgFSsmn0LR5+2Pcm0ZEMAXvZuJV5OHAJz9JxhLiG1Wx+khFB5JoY9nsss593OlpINOHNkhf7mYoT2G98BShrmKARV7b8UGziss8IHp25LbHpHmXmw7TA1pvmL/XOCGkcd2sVNb+; s_ips=2014; s_tp=2014; s_ppv=WebPlayer%2C100%2C100%2C2014%2C1%2C1; s_nr30=1702573944122-Repeat; s_tslv=1702573944122; AMCV_165958B4533AEE5B0A490D45%40AdobeOrg=359503849%7CMCIDTS%7C19706%7CMCMID%7C13672496198141191887961223155353779584%7CMCAID%7CNONE%7CMCOPTOUT-1702581144s%7CNONE%7CvVersion%7C5.0.1; csm-hit=tb:BM79CAQJM8ES7CNSH5WH+s-HMANNRXGDSQR3ESJHNN1|1702576038758&t:1702576038758&adb:adblk_no',
}

# we need to get the ASIN for all of these
# the actual web player URI is here https://www.audible.com/webplayer?asin=B003U868B4
# so we scan the index pages and get all ASINS

AudibleBookURI = lambda asin: f"https://www.audible.com/webplayer?asin={asin}"
LibraryURI = lambda page: f"https://www.audible.com/library/titles?page={page}"
ADBL_LOGIN_URI = "https://www.audible.com/signin?userType=adbl"

driver = webdriver.Chrome()  # or use another driver
options = Options()
# if headless:
#     options.add_argument("--headless")  # Run in headless mode (no browser UI)

# cookie = SimpleCookie()
# cookie.load(HEADERS["cookie"])

# Initialize the WebDriver
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)
#  For the boo kscraping, we need to switch over to slenium
# audible stores booksmarks as timestamps. so what we are going to do is


# NOTE: because we are recording the audio output this could take awhile


def scrape_book(asin):
    uri = AudibleBookURI(asin)
    print(f"Scraping book uri {uri}")
    # Set up Selenium WebDriver options

    # with open(COOKIE_SAVE_LOC, "r") as file:
    #     cookies = json.load(file)

    # for cookie in cookies:
    #     print(f"adding cookie {cookie}")
    #     driver.add_cookie(cookie)

    # Navigate to the URL
    driver.get(uri)

    # Close the WebDriver
    # driver.quit()


def login_and_get_cookie():
    # driver = webdriver.Chrome()  # or use another driver

    # Navigate to the login page
    driver.get(ADBL_LOGIN_URI)

    # Wait for user to manually enter credentials and log in
    # email = os.environ.get("ADBL_EMAIL", None) or input("Enter email: ")
    # password = os.environ.get("ADBL_PASSWORD", None) or input("Enter password: ")
    email = os.environ.get("ADBL_EMAIL", None)
    password = os.environ.get("ADBL_PASSWORD", None)

    driver.find_element(By.NAME, "email").send_keys(email)
    driver.find_element(By.NAME, "password").send_keys(password)
    driver.find_element(By.ID, "signInSubmit").click()

    # # Get cookies after login
    # cookies = driver.get_cookies()

    # with open(COOKIE_SAVE_LOC, "w") as file:
    #     json.dump(cookies, file)

    # driver.quit()

    # return cookies


def construct_library():
    book_asins = set()
    for page in range(1, 2):
        uri = LibraryURI(page)
        req = Request(uri, headers={"cookie": HEADERS["cookie"]})
        response = urlopen(req)
        soup = BeautifulSoup(response, "html.parser")
        books = soup.find_all("input", attrs={"name": "asin"})
        print(f"Fetching {uri} - {len(books)} books found")
        book_asins.update([book["value"] for book in books])
    return book_asins


# 0. login and get cookie
# 1: go to bookmarks page
# 2: create map of book marks with timeframe
# 3: go to bookmark
# 4: start playing
# 5: start audio recording of stream
# 6: wait for bookmark to finish
# 7: stop audio recording
# 8: save audio recording to file
# 9: repeat for all bookmarks
# 10: send audio file to whisper-asr for transcoding
if __name__ == "__main__":
    login_and_get_cookie()
    scrape_book("B003U868B4")
    # driver.quit()
    # asins = construct_library()
    # print(f"Found {len(asins)} books in library")
