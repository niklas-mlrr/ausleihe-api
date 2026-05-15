import pyautogui
import os
import time
from functions import *



with open("config.json", "r", encoding="utf-8") as config_file:
    config = json.load(config_file)

excel_file = load_workbook(config["excelFilePath"])
sheet = excel_file[config["excelSheetName"]]


cell = sheet['B4']
cell.value = "1234"
cell.number_format = 'General'




print("\n\n\n")
os.system('pause')