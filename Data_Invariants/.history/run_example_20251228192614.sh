#!/bin/bash
# Пример скрипта для запуска с переменными окружения

# Установка переменных окружения
# ВАЖНО: Укажите правильный путь к директории с данными!
# Примеры:
# export GE_RAW_DATA_PATH=../data/raw          # относительный путь
# export GE_RAW_DATA_PATH=/absolute/path/to/data/raw  # абсолютный путь
export GE_RAW_DATA_PATH=../data/raw
export GE_CLEAN_DATA_PATH=../data/processed
export GE_DATA_SOURCE_NAME=my_local_datasource
export GE_ASSET_NAME=legal_json_asset
export GE_FILE_PATTERN=**/*.json

# Запуск скрипта
python setup_ge.py

