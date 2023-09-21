import json
import time
import logging

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from selenium.common.exceptions import (
    TimeoutException,
    ElementClickInterceptedException,
)


logger = logging.getLogger(__name__)


class DoctolibBrowser:
    def __init__(self, speciality: str, place: str) -> None:
        self.speciality = speciality
        self.place = place
        self.driver = self._init_driver()

        self.first_page_fetched = False

    def _init_driver(self) -> webdriver.Chrome:
        options = webdriver.ChromeOptions()
        options.add_argument("--headless=new")
        options.add_argument('--no-sandbox')
        options.add_argument("--disable-setuid-sandbox")

        # To get acces to browser logs (https://stackoverflow.com/questions/52633697/selenium-python-how-to-capture-network-traffics-response)
        options.set_capability("goog:loggingPrefs", {"performance": "ALL"})

        # Adding argument to disable the AutomationControlled flag
        options.add_argument("--disable-blink-features=AutomationControlled")

        # Exclude the collection of enable-automation switches
        options.add_experimental_option("excludeSwitches", ["enable-automation"])

        # Turn-off userAutomationExtension
        options.add_experimental_option("useAutomationExtension", False)

        driver = webdriver.Chrome(options=options)
        driver.maximize_window()

        # Changing the property of the navigator value for webdriver to undefined
        driver.execute_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )
        logger.info(f"WebDriver created ({driver.service.path})")
        return driver

    def _get_first_page(self) -> str:
        self.driver.get("https://www.doctolib.fr/")

        # Refuse cookie
        try:
            refuse_cookie_button = WebDriverWait(driver=self.driver, timeout=10).until(
                EC.presence_of_element_located((By.ID, "didomi-notice-disagree-button"))
            )
            refuse_cookie_button.click()
            logger.info(f"[{self.driver.current_url}] Cookies refused")
        except TimeoutException:
            logger.info(f"[{self.driver.current_url}] No refuse cookie button")
            pass

        # Search for speciality
        searchbar_query = WebDriverWait(driver=self.driver, timeout=10).until(
            EC.presence_of_element_located((By.ID, ":r0:"))
        )
        searchbar_query.send_keys(self.speciality)
        search_query_container = WebDriverWait(driver=self.driver, timeout=10).until(
            EC.presence_of_element_located(
                (By.ID, "search-query-input-results-container")
            )
        )
        searchbar_query_buttons = WebDriverWait(
            driver=search_query_container, timeout=10
        ).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, "searchbar-result"))
        )
        searchbar_query_button_text = searchbar_query_buttons[0].text
        logger.info(
            f"[{self.driver.current_url}] Query about to be selected ({repr(searchbar_query_button_text)})"
        )
        searchbar_query_buttons[0].click()

        # Search for place
        searchbar_place = WebDriverWait(driver=self.driver, timeout=10).until(
            EC.presence_of_element_located((By.ID, ":r1:"))
        )
        searchbar_place.send_keys(self.place)
        search_place_container = WebDriverWait(driver=self.driver, timeout=10).until(
            EC.presence_of_element_located(
                (By.ID, "search-place-input-results-container")
            )
        )
        searchbar_place_buttons = WebDriverWait(
            driver=search_place_container, timeout=10
        ).until(
            EC.presence_of_all_elements_located(((By.CLASS_NAME, "searchbar-result")))
        )
        searchbar_place_buttons_text = searchbar_place_buttons[1].text
        logger.info(
            f"[{self.driver.current_url}] Place about to be selected ({repr(searchbar_place_buttons_text)})"
        )
        searchbar_place_buttons[1].click()

        # Click on button "Rechercher"
        search_button = WebDriverWait(driver=self.driver, timeout=10).until(
            EC.presence_of_element_located(
                (By.CLASS_NAME, "searchbar-submit-button-label")
            )
        )
        logger.info(f"[{self.driver.current_url}] Search button about to be clicked")
        search_button.click()

        # Wait until page can be parsed
        WebDriverWait(driver=self.driver, timeout=10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "search-results-col-list"))
        )

        self.first_page_fetched = True
        return self.driver.page_source

    def _get_next_page(self) -> str:
        # Click on next page button
        while True:
            try:
                next_button = WebDriverWait(driver=self.driver, timeout=10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "next-link"))
                )
                logger.info(
                    f"[{self.driver.current_url}] Next page button about to be clicked"
                )
                next_button.click()
            except ElementClickInterceptedException:
                logger.warning(
                    f"[{self.driver.current_url}] Next page button unclickable"
                )
                continue
            break

        # Wait until page can be parsed
        WebDriverWait(driver=self.driver, timeout=10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "search-results-col-list"))
        )

        return self.driver.page_source

    def get_next_page(self) -> str:
        if self.first_page_fetched:
            return self._get_next_page()
        return self._get_first_page()

    def get_doctors_availabilities(self) -> dict:
        availabilities = {}
        for _ in range(5):
            browser_log = self.driver.get_log("performance")
            events = [self._process_browser_log_entry(entry) for entry in browser_log]
            response_events = [
                event
                for event in events
                if event["method"] == "Network.responseReceived"
            ]

            if len(response_events) == 0:
                break

            for event in response_events:
                url = event["params"]["response"]["url"]
                if f"https://www.doctolib.fr/search_results" in url:
                    r = self.driver.execute_cdp_cmd(
                        "Network.getResponseBody",
                        {"requestId": event["params"]["requestId"]},
                    )
                    availabilities[self._extract_doctor_id_from_url(url)] = json.loads(
                        r["body"]
                    )

            self.driver.execute_script("window.scrollTo(0,document.body.scrollHeight)")
            time.sleep(2)

        logger.info(
            f"[{self.driver.current_url}] {len(availabilities)} availabilities of doctors extracted"
        )
        return availabilities

    @staticmethod
    def _process_browser_log_entry(entry):
        response = json.loads(entry["message"])["message"]
        return response

    @staticmethod
    def _extract_doctor_id_from_url(url):
        return url.split("?")[0].split("/")[-1].split(".")[0]
