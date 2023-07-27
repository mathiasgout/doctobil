#!/bin/bash

FOLDER_PATH=/home/mathias/doctobil

/usr/bin/docker compose -f ${FOLDER_PATH}/docker-compose.prod.yml down
/usr/bin/docker compose -f ${FOLDER_PATH}/docker-compose.prod.yml up --build -d
