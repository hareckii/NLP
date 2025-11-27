import threading
import time
import requests
from pathlib import Path
import hashlib
from typing import Dict
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FolderSyncClient:
    def __init__(self, folder_path: str, server_url: str = "http://127.0.0.1:8000", sync_interval: int = 60):
        self.folder_path = Path(folder_path)
        self.server_url = server_url
        self.sync_interval = sync_interval  # секунды
        self.is_running = False
        self.sync_thread = None
        
    def calculate_file_hash(self, file_path: Path) -> str:
        """Вычисляет MD5 хеш файла"""
        hash_md5 = hashlib.md5()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception as e:
            logger.error(f"Error calculating hash for {file_path}: {e}")
            return ""
    
    def scan_local_folder(self) -> Dict[str, str]:
        """Сканирует локальную папку и возвращает словарь {path: hash}"""
        local_files = {}
        
        if not self.folder_path.exists():
            logger.error(f"Folder {self.folder_path} does not exist")
            return local_files
            
        for file_path in self.folder_path.rglob("*.txt"):
            if file_path.is_file():
                try:
                    file_hash = self.calculate_file_hash(file_path)
                    if file_hash:  # только если хеш успешно вычислен
                        local_files[str(file_path.absolute())] = file_hash
                except Exception as e:
                    logger.error(f"Error processing file {file_path}: {e}")
                    
        return local_files
    
    def get_server_snapshot(self) -> Dict[str, str]:
        """Получает скриншот файлов с сервера"""
        try:
            response = requests.get(f"{self.server_url}/documents/snapshot")
            if response.status_code == 200:
                snapshot = response.json()
                return {file["path"]: file["hash_value"] for file in snapshot}
            else:
                logger.error(f"Server error: {response.status_code} - {response.text}")
                return {}
        except Exception as e:
            logger.error(f"Error getting server snapshot: {e}")
            return {}
    
    def upload_file(self, file_path: Path) -> bool:
        """Загружает файл на сервер"""
        try:
            with open(file_path, 'rb') as f:
                file_content = f.read()
            
            hash_value = self.calculate_file_hash(file_path)
            
            files = {'file': (file_path.name, file_content, 'text/plain')}
            data = {
                'title': file_path.stem,
                'path': str(file_path.absolute()),
                'hash_value': hash_value
            }
            
            response = requests.post(
                f"{self.server_url}/documents/add",
                files=files,
                data=data
            )
            
            if response.status_code == 200:
                logger.info(f"✓ File uploaded: {file_path.name}")
                return True
            else:
                logger.error(f"✗ Upload failed for {file_path.name}: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error uploading file {file_path}: {e}")
            return False
    
    def update_file(self, file_path: Path, file_id: int) -> bool:
        """Обновляет файл на сервере"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            hash_value = self.calculate_file_hash(file_path)
            
            update_data = {
                "id": file_id,
                "title": file_path.stem,
                "text": content,
                "path": str(file_path.absolute()),
                "hash_value": hash_value
            }
            
            response = requests.patch(
                f"{self.server_url}/documents/update",
                json=update_data
            )
            
            if response.status_code == 200:
                logger.info(f"✓ File updated: {file_path.name}")
                return True
            else:
                logger.error(f"✗ Update failed for {file_path.name}: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error updating file {file_path}: {e}")
            return False
    
    def delete_file(self, file_path: str) -> bool:
        """Удаляет файл с сервера"""
        try:
            response = requests.delete(
                f"{self.server_url}/documents/delete_by_path",
                params={"file_path": file_path}
            )
            
            if response.status_code == 200:
                logger.info(f"✓ File deleted: {file_path}")
                return True
            else:
                logger.error(f"✗ Delete failed for {file_path}: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error deleting file {file_path}: {e}")
            return False
    
    def get_file_id_by_path(self, file_path: str) -> int:
        """Получает ID файла по пути (нужно для обновления)"""
        try:
            # Получаем все файлы и ищем по пути
            snapshot = self.get_server_snapshot()
            server_files = {file["path"]: file["id"] for file in requests.get(f"{self.server_url}/documents/snapshot").json()}
            return server_files.get(file_path)
        except:
            return None
    
    def sync(self):
        """Основная логика синхронизации"""
        logger.info("Starting synchronization...")
        
        try:
            # 1. Получаем данные с сервера
            server_files = self.get_server_snapshot()
            if not server_files:
                logger.error("Could not get server snapshot")
                return
            
            # 2. Сканируем локальную папку
            local_files = self.scan_local_folder()
            
            # 3. Анализируем различия
            changes_detected = False
            
            # Файлы, которые есть локально, но нет на сервере (добавить)
            files_to_add = set(local_files.keys()) - set(server_files.keys())
            
            # Файлы, которые есть на сервере, но нет локально (удалить)
            files_to_delete = set(server_files.keys()) - set(local_files.keys())
            
            # Файлы, которые есть в обоих местах, но хеши разные (обновить)
            files_to_update = set()
            for path in set(local_files.keys()) & set(server_files.keys()):
                if local_files[path] != server_files[path]:
                    files_to_update.add(path)
            
            # 4. Применяем изменения
            # Добавляем новые файлы
            for file_path in files_to_add:
                logger.info(f"New file detected: {file_path}")
                if self.upload_file(Path(file_path)):
                    changes_detected = True
            
            # Удаляем отсутствующие файлы
            for file_path in files_to_delete:
                logger.info(f"File to delete: {file_path}")
                if self.delete_file(file_path):
                    changes_detected = True
            
            # Обновляем измененные файлы
            for file_path in files_to_update:
                logger.info(f"File changed: {file_path}")
                file_id = self.get_file_id_by_path(file_path)
                if file_id and self.update_file(Path(file_path), file_id):
                    changes_detected = True
            
            if not changes_detected:
                logger.info("No changes detected")
            else:
                logger.info("Synchronization completed with changes")
                
        except Exception as e:
            logger.error(f"Error during synchronization: {e}")
    
    def start_sync_loop(self):
        """Запускает фоновую синхронизацию"""
        self.is_running = True
        
        def sync_loop():
            while self.is_running:
                try:
                    self.sync()
                    time.sleep(self.sync_interval)
                except Exception as e:
                    logger.error(f"Error in sync loop: {e}")
                    time.sleep(self.sync_interval)
        
        self.sync_thread = threading.Thread(target=sync_loop, daemon=True)
        self.sync_thread.start()
        logger.info(f"Background sync started (interval: {self.sync_interval}s)")
    
    def stop_sync_loop(self):
        """Останавливает фоновую синхронизацию"""
        self.is_running = False
        if self.sync_thread:
            self.sync_thread.join(timeout=5)
        logger.info("Background sync stopped")

# Использование
if __name__ == "__main__":
    # Создаем клиент синхронизации
    sync_client = FolderSyncClient(
        folder_path="/home/hareckii/university/cooking_hub_docs",
        server_url="http://127.0.0.1:8000",
        sync_interval=30  # синхронизация каждые 30 секунд
    )
    
    try:
        # Запускаем фоновую синхронизацию
        sync_client.start_sync_loop()
        
        # Основной поток может делать что-то еще
        print("Background sync is running. Press Ctrl+C to stop.")
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nStopping...")
        sync_client.stop_sync_loop()