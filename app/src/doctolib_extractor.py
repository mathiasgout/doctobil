from src.tools import basic_tools
from src.errors import UnrequestableError

import re
import os
import json
import pathlib
import logging
from typing import Optional

import requests
from bs4 import BeautifulSoup


logger = logging.getLogger(__name__)


class DoctolibExtrator:
    def __init__(
        self, speciality: str, place: str, path_folder_data: str = "data"
    ) -> None:
        self.speciality = speciality
        self.place = place
        self.path_folder_data = path_folder_data

        self._create_data_folder(path_folder_data)

    def extract_data_to_json(self) -> None:
        try:
            datas = []
            for i in range(1, 1_000_000):
                page_text = self._get_page_text(page=i)
                page_data = self._extract_data_from_page(page_text)
                datas.extend(page_data["data"])

                if page_data["end"] is True:
                    self._create_json_file(data=datas)
                    return

        except Exception as e:
            logger.error(f"{e.__class__.__name__}: {e}")

    def _get_page_text(self, page: int) -> Optional[str]:
        headers = {
            "Host": "www.doctolib.fr",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/115.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            # "Accept-Language": "fr,fr-FR;q=0.8,en-US;q=0.5,en;q=0.3",
            # "Accept-Encoding": "gzip, deflate, br",
            # "DNT": "1",
            # "Connection": "keep-alive",
            # "Upgrade-Insecure-Requests": "1",
            # "Sec-Fetch-Dest": "document",
            # "Sec-Fetch-Mode": "navigate",
            # "Sec-Fetch-Site": "none",
            # "Sec-Fetch-User": "?1",
            # "Pragma": "no-cache",
            # "Cache-Control": "no-cache",
        }

        if page == 1:
            url = f"https://www.doctolib.fr/{self.speciality}/{self.place}"
        else:
            url = f"https://www.doctolib.fr/{self.speciality}/{self.place}?page={page}"

        r_get = requests.get(url, headers=headers)
        logger.debug(f"{r_get.url} (code={r_get.status_code})")

        if r_get.ok:
            return r_get.text
        raise UnrequestableError(f"{r_get.url} (code={r_get.status_code})")

    def _extract_data_from_page(self, page_text: str) -> dict:
        soup = BeautifulSoup(page_text, "html.parser")

        data_layer = soup.find("div", attrs={"id": "datalayer"})
        js_doctor_results = soup.find("div", attrs={"class": "js-dl-doctor-results"})

        data_layer_dict = basic_tools.text_to_dict(data_layer["data-props"])
        number_exact_match = int(data_layer_dict["search_results_number_exact_match"])
        number_broad_match = int(data_layer_dict["search_results_number_broad_match"])
        speciality_id = str(data_layer_dict["speciality_id"])

        doctor_results_dict = basic_tools.text_to_dict(js_doctor_results["data-props"])
        page = str(doctor_results_dict["currentPage"])
        search_results = doctor_results_dict["searchResults"][0:number_exact_match]

        datas = []
        for result in search_results:
            data = {"page": page}
            data["id"] = str(result["id"])
            data["url"] = result["profile_path"]
            data["full_name"] = result["name_with_title"]
            data["total_availabilities"] = self._extract_availabilities(
                data["id"], speciality_id
            )
            datas.append(data)

        logger.debug(f"page: {page} scraped")
        if number_broad_match > 0:
            return {"data": datas, "end": True}
        return {"data": datas, "end": False}

    @staticmethod
    def _extract_availabilities(doctor_id: str, speciality_id: str) -> Optional[int]:
        headers = {
            "Host": "www.doctolib.fr",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/115.0",
        }

        r_get = requests.get(
            f"https://www.doctolib.fr/search_results/{doctor_id}.json?limit=7&speciality_id={speciality_id}",
            headers=headers,
        )
        logger.debug(f"{r_get.url} (code={r_get.status_code})")

        if r_get.ok:
            try:
                json_value = r_get.json()
                total_availabilities = json_value["total"]
            except Exception as e:
                logger.warning(f"{e.__class__.__name__}: {e}")
                total_availabilities = None
        else:
            total_availabilities = None

        return total_availabilities

    def _create_json_file(self, data: list) -> None:
        speciality_cleaned = re.sub("[^A-Za-z0-9]+", "", str(self.speciality).upper())
        place_cleaned = re.sub("[^A-Za-z0-9]+", "", str(self.place).upper())

        file_path = os.path.join(
            self.path_folder_data,
            f"data_{speciality_cleaned}_{place_cleaned}_{basic_tools.get_timestamp_utc()}.json",
        )
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
            logger.info(f"{file_path} created")

    @staticmethod
    def _create_data_folder(path_folder: str) -> None:
        pathlib.Path(path_folder).mkdir(parents=True, exist_ok=True)
