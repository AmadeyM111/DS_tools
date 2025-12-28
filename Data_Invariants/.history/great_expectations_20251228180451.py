import great_expectations as gx
import os
from pathlib import Path

# Инициализация контекста Great Expectations
context = gx.get_context()

# Расширение путей с использованием os.path.expanduser для корректной работы с ~
raw_data = os.path.expanduser("~/github-projects/Active/experimental/data/raw")
clean_data = os.path.expanduser("~/github-projects/Active/experimental/data/processed")

# Проверка существования директорий
if not os.path.exists(raw_data):
    raise FileNotFoundError(f"Директория raw_data не найдена: {raw_data}")

# Определение источника данных
# ИСПРАВЛЕНО: исправлена опечатка contxt -> context
data_source = context.data_sources.add_pandas_filesystem(
    name="my_local_datasource",
    base_directory=raw_data
)

# ИСПРАВЛЕНО: удалено дублирование создания Data Asset
# Создание Data Asset для JSON файлов
asset_name = "legal_json_asset"
data_asset = data_source.add_json_asset(name=asset_name)

# Data Asset позволяет сгруппировать данные по типу и сохранить их вместе с метаданными
# Для этого мы создаем Data Asset с именем "legal_json_asset"
# и добавляем в него данные из файла "legal_data.json"
# Это позволяет нам использовать Data Asset в качестве источника данных для проверки
# и анализа данных

# Создание и определение пакета (Batch Definition)
batch_definition = data_asset.add_batch_definition_whole_file("whole_file")

# DEFINITIONS:
# Context: Мозг системы (хранит настройки).
# Data Source: Указывает на папку с данными.
# Data Asset: Указывает на конкретный тип файла в этой папке.
# Batch: Конкретные данные, которые будут проверяться тестами.