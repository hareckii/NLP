import os
import hashlib
import requests
from pathlib import Path
import time

def calculate_file_hash(file_path):
    """Вычисляет MD5 хеш файла"""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def upload_file_sync(file_path, base_url, directory):
    """Синхронно загружает один файл на оба эндпоинта"""
    try:
        # Читаем содержимое файла как бинарные данные
        with open(file_path, 'rb') as f:
            file_content = f.read()
        
        # Вычисляем хеш файла
        hash_value = calculate_file_hash(file_path)
        
        # Определяем title и path
        title = file_path.stem
        absolute_path = str(file_path.absolute())
        
        # Подготавливаем данные формы для /add
        files_add = {
            'file': (file_path.name, file_content, 'text/plain')
        }
        
        data_add = {
            'title': title,
            'path': absolute_path,
            'hash_value': hash_value
        }
        
        # Подготавливаем данные формы для /load_file
        files_load = {
            'file': (file_path.name, file_content, 'text/plain')
        }
        
        print(f"Отправка файла: {file_path.name}")
        print(f"Title: {title}, Hash: {hash_value}")
        
        response_add = requests.post(
            "http://127.0.0.1:8000/documents/add", 
            files=files_add,
            data=data_add
            )
        
        if response_add.status_code == 200:
            result_add = response_add.json()
            print(f"  ✓ Файл успешно обработан")
        else:
            print(f"  ✗ Ошибка при обработке: {response_add.status_code} - {response_add.text}")
        
        # Небольшая пауза между запросами
        time.sleep(0.1)
        
        # Отправляем на эндпоинт /load_file
        response_load = requests.post(f"{base_url}/load_file", files=files_load)
        
        if response_load.status_code == 200:
            result_load = response_load.json()
            print(f"  ✓ Файл успешно обработан")
            return True
        else:
            print(f"  ✗ Ошибка при обработке: {response_load.status_code} - {response_load.text}")
            return False
            
    except Exception as e:
        print(f"✗ Ошибка при обработке файла {file_path}: {str(e)}")
        return False

def process_directory_sync(directory_path):
    """Синхронно обрабатывает все txt файлы в директории"""
    base_url = "http://127.0.0.1:8000/llm"  # Изменил на /llm согласно роутеру
    directory = Path(directory_path)
    
    # Находим все txt файлы рекурсивно
    txt_files = list(directory.rglob("*.txt"))
    
    print(f"Найдено {len(txt_files)} txt файлов")
    
    successful = 0
    processed = 0
    
    # Обрабатываем файлы по одному
    for file_path in txt_files:
        processed += 1
        print(f"\n[{processed}/{len(txt_files)}] Обработка файла: {file_path.name}")
        
        if upload_file_sync(file_path, base_url, directory):
            successful += 1
        
        # Пауза между файлами чтобы не перегружать сервер
        time.sleep(0.2)
        
        print("-" * 50)
    
    print(f"\nЗавершено! Успешно обработано: {successful}/{len(txt_files)} файлов")
    return successful

if __name__ == "__main__":
    directory_path = "/home/hareckii/university/cooking_hub_docs"
    
    if not os.path.exists(directory_path):
        print(f"Директория {directory_path} не существует!")
    else:
        process_directory_sync(directory_path)