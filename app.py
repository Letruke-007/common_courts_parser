# import the required library
import json
from selenium.webdriver.common.by import By
from seleniumwire import webdriver
from time import sleep, time
from fake_useragent import UserAgent
import datetime
import requests


# set applicant name
applicant = str('сервисград')

# open data from .json file
with open("data.json", "r", encoding="UTF-8") as read_file:
    data = json.load(read_file)


# define the request interceptor to configure custom headers
def interceptor(request):
    # add the missing headers
    request.headers["Accept-Language"] = "en-US,en;q=0.9"
    request.headers["Referer"] = "https://www.google.com/"

    # delete the existing misconfigured default headers values
    del request.headers["User-Agent"]
    del request.headers["Sec-Ch-Ua"]
    del request.headers["Sec-Fetch-Site"]
    del request.headers["Accept-Encoding"]

    # replace the deleted headers with edited values
    request.headers[
        "User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 YaBrowser/24.7.0.0 Safari/537.36"
    request.headers["Sec-Ch-Ua"] = "\"Chromium\";v=\"122\", \"Not(A:Brand\";v=\"24\", \"Google Chrome\";v=\"122\""
    request.headers["Sec-Fetch-Site"] = "cross-site"
    request.headers["Accept-Encoding"] = "gzip, deflate, br, zstd"


# create a webdriver option
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument('ignore-certificate-errors')
chrome_options.add_argument('force-device-scale-factor=0.75')
chrome_options.add_argument('high-dpi-support=0.75')

# start a Chrome instance
driver = webdriver.Chrome(chrome_options=chrome_options)

# add the interceptor
driver.request_interceptor = interceptor

# open the target web page
base_url = "https://mos-sud.ru/"

response_data = {'status_code': [],
            'responder': [],
            'case_number': [],
            'case_status': [],
            'case_category': [],
            'link': []
            }


# set function 'scrapper'
def scrapper(data_):
    for i in range(len(data_['debtor'])):
        responder = data_['debtor'][i]
        court_number = data_['court_number'][i]
        registration_date = datetime.datetime.strptime(data_['registration_date'][i], '%d.%m.%Y').date()
        date_from = str(registration_date - datetime.timedelta(days=7)).split('-')[2] + '.' + \
                    str(registration_date - datetime.timedelta(days=7)).split('-')[1] + '.' + \
                    str(registration_date - datetime.timedelta(days=7)).split('-')[0]
        date_to = str(registration_date + datetime.timedelta(days=7)).split('-')[2] + '.' + \
                  str(registration_date + datetime.timedelta(days=7)).split('-')[1] + '.' + \
                  str(registration_date + datetime.timedelta(days=7)).split('-')[0]

        current_url = base_url + str(court_number) + '/cases/civil'

        try:
            attempt_connection = requests.get(current_url, headers={'User-Agent': UserAgent().chrome}, verify=False)
            status_code = (attempt_connection.status_code)
            response_data['status_code'].append(status_code)
            attempt_connection.close()
        except:
            print('отсутствует соединение с сервером')

        try:
            if status_code == 200:
                driver.get(current_url)
                sleep(1)
                driver.implicitly_wait(20)

                driver.find_element(by=By.LINK_TEXT, value='Расширенная форма').click()
                sleep(0.5)

                driver.find_elements(by=By.CLASS_NAME, value='input_wrap.left')[0].click()
                sleep(0.5)
                driver.find_element(by=By.ID, value='caseDateFrom').send_keys(date_from + '\t')
                sleep(0.5)

                driver.find_element(by=By.ID, value='caseDateTo').send_keys(date_to + '\t')
                sleep(0.5)

                driver.find_element(by=By.XPATH, value='//input[@type="text" and @name="participant"]').send_keys(
                    responder + '\n')
                sleep(2)

                try:
                    matches_found = int(
                        driver.find_element(by=By.CLASS_NAME, value='resultsearch_text').text.split(sep=' ')[-1])
                except:
                    response_data['link'].append('no_result')
                    response_data['case_number'].append('no_result')
                    response_data['case_status'].append('no_result')
                    response_data['case_category'].append('no_result')
                    response_data['responder'].append(responder)
                try:
                    if matches_found > 0:
                        counter = 0
                        for j in range(1, matches_found + 1):
                            counter += 1
                            el_ = str(j)
                            case_details = driver.find_element(by=By.XPATH, value='//tbody//tr[' + el_ + ']').text
                            plaintiff = \
                            driver.find_element(by=By.XPATH, value='//tbody//tr[' + el_ + ']').text.split(sep=':')[
                                1].split(sep='\n')[0]
                            case_status = case_details.split(sep='\n')[2].split(sep=' 124')[0]
                            case_category = case_details.split(sep='\n')[2].split(sep=' 124')[1].split(sep='- ')[1]

                            if applicant in plaintiff.lower():
                                current_position = driver.find_element(by=By.XPATH,
                                                                       value='//tbody//tr[' + el_ + ']''//td[1]').text
                                link = driver.find_element(by=By.XPATH,
                                                           value='//tbody//tr[' + el_ + ']''//td//a[@href]').get_attribute(
                                    'href')
                                case_number = current_position.split(sep=' ')[0]
                                response_data['link'].append(link)
                                response_data['case_number'].append(case_number)
                                response_data['case_status'].append(case_status)
                                response_data['case_category'].append(case_category)
                                response_data['responder'].append(responder)
                            else:
                                pass
                except:
                    pass
        except:
            pass

    driver.quit()


# start scrapping
scrapper(data)

with open("response.json", "w", encoding='UTF-8') as write_file:
    json.dump(response_data, write_file, indent=4, ensure_ascii=False)
