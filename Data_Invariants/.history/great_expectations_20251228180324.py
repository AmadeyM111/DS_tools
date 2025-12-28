import great_expectations as gx

context = gx.get_context()

raw_data = "~/github-projects/Active/experimental/data/raw"
clean_data = "~/github-projects/Active/experimental/data/processed"

# Define the data source
"""
sft_datasets = context.sources.pandas_default.read_csv(
    file_path=os.path.join(raw_data, "sft_datasets.csv")
)
"""

data_source = contxt.data_sources.add_pandas_filesystem(
    name = "my_local_datasource",
    base_directory = raw_data
)

law_data_asset = "legal_json_asset"
data_asset = data_source.add_json_asset(name=law_data_asset)

# Data Asset позволяет сгруппировать данные по типу и сохранить их вместе с метаданными
# Для этого мы создаем Data Asset с именем "legal_json_asset"
# и добавляем в него данные из файла "legal_data.json"
# Это позволяет нам использовать Data Asset в качестве источника данных для проверки
# и анализа данных

# Регистрируем Data Asset в контексте - мы можем использовать Data Asset для проверки и анализа данных
# Например, мы можем использовать Data Asset для проверки данных на валидность
# или для анализа данных

asset_name = "legal_json_asset"
data_asset = data_source.add_json_asset(name=asset_name)

# Создание и определение пакета (Batch Definition)
batch_definition = data_asset.add_batch_definition_whole_file("whole_file")

# DEFINITIONS:
# Context: Мозг системы (хранит настройки).
# Data Source: Указывает на папку с данными.
​# Data Asset: Указывает на конкретный тип файла в этой папке.
​# Batch: Конкретные данные, которые будут проверяться тестами.