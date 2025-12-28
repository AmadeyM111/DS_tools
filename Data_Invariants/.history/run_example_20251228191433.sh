#!/bin/bash
# Пример скрипта для запуска с переменными окружения

# Установка переменных окружения
export GE_RAW_DATA_PATH=.
export GE_CLEAN_DATA_PATH=../data/processed
export GE_DATA_SOURCE_NAME=my_local_datasource
export GE_ASSET_NAME=legal_json_asset

# Запуск скрипта
python setup_ge.py

