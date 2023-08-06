from src import doctolib_extractor

import time
import json
import logging


if __name__ == "__main__":
    logger = logging.getLogger(__name__)

    # 'config.json' file must contains "speciality", "place" and "time_to_wait" fields
    with open("config.json", "r") as f:
        config = json.load(f)

    while True:
        logger.info("Extraction started")
        extractor = doctolib_extractor.DoctolibExtrator(
            speciality=config["speciality"], place=config["place"]
        )
        extractor.extract_data_to_json()

        logger.info(f"Extraction ended (wait={config['time_to_wait']})")
        time.sleep(config["time_to_wait"])
