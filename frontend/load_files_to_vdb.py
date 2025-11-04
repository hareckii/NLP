import os
import requests

# === Настройки ===
FOLDER_PATH = r"C:\Users\User\Documents\cooking_hub_docs"
URL = "http://127.0.0.1:8000/llm/load_file"

# === Основная функция ===
def upload_all_files(folder_path, url):
    # Проверяем, что путь существует
    if not os.path.exists(folder_path):
        print(f"❌ Папка не найдена: {folder_path}")
        return

    files_uploaded = 0

    for root, _, files in os.walk(folder_path):
        for filename in files:
            file_path = os.path.join(root, filename)

            try:
                with open(file_path, "rb") as f:
                    # Отправляем файл как multipart/form-data
                    files = {"file": (filename, f)}
                    response = requests.post(url, files=files)

                if response.status_code == 200:
                    print(f"✅ Загружен: {filename}")
                else:
                    print(f"⚠️ Ошибка при загрузке {filename}: {response.status_code} — {response.text}")

                files_uploaded += 1

            except Exception as e:
                print(f"❌ Не удалось отправить {filename}: {e}")

    print(f"\n📦 Всего отправлено файлов: {files_uploaded}")

# === Запуск ===
if __name__ == "__main__":
    upload_all_files(FOLDER_PATH, URL)
