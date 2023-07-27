from src.tools import basic_tools

import os
import re
import json
import time
import pathlib
import logging
from typing import Optional

import requests
from random_tools.error.error_tools import exception
from bs4 import BeautifulSoup
from unidecode import unidecode
from selenium import webdriver
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.common.exceptions import TimeoutException, ElementNotInteractableException


logger = logging.getLogger(__name__)


class DoctolibScraper:
    def __init__(
        self,
        speciality: str,
        place: str,
        firefox_driver_path: str = "geckodriver",
        headless: bool = True,
        path_folder_data: str = "data",
    ) -> None:
        self.speciality = speciality
        self.place = place
        self.firefox_driver_path = firefox_driver_path
        self.headless = headless
        self.path_folder_data = path_folder_data

        self._create_data_folder()

        self.driver = self._init_driver()
        self.speciality_id = None

    def extract_data_to_json(self) -> None:
        try:
            datas = []
            for i in range(1, 1_000_000):
                if i == 1:
                    page_data = self._extract_data_from_page(
                        self._get_first_page(), page=1
                    )
                    datas.extend(page_data["data"])
                else:
                    page_data = self._extract_data_from_page(
                        self._get_next_page(), page=i
                    )
                    datas.extend(page_data["data"])

                if page_data["end"] is True:
                    self.driver.close()
                    self._create_json_file(data=datas)
                    return

        except Exception as e:
            logger.error(f"{e.__class__.__name__}: {e}")

    @exception(logger)
    def _init_driver(self) -> webdriver.firefox.webdriver.WebDriver:
        options = webdriver.FirefoxOptions()
        if self.headless:
            options.add_argument("-headless")

        service = FirefoxService(
            executable_path=self.firefox_driver_path, log_path=os.path.devnull
        )

        driver = webdriver.Firefox(options=options, service=service)
        return driver

    def _get_first_page(self) -> str:
        self.driver.get("https://www.doctolib.fr/")
        logger.debug(f"{self.driver.current_url} browsed")

        # Refuse cookie
        try:
            refuse_cookie_button = WebDriverWait(driver=self.driver, timeout=10).until(
                expected_conditions.presence_of_element_located(
                    (By.ID, "didomi-notice-disagree-button")
                )
            )
            refuse_cookie_button.click()
            logger.debug("cookie refused")
        except TimeoutException as e:
            logger.debug("no refuse cookie button")

        # Search for self.speciality
        searchbar_query = WebDriverWait(driver=self.driver, timeout=10).until(
            expected_conditions.presence_of_element_located((By.ID, ":r0:"))
        )
        searchbar_query.send_keys(self.speciality)

        search_query_container = WebDriverWait(driver=self.driver, timeout=10).until(
            expected_conditions.presence_of_element_located(
                (By.ID, "search-query-input-results-container")
            )
        )
        searchbar_query_buttons = WebDriverWait(
            driver=search_query_container, timeout=10
        ).until(
            expected_conditions.presence_of_all_elements_located(
                (By.CLASS_NAME, "searchbar-result")
            )
        )
        self.speciality_id = self._extract_speciality_id(searchbar_query_buttons[0])
        searchbar_query_buttons[0].click()

        # Search for self.place
        searchbar_place = WebDriverWait(driver=self.driver, timeout=10).until(
            expected_conditions.presence_of_element_located((By.ID, ":r1:"))
        )
        searchbar_place.send_keys(self.place)

        search_place_container = WebDriverWait(driver=self.driver, timeout=10).until(
            expected_conditions.presence_of_element_located(
                (By.ID, "search-place-input-results-container")
            )
        )

        searchbar_place_buttons = WebDriverWait(
            driver=search_place_container, timeout=10
        ).until(
            expected_conditions.presence_of_all_elements_located(
                ((By.CLASS_NAME, "searchbar-result"))
            )
        )
        searchbar_place_buttons[1].click()

        # Click on button "Rechercher"
        search_button = WebDriverWait(driver=self.driver, timeout=10).until(
            expected_conditions.presence_of_element_located(
                (By.CLASS_NAME, "searchbar-submit-button-label")
            )
        )
        search_button.click()

        # Wait until page can be parsed
        WebDriverWait(driver=self.driver, timeout=10).until(
            expected_conditions.presence_of_element_located(
                (By.CLASS_NAME, "search-results-col-list")
            )
        )
        logger.debug(f"{self.driver.current_url} browsed")
        return self.driver.page_source

    def _get_next_page(self) -> str:
        while True:
            try:
                # Scroll to the bottom of the page
                self.driver.execute_script(
                    "window.scrollTo(0, document.body.scrollHeight);"
                )
                time.sleep(0.5)  # Need to wait to reach the end of the page
                next_button_button = WebDriverWait(
                    driver=self.driver, timeout=10
                ).until(
                    expected_conditions.presence_of_element_located(
                        (By.CLASS_NAME, "next-link")
                    )
                )
                next_button_button.click()
            except ElementNotInteractableException as e:
                logger.warning(f"{e.__class__.__name__}: {e}")
                continue
            break

        # Wait until page can be parsed
        WebDriverWait(driver=self.driver, timeout=10).until(
            expected_conditions.presence_of_element_located(
                (By.CLASS_NAME, "search-results-col-list")
            )
        )
        logger.debug(f"{self.driver.current_url} browsed")
        return self.driver.page_source

    def _extract_data_from_page(self, page_txt: str, page: int) -> dict:
        soup = BeautifulSoup(page_txt, "html.parser")
        results = soup.find("div", attrs={"class": "search-results-col-list"})

        datas = []
        for result in results.contents:
            class_value = result.get("class")
            if class_value[0] != "dl-search-result":
                if class_value[0] == "pb-16":
                    if result.find("h2") is not None:
                        logger.debug("page scraped")
                        return {"data": datas, "end": True}
                continue

            data = {"page": page}
            data["id"] = result.get("id").split("-")[-1]

            div_search_result = result.find("div", {"class": "dl-search-result-title"})
            a_tag = div_search_result.find("a")

            data["url"] = a_tag["href"]
            data["full_name"] = a_tag.text
            data["total_availabilities"] = self._extract_availabilities(
                data["id"], self.speciality_id
            )
            datas.append(data)

        logger.debug("page scraped")
        return {"data": datas, "end": False}

    def _extract_speciality_id(
        self, speciality_web_element: webdriver.remote.webelement.WebElement
    ) -> str:
        try:
            value_id = speciality_web_element.get_attribute("id")
            speciality_id = value_id.split("-")[0]
            logger.debug("speciality ID extracted")
        except Exception as e:
            speciality_id = None
            logger.warning(f"{e.__class__.__name__}: {e}")

        return speciality_id

    @staticmethod
    def _extract_availabilities(doctor_id: str, speciality_id: str) -> Optional[int]:
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/115.0"
        }
        r_get = requests.get(
            f"https://www.doctolib.fr/search_results/{doctor_id}.json?limit=7&speciality_id={speciality_id}",
            headers=headers,
        )
        if r_get.ok:
            json_value = r_get.json()
            total_availabilities = json_value["total"]
        else:
            logger.warning(f"{r_get.url} (code={r_get.status_code})")
            total_availabilities = None

        return total_availabilities

    def _create_json_file(self, data: list) -> None:
        speciality_cleaned = re.sub(
            "[^A-Za-z0-9]+", "", unidecode(str(self.speciality)).upper()
        )
        place_cleaned = re.sub("[^A-Za-z0-9]+", "", unidecode(str(self.place)).upper())

        file_path = os.path.join(
            self.path_folder_data,
            f"data_{speciality_cleaned}_{place_cleaned}_{basic_tools.get_timestamp_utc()}.json",
        )
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
            logger.info(f"{file_path} created")

    def _create_data_folder(self) -> None:
        pathlib.Path(self.path_folder_data).mkdir(parents=True, exist_ok=True)
