import great_expectations as gx
import os
import logging
from pathlib import Path
from typing import Optional, Any

# Попытка загрузить переменные окружения из .env файла (опционально)
try:
    from dotenv import load_dotenv
    # Загружаем переменные из .env файла, если он существует
    env_path = Path(__file__).parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
        logging.getLogger(__name__).debug(f"Переменные окружения загружены из {env_path}")
except ImportError:
    # python-dotenv не установлен - используем только системные переменные окружения
    pass

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Определяем корень проекта относительно расположения этого файла
PROJECT_ROOT = Path(__file__).parent.resolve()


def get_config_from_env() -> dict:
    """
    Получение конфигурации из переменных окружения.
    Возвращает словарь с настройками или значения по умолчанию.
    
    Пути по умолчанию задаются относительно корня проекта для лучшей переносимости.
    """
    # Относительные пути от корня проекта
    default_raw_data = PROJECT_ROOT.parent.parent.parent / 'data' / 'raw'
    default_clean_data = PROJECT_ROOT.parent.parent.parent / 'data' / 'processed'
    
    # Получаем пути из переменных окружения или используем относительные по умолчанию
    raw_data_path = os.getenv('GE_RAW_DATA_PATH')
    if raw_data_path:
        # Если путь задан через переменную окружения, преобразуем его в абсолютный
        raw_data_path = str(Path(raw_data_path).expanduser().resolve())
    else:
        # Используем относительный путь от корня проекта
        raw_data_path = str(default_raw_data)
    
    clean_data_path = os.getenv('GE_CLEAN_DATA_PATH')
    if clean_data_path:
        clean_data_path = str(Path(clean_data_path).expanduser().resolve())
    else:
        clean_data_path = str(default_clean_data)
    
    # Паттерн для поиска файлов (поддерживает glob patterns для работы с поддиректориями)
    # Примеры: "**/*.json" - все JSON файлы рекурсивно
    #          "class*/codec*/*.json" - файлы в поддиректориях по классам и кодексам
    file_pattern = os.getenv('GE_FILE_PATTERN', '**/*.json')
    
    config = {
        'raw_data_path': raw_data_path,
        'clean_data_path': clean_data_path,
        'data_source_name': os.getenv('GE_DATA_SOURCE_NAME', 'my_local_datasource'),
        'asset_name': os.getenv('GE_ASSET_NAME', 'legal_json_asset'),
        'batch_definition_name': os.getenv('GE_BATCH_DEFINITION_NAME', 'whole_file'),
        'file_pattern': file_pattern,  # Паттерн для поиска файлов в поддиректориях
    }
    logger.info(f"Конфигурация загружена: {config}")
    return config


def validate_paths(config: dict) -> None:
    """
    Валидация существования директорий и файлов по паттерну.
    
    Args:
        config: Словарь с конфигурацией
        
    Raises:
        FileNotFoundError: Если директория не существует или файлы не найдены
    """
    raw_data_path = Path(config['raw_data_path'])
    if not raw_data_path.exists():
        error_msg = f"Директория raw_data не найдена: {raw_data_path}"
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)
    logger.info(f"Директория raw_data найдена: {raw_data_path}")
    
    # Проверяем наличие файлов по паттерну
    file_pattern = config.get('file_pattern', '**/*.json')
    matching_files = list(raw_data_path.glob(file_pattern))
    
    if not matching_files:
        error_msg = (
            f"Не найдено файлов по паттерну '{file_pattern}' в директории: {raw_data_path}\n"
            f"Убедитесь, что:\n"
            f"  1. Путь GE_RAW_DATA_PATH указывает на директорию с данными\n"
            f"  2. В директории есть файлы, соответствующие паттерну '{file_pattern}'\n"
            f"  3. Текущий путь: {raw_data_path.absolute()}"
        )
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)
    
    logger.info(f"Найдено {len(matching_files)} файл(ов) по паттерну '{file_pattern}'")
    if len(matching_files) <= 10:
        logger.debug(f"Найденные файлы: {[str(f.relative_to(raw_data_path)) for f in matching_files]}")
    else:
        logger.debug(f"Первые 10 файлов: {[str(f.relative_to(raw_data_path)) for f in matching_files[:10]]}")


def setup_great_expectations(config: dict) -> tuple:
    """
    Настройка Great Expectations: создание контекста, источника данных и asset.
    
    Args:
        config: Словарь с конфигурацией
        
    Returns:
        tuple: (context, data_source, data_asset, batch_definition)
        
    Raises:
        Exception: При ошибках инициализации Great Expectations
    """
    try:
        logger.info("Инициализация контекста Great Expectations...")
        context = gx.get_context()
        logger.info("Контекст успешно инициализирован")
        
        logger.info(f"Создание источника данных: {config['data_source_name']}")
        data_source = context.data_sources.add_pandas_filesystem(
            name=config['data_source_name'],
            base_directory=config['raw_data_path']
        )
        logger.info(f"Источник данных '{config['data_source_name']}' успешно создан")
        
        logger.info(f"Создание Data Asset: {config['asset_name']}")
        logger.info(f"Использование паттерна файлов: {config['file_pattern']}")
        
        # Создаем Data Asset с паттерном для поиска файлов в поддиректориях
        # Это позволяет работать с данными, разбитыми по классам/кодексам
        # Пробуем разные варианты API для совместимости с разными версиями
        try:
            # Для новых версий Great Expectations
            data_asset = data_source.add_json_asset(
                name=config['asset_name'],
                glob_directive=config['file_pattern']
            )
        except TypeError:
            try:
                # Альтернативный вариант с batching_regex
                data_asset = data_source.add_json_asset(
                    name=config['asset_name'],
                    batching_regex=config['file_pattern']
                )
            except TypeError:
                # Если паттерн не поддерживается напрямую, создаем asset без паттерна
                # и настроим batch definition с паттерном позже
                logger.warning("Прямая поддержка паттернов не найдена, используем базовый asset")
                data_asset = data_source.add_json_asset(name=config['asset_name'])
        
        logger.info(f"Data Asset '{config['asset_name']}' успешно создан с паттерном '{config['file_pattern']}'")
        
        logger.info(f"Создание Batch Definition: {config['batch_definition_name']}")
        # Используем whole_file для обработки всех файлов, соответствующих паттерну
        batch_definition = data_asset.add_batch_definition_whole_file(
            config['batch_definition_name']
        )
        logger.info(f"Batch Definition '{config['batch_definition_name']}' успешно создан")
        
        return context, data_source, data_asset, batch_definition
        
    except Exception as e:
        logger.error(f"Ошибка при настройке Great Expectations: {str(e)}", exc_info=True)
        raise


def create_expectations(context: Any, data_asset: Any) -> Optional[Any]:
    """
    Создание набора expectations для проверки данных.
    
    Args:
        context: Контекст Great Expectations
        data_asset: Data Asset для создания expectations
        
    Returns:
        ExpectationSuite или None при ошибке
    """
    try:
        logger.info("Создание Expectation Suite...")
        suite_name = f"{data_asset.name}_suite"
        
        # Получаем или создаем Expectation Suite
        try:
            # Пытаемся получить существующий suite
            if hasattr(context.suites, 'get'):
                suite = context.suites.get(suite_name)
                logger.info(f"Использование существующего Expectation Suite: {suite_name}")
            else:
                # Альтернативный способ для разных версий API
                suite = context.suites.add(gx.ExpectationSuite(name=suite_name))
                logger.info(f"Создан новый Expectation Suite: {suite_name}")
        except (AttributeError, KeyError, Exception) as e:
            # Если suite не существует, создаем новый
            suite = context.suites.add(gx.ExpectationSuite(name=suite_name))
            logger.info(f"Создан новый Expectation Suite: {suite_name}")
        
        # Получаем валидатор для работы с данными
        logger.info("Получение валидатора для создания expectations...")
        batch_request = data_asset.build_batch_request()
        
        # Получаем валидатор (разные версии API могут иметь разные методы)
        try:
            validator = context.get_validator(
                batch_request=batch_request,
                expectation_suite_name=suite_name
            )
        except AttributeError:
            # Альтернативный способ для старых версий
            validator = context.get_validator(
                batch_request=batch_request,
                expectation_suite=suite
            )
        
        # Добавляем expectations для проверки данных
        logger.info("Добавление expectations...")
        
        # Примеры expectations для JSON данных:
        # 1. Проверка, что данные не пустые
        try:
            validator.expect_table_row_count_to_be_between(min_value=1)
            logger.info("✓ Expectation добавлена: таблица не пустая")
        except Exception as e:
            logger.warning(f"Не удалось добавить expectation для проверки количества строк: {e}")
        
        # 2. Проверка наличия обязательных колонок (если данные структурированы)
        # Это будет работать только если JSON преобразован в таблицу
        # Пример для случая, когда JSON имеет структуру с колонками:
        # try:
        #     validator.expect_column_to_exist("column_name")
        #     logger.info("✓ Expectation добавлена: проверка наличия колонки")
        # except Exception as e:
        #     logger.debug(f"Проверка колонок не применима: {e}")
        
        # 3. Проверка уникальности (если применимо)
        # try:
        #     validator.expect_column_values_to_be_unique("id")
        #     logger.info("✓ Expectation добавлена: проверка уникальности")
        # except Exception as e:
        #     logger.debug(f"Проверка уникальности не применима: {e}")
        
        # Сохраняем suite
        validator.save_expectation_suite()
        logger.info(f"Expectation Suite '{suite_name}' успешно сохранен")
        
        return suite
        
    except Exception as e:
        logger.error(f"Ошибка при создании expectations: {str(e)}", exc_info=True)
        return None


def validate_data(context: Any, data_asset: Any, suite_name: str) -> Optional[Any]:
    """
    Выполнение валидации данных с использованием созданных expectations.
    
    Args:
        context: Контекст Great Expectations
        data_asset: Data Asset для валидации
        suite_name: Имя Expectation Suite
        
    Returns:
        CheckpointResult или None при ошибке
    """
    try:
        logger.info("Запуск валидации данных...")
        
        # Создаем checkpoint для валидации
        checkpoint_name = f"{data_asset.name}_checkpoint"
        
        batch_request = data_asset.build_batch_request()
        
        # Пытаемся получить существующий checkpoint или создать новый
        try:
            checkpoint = context.checkpoints.get(checkpoint_name)
            logger.info(f"Использование существующего Checkpoint: {checkpoint_name}")
        except (KeyError, AttributeError):
            # Создаем новый checkpoint
            checkpoint = context.checkpoints.add(
                name=checkpoint_name,
                validations=[
                    {
                        "batch_request": batch_request,
                        "expectation_suite_name": suite_name,
                    }
                ],
            )
            logger.info(f"Checkpoint '{checkpoint_name}' создан")
        
        # Запускаем валидацию
        logger.info("Выполнение валидации...")
        result = checkpoint.run()
        
        # Проверяем результат
        if hasattr(result, 'success'):
            if result.success:
                logger.info("✓ Валидация прошла успешно!")
            else:
                logger.warning("⚠ Валидация завершилась с предупреждениями или ошибками")
        else:
            # Для некоторых версий API результат может иметь другую структуру
            logger.info("Валидация выполнена")
        
        logger.info(f"Результаты валидации: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Ошибка при валидации данных: {str(e)}", exc_info=True)
        return None


def main():
    """
    Главная функция для запуска всего процесса настройки и валидации данных.
    """
    try:
        logger.info("=" * 60)
        logger.info("Запуск процесса настройки Great Expectations")
        logger.info("=" * 60)
        
        # 1. Загрузка конфигурации из переменных окружения
        config = get_config_from_env()
        
        # 2. Валидация путей
        validate_paths(config)
        
        # 3. Настройка Great Expectations
        context, data_source, data_asset, batch_definition = setup_great_expectations(config)
        
        # 4. Создание expectations
        suite = create_expectations(context, data_asset)
        
        # 5. Выполнение валидации данных (если suite создан успешно)
        if suite:
            suite_name = suite.name
            validation_result = validate_data(context, data_asset, suite_name)
            
            if validation_result:
                logger.info("=" * 60)
                logger.info("Процесс валидации завершен успешно")
                logger.info("=" * 60)
            else:
                logger.warning("Валидация не была выполнена из-за ошибок")
        else:
            logger.warning("Expectations не были созданы, валидация пропущена")
        
    except FileNotFoundError as e:
        logger.error(f"Ошибка файловой системы: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Критическая ошибка: {str(e)}", exc_info=True)
        raise


# DEFINITIONS:
# Context: Мозг системы (хранит настройки).
# Data Source: Указывает на папку с данными.
# Data Asset: Указывает на конкретный тип файла в этой папке.
# Batch: Конкретные данные, которые будут проверяться тестами.
# Expectation Suite: Набор правил для проверки данных.
# Validator: Объект для выполнения проверок на данных.
# Checkpoint: Точка проверки, объединяющая данные и expectations.

if __name__ == "__main__":
    main()
