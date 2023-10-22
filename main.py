import time
import selenium
import json

from pyvirtualdisplay import Display  # --> only for Linux
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By


class TeslaScrap:
    def __init__(self):
        self.browser = None
        self.main_url = "https://www.tesla.com/de_DE/inventory/new/ms?arrangeby=plh&zip=10115&range=50"
        self.chromedriver_path = "/usr/local/bin/chromedriver"
        self.car_list = []

        return

    # -- create Selenium browser instance --
    def create_browser_instance(self, maximize: bool) -> None:
        """
        Function to create a Selenium global instance
        :param maximize: bool
        :return:
        """
        # -- uncomment this to hide the display of selenium browser ONLY FOR LINUX --
        # display = Display(visible=False, size=(800, 600))
        # display.start()

        # -- create chrome webdriver for selenium --
        options = webdriver.ChromeOptions()
        service = ChromeService(executable_path=self.chromedriver_path)
        self.browser = webdriver.Chrome(service=service, options=options)
        if maximize:
            self.browser.maximize_window()

        return

    # -- get car leasing prices --
    def get_car_leasings(self) -> list:
        """
        Function to get car leasing prices

        :return:
        """
        leasings = []

        # -- access leasing prices layer --
        lease_button = self.browser.find_element(By.CLASS_NAME, "modal-trigger.tds-icon-trigger")
        lease_button.click()
        time.sleep(1)
        private_leasing = self.browser.find_element(By.ID, "lease.lease_private")
        private_leasing.click()
        time.sleep(1)

        # -- loop to get leasing prices --
        terms = ['24', '36', '48']
        distances = ['10000', '15000', '20000']
        for term in range(0, len(terms)):
            term_dropdown = self.browser.find_element(By.ID, "term")
            term_opt = term_dropdown.find_elements(By.TAG_NAME, "option")[term]
            term_opt.click()
            time.sleep(1)
            for distance in range(0, len(distances)):
                dst_dropdown = self.browser.find_element(By.ID, "distance")
                dst_opt = dst_dropdown.find_elements(By.TAG_NAME, "option")[distance]
                dst_opt.click()
                time.sleep(1)

                if term <= 2 and distance <= 2:
                    l_price = self.browser.find_element(By.CLASS_NAME, "tds-o-fin-header.line-item--value")
                    lease_price = l_price.text

                    leasing_line = {
                        'term': terms[term],
                        'distance': distances[distance],
                        'price': lease_price
                    }
                    leasings.append(leasing_line)
                    print(leasings[-1])

        return leasings

    # -- get car details --
    def get_car_details(self, car_url: str) -> dict:
        """
        Function to get car details like range, max_speed and color

        :param car_url:
        :return:
        """
        print("--> Getting " + car_url + "...")
        self.browser.get(car_url)
        time.sleep(1)

        # -- get car details --
        details = []
        for side_block in self.browser.find_elements(By.CLASS_NAME, "aside-section.side-scroll--item"):
            for item in side_block.find_elements(By.CLASS_NAME, "tds-list-item"):
                details.append(item.text)
        km_range = details[0].split("km")
        max_speed = details[1].split("km")
        color = details[4]

        final_details = {'range': km_range[0],
                         'max_speed': max_speed[0],
                         'color': color,
                         'leasings': self.get_car_leasings()
                         }

        return final_details

    def scrap_main_page(self) -> list:
        """
        Function to get main cars page, details and call function to get car details

        :return: dict
        """
        self.create_browser_instance(True)

        # -- download main URL --
        print("--> Getting "+self.main_url+"...")
        self.browser.get(self.main_url)
        time.sleep(1)

        # -- close international layer, if any --
        try:
            close_elem = self.browser.find_element(By.CLASS_NAME, "tds-modal-close.tds-icon-btn.tds-icon-btn--medium")
            close_elem.click()
            time.sleep(1)
        except selenium.common.exceptions.NoSuchElementException:
            close_elem = (self.browser.
                          find_element(By.CLASS_NAME,
                                       "tds-link.tds-link--secondary.tds-locale-selector-language.tds-lang--de"))
        close_elem.click()
        time.sleep(1)

        # -- scroll down page to make most of the elements visible --
        self.browser.execute_script("window.scrollTo(3000,document.body.scrollHeight);")
        self.browser.execute_script("window.scrollTo(0, 220)")
        time.sleep(1)

        # -- get car list --
        for article in self.browser.find_elements(By.CLASS_NAME, "result.card"):
            # -- get price --
            price_elem = article.find_element(By.CLASS_NAME, "result-purchase-price.tds-text--h4").text
            car_price = price_elem

            # -- get product URL --
            data_id = article.get_attribute("data-id")
            tmp = data_id.split("-")
            car_url = "https://www.tesla.com/de_DE/ms/order/5YJS" + tmp[0]
            print("CAR URL:")
            print(car_url)

            car_list = {
                'price': car_price,
                'url': car_url,
                'range': '',
                'max_speed': '',
                'color': '',
                'leasings': []
            }
            self.car_list.append(car_list)

        for car in range(0, len(self.car_list)):
            car_details = self.get_car_details(self.car_list[car]['url'])
            for key in car_details.keys():
                self.car_list[car][key] = car_details[key]

        print("Got a list with "+str(len(self.car_list))+" cars!")

        # -- save JSON result to file --
        content = json.dumps(self.car_list)
        with open("result.json", "w") as fp:
            fp.write(content)
            fp.close()

        return self.car_list


if __name__ == "__main__":
    ts = TeslaScrap()
    car_list = ts.scrap_main_page()
