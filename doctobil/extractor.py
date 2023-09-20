import logging

import bs4
from bs4 import BeautifulSoup


logger = logging.getLogger(__name__)


class DoctolibExtractor:
    def __init__(self) -> None:
        self.last_page = False

    def extract_partial_data_from_page(self, page_source: str) -> dict:
        soup = BeautifulSoup(page_source, "html.parser")
        results_raw = soup.find("div", attrs={"class": "search-results-col-list"})
        results = self._extract_page_results(results_raw=results_raw)

        datas = []
        for result in results:
            data = {}
            data["id"] = result.get("id").split("-")[-1]

            div_search_result = result.find("div", {"class": "dl-search-result-title"})
            a_tag = div_search_result.find("a")

            data["url"] = a_tag["href"]
            data["full_name"] = a_tag.text
            datas.append(data)

        return {"data": datas, "end": self.last_page}

    def _extract_page_results(
        self, results_raw: list[bs4.element.Tag]
    ) -> list[bs4.element.Tag]:
        results = []
        for result_raw in results_raw:
            class_value = result_raw.get("class")
            if class_value[0] == "dl-search-result":
                results.append(result_raw)
            else:
                if (class_value[0] == "pb-16") and (result_raw.find("h2") is not None):
                    self.last_page = True
                    break

        logger.info(
            f"{len(results)} information about doctors extracted (last_page={self.last_page})"
        )
        return results
