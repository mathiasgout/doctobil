from src import doctolib_extractor

import time
import json


if __name__ == "__main__":
    # 'config.json' file must contains "speciality", "place" and "time_to_wait" fields
    with open("config.json", "r") as f:
        config = json.load(f)

    while True:
        extractor = doctolib_extractor.DoctolibExtrator(
            speciality=config["speciality"], place=config["place"]
        )
        extractor.extract_data_to_json()

        time.sleep(config["time_to_wait"])
