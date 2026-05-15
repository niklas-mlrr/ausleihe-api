import time
import json
import os

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from openpyxl import load_workbook
import pyautogui
import ctypes


changed_cells = []
change_count = 0
timeout_for_pageload = 30


def login(driver, config):
    terminal_window = pyautogui.getWindowsWithTitle(get_console_title())[0]

    driver.get(config["loginUrl"])
    WebDriverWait(driver, timeout_for_pageload).until(EC.presence_of_element_located((By.TAG_NAME, "body")))

    terminal_window.activate()
    input("\n\n\nMelden Sie sich im (gerade automatisch geöffnetem) IServ-Browserfenster an und \ndrücken Sie (in diesem Terminal-Fenster) Enter, wenn Sie eingeloggt sind.\n")
    print("Daten werden nun aktualisiert...\nInteragieren Sie nun bitte nicht mehr mit dem Browserfenster.")
 


def navigate_to_entry(driver, entry):
    if "url" in entry:
        driver.get(entry["url"])

    WebDriverWait(driver, timeout_for_pageload).until(EC.presence_of_element_located((By.TAG_NAME, "body")))


    if "iFrameToSwitchTo" in entry:
        if entry["iFrameToSwitchTo"] == "default":
            driver.switch_to.default_content()
        else:
            driver.switch_to.frame(entry["iFrameToSwitchTo"])


    for key in ["elementOneToClickOn", "elementTwoToClickOn", "elementThreeToClickOn"]:
        if key in entry:
            WebDriverWait(driver, timeout_for_pageload).until(EC.presence_of_element_located((By.XPATH, entry[key])))
            driver.find_element(By.XPATH, entry[key]).click()



def save_changed_content(config, excel_file):
    if (len(changed_cells) > 0):
        excel_file.save(config["excelFilePath"])

        print(f"\n\n\nEs wurde(n) {len(changed_cells)} Zelle(n) aktualisiert:")
        for changed_cell in changed_cells:
            print(f"{changed_cell[0]}: {changed_cell[1]} -> {changed_cell[2]}")
    else:
        print("\n\n\nEs wurden keine Zellen aktualisiert.")

# Beispiel für die Initialisierung des Chrome WebDrivers mit unterdrückter Ausgabe:
def get_silent_chrome_driver(chrome_options=None):
    service = Service(log_path=os.devnull)
    if chrome_options is None:
        chrome_options = Options()
    chrome_options.add_argument('--log-level=3')
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver


def get_console_title():
    BUF_SIZE = 256
    buffer = ctypes.create_unicode_buffer(BUF_SIZE)
    ctypes.windll.kernel32.GetConsoleTitleW(buffer, BUF_SIZE)
    return buffer.value