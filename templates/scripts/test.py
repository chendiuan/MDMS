import os
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import time
from datetime import datetime
from PIL import Image

current_directory = os.path.dirname(os.path.abspath(__file__))
line_notify_token = "lcw8VRKeDQJj6VY2Lfcs9mAMVzaMXlMngdD36RSYWej"
line_notify_api = 'https://notify-api.line.me/api/notify'
today_date = datetime.now().strftime("%Y-%m-%d")
temp_screenshot = os.path.join(current_directory, 'table_screenshot.png')
cropped_table_screenshot = os.path.join(current_directory, 'cropped_table_screenshot.png')
url = 'https://goodinfo.tw/tw2/StockList.asp?MARKET_CAT=%E8%87%AA%E8%A8%82%E7%AF%A9%E9%81%B8&INDUSTRY_CAT=%E6%88%91%E7%9A%84%E6%A2%9D%E4%BB%B6&FILTER_ITEM0=%E5%B9%B4%E5%BA%A6%E2%80%93ROE%28%25%29&FILTER_VAL_S0=30&FILTER_VAL_E0=&FILTER_SHEET=%E5%B9%B4%E7%8D%B2%E5%88%A9%E8%83%BD%E5%8A%9B&WITH_ROTC=F&FILTER_QUERY=%E6%9F%A5++%E8%A9%A2'
def send_line_notify(message, file_path=None):
    headers = {
        "Authorization": f"Bearer {line_notify_token}"
    }
    payload = {
        'message': message
    }
    files = None
    if file_path:
        files = {
            'imageFile': open(file_path, 'rb')
        }
    r = requests.post(line_notify_api, headers=headers, data=payload, files=files)
    return r.status_code

def init_driver():
    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--incognito")
    chrome_options.add_argument("--disable-preconnect")
    chrome_options.add_argument("--dns-prefetch-disable")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--ignore-certificate-errors")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument('--headless')  # Active headless
    chrome_options.add_argument('--disable-gpu')  # Shutdown GPU
    return webdriver.Chrome(options=chrome_options)

def click_element(driver, xpath, description):
    try:
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, xpath))).click()
        print(f"成功點擊 {description}")
    except Exception as e:
        print(f"無法點擊 {description}: {e}")
    time.sleep(2)

def input_text(driver, xpath, text, description):
    try:
        element = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, xpath)))
        element.clear()
        element.send_keys(text)
        print(f"成功在 {description} 中輸入 {text}")
    except Exception as e:
        print(f"無法在 {description} 中輸入 {text}: {e}")
    time.sleep(1)

def select_dropdown_option(driver, xpath, visible_text, description):
    try:
        element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, xpath)))
        select = Select(element)
        select.select_by_visible_text(visible_text)
        print(f"成功選取 {description} 選項 {visible_text}")
    except Exception as e:
        print(f"無法選取 {description} 選項 {visible_text}: {e}")
    time.sleep(2)


def screenshot_table(driver, xpath, file_path):
    try:
        table_element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, xpath)))
        location = table_element.location
        size = table_element.size
        if size['width'] == 0 or size['height'] == 0:
            raise Exception("表格未正確加載或不可見")
        temp_screenshot = os.path.join(current_directory, 'temp_screenshot.png')
        driver.save_screenshot(temp_screenshot)
        image = Image.open(temp_screenshot)
        left = location['x']
        top = location['y']
        right = location['x'] + size['width']
        bottom = location['y'] + size['height']
        image = image.crop((left, top, right, bottom))
        image.save(file_path)
        print(f"表格已成功截圖並保存至 {file_path}")
        os.remove(temp_screenshot)
    except Exception as e:
        print(f"無法截取表格截圖: {e}")

def full_page_screenshot(driver, save_path):
    original_size = driver.get_window_size()
    required_width = driver.execute_script('return document.body.parentNode.scrollWidth')
    required_height = driver.execute_script('return document.body.parentNode.scrollHeight')
    driver.set_window_size(required_width, required_height)
    driver.save_screenshot(save_path)
    driver.set_window_size(original_size['width'], original_size['height'])

def crop_image_to_table(image_path, xpath):
    try:
        image = Image.open(image_path)
        table_element = driver.find_element(By.XPATH, xpath)
        location = table_element.location
        size = table_element.size
        left = location['x'] - 20
        top = location['y']
        right = location['x'] + size['width']
        bottom = location['y'] + size['height']
        cropped_image = image.crop((left, top, right, bottom))
        cropped_image.save("cropped_table_screenshot.png")
    except Exception as e:
        print(f"裁剪圖片失敗: {e}")

driver = init_driver()
driver.get(url)
time.sleep(5)
##
click_element(driver, '//*[@id="selFILTER_ITEM0"]', "條件1")
click_element(driver, '//*[@id="tdFilterItemCat10"]', "技術指標")
click_element(driver, '//*[@id="divFilterItem"]/nobr[18]/select', "K值")
click_element(driver, '//*[@id="divFilterItem"]/nobr[18]/select/option[2]', "K值 (日)")
input_text(driver, '//*[@id="txtFILTER_VAL_S0"]', "45", "範圍45")
input_text(driver, '//*[@id="txtFILTER_VAL_E0"]', "80", "範圍80")
##
click_element(driver, '//*[@id="divMenuContent"]/form/table/tbody/tr[7]/td[1]/nobr/span', "新增條件")
click_element(driver, '//*[@id="divMenuContent"]/form/table/tbody/tr[7]/td[1]/nobr/span', "新增條件")
##
click_element(driver, '//*[@id="selFILTER_RULE0"]', "條件1")
click_element(driver, '//*[@id="tdFilterRuleCat7"]', "均線位置")
click_element(driver, '//*[@id="divFilterRule"]/nobr[30]', "成交價在均價線之下")
click_element(driver, '//*[@id="divFilterRule"]/nobr[30]/select/option[2]', "5日線")
##
click_element(driver, '//*[@id="selFILTER_RULE1"]', "條件2")
click_element(driver, '//*[@id="tdFilterRuleCat7"]', "均線位置")
click_element(driver, '//*[@id="divFilterRule"]/nobr[22]', "均價線多頭排列且走揚")
click_element(driver, '//*[@id="divFilterRule"]/nobr[22]/select/option[5]', "10日/20日")
##
click_element(driver, '//*[@id="selFILTER_RULE2"]', "條件3")
click_element(driver, '//*[@id="tdFilterRuleCat7"]', "均線位置")
click_element(driver, '//*[@id="divFilterRule"]/nobr[29]', "成交價在均價線之上")
click_element(driver, '//*[@id="divFilterRule"]/nobr[29]/select/option[5]', "20日線")
##
click_element(driver, '//*[@id="selFILTER_RULE3"]', "條件4")
click_element(driver, '//*[@id="tdFilterRuleCat1"]', "產業類別")
click_element(driver, '//*[@id="divFilterRule"]/nobr[38]/a', "ETF")
click_element(driver, '//*[@id="chkFILTER_RULE3"]', "排除條件")
##
click_element(driver, '//*[@id="selFILTER_RULE4"]', "條件5")
click_element(driver, '//*[@id="tdFilterRuleCat10"]', "MACD")
click_element(driver, '//*[@id="divFilterRule"]/nobr[1]', "日MACD落點")
click_element(driver, '//*[@id="divFilterRule"]/nobr[1]/select/option[2]', "DIF、MACD小於0")
click_element(driver, '//*[@id="chkFILTER_RULE4"]', "排除條件")
##
click_element(driver, '//*[@id="selFILTER_RULE5"]', "條件6")
click_element(driver, '//*[@id="tdFilterRuleCat1"]', "產業類別")
click_element(driver, '//*[@id="divFilterRule"]/nobr[41]/a', "ETF")
click_element(driver, '//*[@id="chkFILTER_RULE5"]', "排除條件")
##
click_element(driver, '//*[@id="selFILTER_SHEET"]', "顯示依據")
click_element(driver, '//*[@id="selFILTER_SHEET"]/option[12]', "KD指標")
click_element(driver, '//*[@id="selFILTER_SHEET2"]', "顯示依據")
click_element(driver, '//*[@id="selFILTER_SHEET2"]/option[1]', "日")
click_element(driver, '//*[@id="divMenuContent"]/form/table/tbody/tr[19]/td[2]/table/tbody/tr/td[2]/nobr/input', "查詢")
time.sleep(10)
click_element(driver, '//*[@id="tblStockList"]/tbody/tr[1]/th[14]', "KD交叉")
click_element(driver, '//*[@id="tblStockList"]/tbody/tr[1]/th[14]', "KD交叉")

##
click_element(driver, "//table[@id='tblStockList']", "Table List")
full_page_screenshot(driver, "full_page_screenshot.png")
crop_image_to_table("full_page_screenshot.png", "//table[@id='tblStockList']")

send_line_notify(f"{today_date}\n", file_path=cropped_table_screenshot)

time.sleep(10)
driver.quit()
