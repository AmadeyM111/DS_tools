import pandas as pd


def json_to_csv(input_file, output_file):
    try:
        # Прочитайте JSON файл в DataFrame
        df = pd.read_json(input_file)
        
        # Сохраните DataFrame в CSV файл с кодировкой UTF-8
        df.to_csv(output_file, index=False, encoding='utf-8')
        print(f"JSON файл успешно преобразован в CSV и сохранен как {output_file}")
    except Exception as e:
        print(f"Произошла ошибка при преобразовании: {e}")

        
# Пример использования функции
json_to_csv('input.json', 'output.csv')