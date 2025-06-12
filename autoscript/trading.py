import time
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup

url = "https://fund.cnyes.com/Fixedincome/search.aspx"
token = "B1lCc5KlmAXCcIDRfiXp3koB4GyhIcOe3KKUqVDt8uL"


def print_fund_data(data):
    data = f"\n基金名稱: {data[0]}\n" \
           f"淨值/日期: {data[1][0:7]} / {data[1][7:]}\n" \
           f"績效: {data[2]}\n" \
           f"基準日/配息日: {data[3][0:10]} - {data[3][10:]}\n" \
           f"配息金額/年化配息率: {data[4][0:6]} / {data[4][6:]}\n" \
           f"評比: {data[5]}"
    return data


def lineNotifyMessage(token, msg):
    headers = {
        "Authorization": "Bearer " + token,
        "Content-Type": "application/x-www-form-urlencoded"
    }

    payload = {"message": msg}
    r = requests.post("https://notify-api.line.me/api/notify", headers=headers, params=payload)
    return r.status_code


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
driver = webdriver.Chrome(options=chrome_options)
driver.get(url=url)

driver.find_element(by="id", value="ctl00_ContentPlaceHolder1_DropDownList1").click()
driver.find_element(by="xpath", value='//*[@id="ctl00_ContentPlaceHolder1_DropDownList1"]/option[8]').click()
driver.find_element(by="id", value="ctl00_ContentPlaceHolder1_DropDownList2").click()
driver.find_element(by="xpath", value='//*[@id="ctl00_ContentPlaceHolder1_DropDownList2"]/option[8]').click()
driver.find_element(by="xpath", value='//*[@id="aspnetForm"]/div[4]/div[1]/select[1]').click()
driver.find_element(by="xpath", value='//*[@id="aspnetForm"]/div[4]/div[1]/select[1]/option[9]').click()
driver.find_element(by="xpath", value='//*[@id="aspnetForm"]/div[4]/div[1]/select[2]').click()
driver.find_element(by="xpath", value='//*[@id="aspnetForm"]/div[4]/div[1]/select[2]/option[3]').click()
driver.find_element(by="id", value="div_type").click()
driver.find_element(by="xpath", value='//*[@id="div_type"]/option[4]').click()
driver.find_element(by="xpath", value='//*[@id="aspnetForm"]/div[4]/div[3]/button').click()
time.sleep(5)

driver.find_element(by="xpath", value='/html/body/div[2]/section[3]/div/div[4]/table[2]/thead/tr/th[3]/select').click()
driver.find_element(by="xpath",
                    value='/html/body/div[2]/section[3]/div/div[4]/table[2]/thead/tr/th[3]/select/option[6]').click()

time.sleep(5)
page_source = driver.page_source

soup = BeautifulSoup(page_source, "html.parser")
target_element = soup.select_one(
    "html body div:nth-of-type(2) section:nth-of-type(3) div div:nth-of-type(4) table:nth-of-type(2) tbody")

table_rows = target_element.find_all("tr")

for row in table_rows:
    row_data = [cell.get_text(strip=True) for cell in row.find_all("td")]
    print(print_fund_data(row_data))
    # lineNotifyMessage(token, msg=print_fund_data(row_data))

driver.quit()
