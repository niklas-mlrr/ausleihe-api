from functions import *


with open("config.json", "r", encoding="utf-8") as config_file:
    config = json.load(config_file)



driver = get_silent_chrome_driver()
driver.maximize_window()

if config["loginUrl"]:
    login(driver, config)



excel_file = load_workbook(config["excelFilePath"])
sheet = excel_file[config["excelSheetName"]]


for entry in config["entries"]:
    navigate_to_entry(driver, entry)
    time.sleep(waiting_time_between_elements)
    WebDriverWait(driver, timeout_for_pageload).until(EC.presence_of_element_located((By.XPATH, entry["elementToRead"])))
    new_content = driver.find_element(By.XPATH, entry["elementToRead"]).text

    
    current_cell_value = sheet[entry["excelCell"]].value

    if current_cell_value != new_content:
        sheet[entry["excelCell"]] = new_content
        change_count += 1
        changed_cell = [entry["excelCell"], current_cell_value, new_content]
        changed_cells.append(changed_cell)

    
driver.quit()

save_changed_content(config, excel_file)



print("\n\n\n")
os.system('pause')