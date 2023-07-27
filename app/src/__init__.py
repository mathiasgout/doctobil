import os

from random_tools.logger.logger_tools import get_loggers


get_loggers(
    logger_names=["src"],
    stream=False,
    file_path=os.path.join(
        os.path.dirname(os.path.dirname(os.path.realpath(__file__))),
        "log/app.log",
    ),
)
