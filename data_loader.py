# Файл: data_loader.py
import logging
from datasets import load_dataset

logger = logging.getLogger(__name__)

class DataLoader:
    def __init__(self, target_size=120 * 1024, num_samples=50, chunk_min_len=200):
        self.target_size = target_size
        self.num_samples = num_samples
        self.chunk_min_len = chunk_min_len

    def download_training_data(self, lang):
        dataset_name = "20231101.es" if lang == 'spanish' else "20231101.it"
        logger.info(f"Загрузка датасета Wikipedia для {lang} ({dataset_name})...")
        try:
            dataset = load_dataset("wikimedia/wikipedia", dataset_name, split="train")
            logger.info(f"Датасет загружен: {len(dataset)} статей")
            
            text = ""
            current_size = 0
            i = 0
            while current_size < self.target_size and i < len(dataset):
                article = dataset[i]['text']
                if len(article) > 100:
                    text += article + ' '
                    current_size = len(text.encode('utf-8'))
                    logger.info(f"Добавлена статья {i+1} ({len(article)//1024} Кб), всего {current_size//1024} Кб")
                i += 1
            logger.info(f"{lang} завершено: {current_size // 1024} Кб")
            return text
        except Exception as e:
            logger.error(f"Ошибка загрузки датасета: {e}")
            return ""

    def get_samples(self, lang):
        dataset_name = "20231101.es" if lang == 'spanish' else "20231101.it"
        logger.info(f"Сбор образцов для нейросети ({lang})...")
        try:
            dataset = load_dataset("wikimedia/wikipedia", dataset_name, split="train")
            samples = []
            i = 0
            while len(samples) < self.num_samples and i < len(dataset):
                article = dataset[i]['text']
                if len(article) > self.chunk_min_len:
                    samples.append(article)
                i += 1
            logger.info(f"{lang} образцы: {len(samples)}")
            return samples
        except Exception as e:
            logger.error(f"Ошибка: {e}")
            return []