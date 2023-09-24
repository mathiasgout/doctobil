from typing import Optional

from doctobil.browser import DoctolibBrowser
from doctobil.extractor import DoctolibExtractor


class Doctobil:
    def __init__(
        self, speciality: str, place: str, remote_address: Optional[str] = None
    ) -> None:
        self.speciality = speciality
        self.place = place
        self.doctolib_browser = DoctolibBrowser(
            speciality=speciality, place=place, remote_address=remote_address
        )
        self.doctolib_extractor = DoctolibExtractor()

    def extract_data(self) -> dict:
        datas = []

        for page in range(1, 1_000_000):
            page_source = self.doctolib_browser.get_next_page()
            page_data = self.doctolib_extractor.extract_partial_data_from_page(
                page_source=page_source
            )
            doctors_availabilities = self.doctolib_browser.get_doctors_availabilities()
            for partial_data in page_data["data"]:
                data = {}

                data["page"] = page
                data["id"] = partial_data["id"]
                data["url"] = partial_data["url"]
                data["full_name"] = partial_data["full_name"]
                data["total_availabilities"] = doctors_availabilities.get(
                    data["id"], {}
                ).get("total")
                datas.append(data)

            if page_data["end"]:
                return datas

        return datas
