from src import doctolib_scraper

import time
import json

import schedule


if __name__ == "__main__":
    # 'config.json' file must contains "speciality" and "place" fields
    with open("config.json", "r") as f:
        config = json.load(f)

    def job():
        scraper = doctolib_scraper.DoctolibScraper(
            speciality=config["speciality"],
            place=config["place"],
            headless=True,
            path_folder_data="data",
        )
        scraper.extract_data_to_json()

    schedule.every().hour.at(":45").do(job)
    schedule.every().hour.at(":15").do(job)

    while True:
        schedule.run_pending()
        time.sleep(1)
