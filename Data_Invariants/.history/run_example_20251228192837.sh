#!/bin/bash
# Пример скрипта для запуска с переменными окружения

# Установка переменных окружения
# Пути к данным: Active/experimental/data/
# Если переменные не заданы, используются пути по умолчанию из кода
# Можно раскомментировать для переопределения:
# export GE_RAW_DATA_PATH=../experimental/data/raw
# export GE_CLEAN_DATA_PATH=../experimental/data/processed
export GE_DATA_SOURCE_NAME=my_local_datasource
export GE_ASSET_NAME=legal_json_asset
export GE_FILE_PATTERN=**/*.json

# Запуск скрипта
python setup_ge.py

