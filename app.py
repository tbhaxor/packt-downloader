from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from os import path
import os
from time import sleep
import requests
from tqdm import tqdm
from argparse import ArgumentParser, RawDescriptionHelpFormatter
from pathlib import Path
from colorama import Fore, Style
import sys

parser = ArgumentParser(
    description="A simple packt subscribed videos downloader")

parser.add_argument("--email",
                    help="your email to login",
                    required=True,
                    metavar="EMAIL")
parser.add_argument("--password",
                    help="your password to login",
                    required=True,
                    metavar="PASSWORD")
parser.add_argument("--no-headless",
                    default=False,
                    help="show chrome window",
                    action="store_true")
parser.add_argument("--download-base-dir",
                    dest="down_dir",
                    help="the base download directory",
                    default=os.getcwd(),
                    metavar="PATH")
args = parser.parse_args()

# varriables
_PRODS = {}
_VIDEOS = {}
_DL_VIDEOS = []
DOWNLOAD = path.realpath(args.down_dir)

# options
option = Options()
option.headless = True if not args.no_headless else False
option.add_argument("--window-size=1920,1080")
option.add_argument("--start-maximized")

# inititalizing
print("{}[!]{} Initializing the application".format(Fore.LIGHTBLUE_EX,
                                                    Style.RESET_ALL))

# instancing the driver
try:
    driver = WebDriver(options=option)
    driver.get("https://subscription.packtpub.com/login")
except KeyboardInterrupt:
    driver.quit()
    exit(1)

# logging you in
try:
    print("{}[!]{} Logging you in".format(Fore.LIGHTBLUE_EX, Style.RESET_ALL))
    E = driver.find_element_by_xpath("//*[@id=\"login-input-email\"]")
    P = driver.find_element_by_xpath("//*[@id=\"login-input-password\"]")
    S = driver.find_element_by_xpath(
        "/html/body/div[2]/div[2]/div[2]/div/div[2]/div/form/button[1]")

    E.send_keys(args.email)
    P.send_keys(args.password)
    S.click()

    try:
        message = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.XPATH, "/html/body/div[2]/div[1]/div/span")))
        print("{}[X]{} {}".format(Fore.LIGHTRED_EX, Style.RESET_ALL,
                                  message.text))
        # driver.quit()
        sys.exit(1)
    except NoSuchElementException:
        print("{}[#]{} Successfully Logged In".format(Fore.LIGHTGREEN_EX,
                                                      Style.RESET_ALL))

    print("{}[!]{} Getting the History".format(Fore.LIGHTBLUE_EX,
                                               Style.RESET_ALL))
    history = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located(
            (By.XPATH, "//a[@class='link link-primary align-right']")))
    history.click()

    print("{}[!]{} Populating More Views".format(Fore.LIGHTBLUE_EX,
                                                 Style.RESET_ALL))
    _48 = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((
            By.XPATH,
            "//html[1]/body[1]/div[2]/div[2]/page-intro[1]/div[1]/div[1]/pagination[1]/nav[1]/div[2]/a[3]"
        )))
    _48.click()

    print("{}[!]{} Getting Product List".format(Fore.LIGHTBLUE_EX,
                                                Style.RESET_ALL))
    PRODUCTS_LIST = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((
            By.XPATH,
            "/html[1]/body[1]/div[2]/div[2]/div[1]/product-listing[1]/ul[1]")))

    products = PRODUCTS_LIST.find_elements_by_class_name("product")
    print("{}[!]{} Select the Product".format(Fore.LIGHTBLUE_EX,
                                              Style.RESET_ALL))
    for id, product in enumerate(products):
        title = driver.find_element_by_xpath(
            "/html[1]/body[1]/div[2]/div[2]/div[1]/product-listing[1]/ul[1]/li[%d]/div[1]/product[1]/div[1]/div[1]/div[2]/h2[1]"
            % (id + 1))
        link = driver.find_element_by_xpath(
            "/html[1]/body[1]/div[2]/div[2]/div[1]/product-listing[1]/ul[1]/li[%d]/div[1]/product[1]/div[1]/div[1]/div[1]/a[1]"
            % (id + 1))
        _PRODS[title.text.split("\n")[0]] = link.get_attribute("href")
        pass

    for id, title in enumerate(_PRODS.keys()):
        print("\t[%d] %s" % (id, title))

    _ = list(_PRODS.keys())[int(input("\t> "))]
    DOWNLOAD = path.join(DOWNLOAD, _.replace(" ", "-"))

    if not path.exists(DOWNLOAD):
        os.system("mkdir -p {}".format(DOWNLOAD))
        pass

    link = _PRODS[_]
    driver.get(link)

    SIDEBAR = driver.find_element_by_xpath(
        "//product-sidebar[@id='sidebar-wrapper']")

    if SIDEBAR.get_attribute("class") == "ng-scope ng-isolate-scope":
        # find button and click
        BTN = driver.find_element_by_xpath("//button[@id='menu-toggle']")
        BTN.click()

    TOC = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((
            By.XPATH,
            "/html[1]/body[1]/div[2]/div[2]/product-sidebar[1]/div[1]/ul[1]/div[1]/tabs[1]/div[1]/div[1]/tab-pane[1]/div[1]"
        )))

    print("{}[!]{} Fetching Table of Content".format(Fore.LIGHTBLUE_EX,
                                                     Style.RESET_ALL))
    topics = TOC.find_elements_by_tag_name("ng-repeat")
    print("{}[!]{} Fetched '{}' Topics".format(Fore.LIGHTBLUE_EX,
                                               Style.RESET_ALL, len(topics)))
    for id, topic in enumerate(topics):
        title = driver.find_element_by_xpath(
            "/html[1]/body[1]/div[2]/div[2]/product-sidebar[1]/div[1]/ul[1]/div[1]/tabs[1]/div[1]/div[1]/tab-pane[1]/div[1]/ng-repeat[%d]/li[1]/div[1]/a[1]/div[2]"
            % (id + 1))
        saveAs_pref = "Part-{:4}_{}".format(
            id + 1,
            title.get_attribute("title").replace(" ", "-")).replace(" ", "0")
        print("{}[!]{} Fetching Lessons in '{}'".format(
            Fore.LIGHTBLUE_EX, Style.RESET_ALL, title.get_attribute("title")))
        lessons = topic.find_elements_by_xpath("./div[1]/li")
        print("{}[!]{} Fetched '{}' Lessons in '{}'".format(
            Fore.LIGHTBLUE_EX, Style.RESET_ALL, len(lessons),
            title.get_attribute("title")))
        for id, lesson in enumerate(lessons):
            link = lesson.find_element_by_xpath("./a")
            title = link.find_element_by_xpath("./div[2]")
            _VIDEOS["{}_{:4}-{}".format(
                saveAs_pref, id + 1,
                title.get_attribute("title").replace(" ", "-")).replace(
                    " ", "0")] = link.get_attribute("href")
            pass
        pass

    print("{}[#]{} Begining Downloading of the Entire Course".format(
        Fore.LIGHTGREEN_EX, Style.RESET_ALL))
    print("{}[!]{} Saving in '{}'".format(Fore.LIGHTBLUE_EX, Style.RESET_ALL,
                                          DOWNLOAD))
    for video, link in _VIDEOS.items():
        if video.endswith("-"):
            video = video[:-1]
        print("{}[!]{} Getting Video '{}'".format(Fore.LIGHTBLUE_EX,
                                                  Style.RESET_ALL, video))
        driver.get(link)
        player = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.XPATH, "//video[@class='vjs-tech']")))
        chunk = 1024
        if video.endswith("-"):
            video = video[:-1]
        video = video.replace("/", "_")
        src = player.get_attribute("src")
        while not src:
            driver.get(link)
            player = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//video[@class='vjs-tech']")))
            src = player.get_attribute("src")
        print("{}[!]{} Downloading Video '{}'".format(Fore.LIGHTBLUE_EX,
                                                      Style.RESET_ALL, video))
        r = requests.get(src, stream=True)
        total = int(r.headers.get("content-length"))
        saveAs = path.join(DOWNLOAD, "{}.mp4".format(video))
        with open(saveAs, "wb") as file:
            for data in tqdm(iterable=r.iter_content(chunk_size=chunk),
                             ascii=True,
                             total=total / chunk,
                             unit="MB"):
                file.write(data)
            file.close()
            pass
        print("{}[#]{} Downloaded Video '{}'".format(Fore.LIGHTBLUE_EX,
                                                     Style.RESET_ALL, video))

    print("{}[!]{} Finished All Downloading".format(Fore.LIGHTBLUE_EX,
                                                    Style.RESET_ALL))
    driver.quit()
except KeyboardInterrupt:
    driver.quit()
    exit(1)
finally:
    driver.quit()
