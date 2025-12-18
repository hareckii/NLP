import requests
import os
import time
import random
from urllib.parse import quote
from bs4 import BeautifulSoup

def setup_folders():
    """Создание структуры папок"""
    folders = ['html_docs/spanish', 'html_docs/italian', 'html_docs/mixed']
    for folder in folders:
        os.makedirs(folder, exist_ok=True)
    print("Структура папок создана")
    return folders

def get_random_article_titles(lang_code, count=10):
    """Получение случайных заголовков статей через API Википедии"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    titles = []
    
    try:
        # API для получения случайных статей
        api_url = f"https://{lang_code}.wikipedia.org/w/api.php"
        params = {
            'action': 'query',
            'list': 'random',
            'rnnamespace': 0,  # Основное пространство имен (статьи)
            'rnlimit': count,
            'format': 'json'
        }
        
        response = requests.get(api_url, params=params, headers=headers, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            titles = [item['title'] for item in data['query']['random']]
            print(f"Получено {len(titles)} заголовков для языка {lang_code}")
        else:
            print(f"Ошибка API: {response.status_code}")
            
    except Exception as e:
        print(f"Ошибка при получении заголовков: {e}")
    
    return titles

def save_html_from_title(title, lang_code, folder, index):
    """Скачивание и сохранение HTML статьи по заголовку"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive'
    }
    
    try:
        # Кодируем заголовок для URL
        encoded_title = quote(title.replace(' ', '_'))
        url = f"https://{lang_code}.wikipedia.org/wiki/{encoded_title}"
        
        print(f"Скачивание: {title} ({lang_code})")
        
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            # Очищаем HTML (оставляем только контент статьи)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Удаляем ненужные элементы
            for element in soup.find_all(['script', 'style', 'nav', 'header', 'footer', 
                                         'aside', '.mw-editsection', '.reference']):
                element.decompose()
            
            # Получаем основной контент
            content_div = soup.find('div', {'id': 'mw-content-text'})
            if content_div:
                # Создаем чистый HTML
                clean_html = f"""<!DOCTYPE html>
<html lang="{lang_code}">
<head>
    <meta charset="UTF-8">
    <title>{title}</title>
</head>
<body>
    <h1>{title}</h1>
    {str(content_div)}
</body>
</html>"""
                
                # Сохраняем файл
                filename = f"{folder}/{index:02d}_{title[:30].replace('/', '_')}.html"
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(clean_html)
                
                print(f"  ✓ Сохранено: {filename}")
                return True
            else:
                print(f"  ✗ Не найден контент для: {title}")
                return False
        else:
            print(f"  ✗ Ошибка HTTP {response.status_code} для: {title}")
            return False
            
    except Exception as e:
        print(f"  ✗ Ошибка при скачивании {title}: {e}")
        return False

def create_mixed_language_file(spanish_texts, italian_texts, folder, index):
    """Создание файла со смешанным текстом (для тестирования)"""
    try:
        # Берем часть текста из каждого языка
        mixed_text = ""
        if spanish_texts and italian_texts:
            # Испанская часть
            spanish_part = spanish_texts[0][:500] if len(spanish_texts[0]) > 500 else spanish_texts[0]
            # Итальянская часть
            italian_part = italian_texts[0][:500] if len(italian_texts[0]) > 500 else italian_texts[0]
            
            mixed_text = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Mixed Language Document {index}</title>
</head>
<body>
    <h1>Documento multilingüe / Documento multilingue</h1>
    
    <h2>Español / Spagnolo</h2>
    <p>{spanish_part}</p>
    
    <h2>Italiano / Italiano</h2>
    <p>{italian_part}</p>
    
    <p>Este es un texto en español. Questo è un testo in italiano.</p>
    <p>El español y el italiano son lenguas romances. Lo spagnolo e l'italiano sono lingue romanze.</p>
</body>
</html>"""
            
            filename = f"{folder}/mixed_{index:02d}.html"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(mixed_text)
            
            print(f"  ✓ Создан смешанный файл: {filename}")
            return True
            
    except Exception as e:
        print(f"  ✗ Ошибка создания смешанного файла: {e}")
    
    return False

def download_wikipedia_articles():
    """Основная функция скачивания статей"""
    print("=" * 60)
    print("Скачивание HTML документов с Википедии")
    print("=" * 60)
    
    # Настройка папок
    folders = setup_folders()
    spanish_folder, italian_folder, mixed_folder = folders
    
    # Получаем заголовки статей
    print("\n1. Получение заголовков статей...")
    spanish_titles = get_random_article_titles('es', count=8)
    italian_titles = get_random_article_titles('it', count=8)
    
    # Список для сохранения текстов для смешанных файлов
    spanish_texts = []
    italian_texts = []
    
    print("\n2. Скачивание испанских статей...")
    spanish_count = 0
    for i, title in enumerate(spanish_titles, 1):
        if save_html_from_title(title, 'es', spanish_folder, i):
            spanish_count += 1
            
            # Сохраняем текст для смешанных файлов
            try:
                filepath = f"{spanish_folder}/{i:02d}_{title[:30].replace('/', '_')}.html"
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    soup = BeautifulSoup(content, 'html.parser')
                    text = soup.get_text()[:1000]  # Первые 1000 символов
                    spanish_texts.append(text)
            except:
                pass
            
            # Пауза между запросами
            time.sleep(random.uniform(1.5, 3.0))
    
    print("\n3. Скачивание итальянских статей...")
    italian_count = 0
    for i, title in enumerate(italian_titles, 1):
        if save_html_from_title(title, 'it', italian_folder, i):
            italian_count += 1
            
            # Сохраняем текст для смешанных файлов
            try:
                filepath = f"{italian_folder}/{i:02d}_{title[:30].replace('/', '_')}.html"
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    soup = BeautifulSoup(content, 'html.parser')
                    text = soup.get_text()[:1000]
                    italian_texts.append(text)
            except:
                pass
            
            # Пауза между запросами
            time.sleep(random.uniform(1.5, 3.0))
    
    print("\n4. Создание смешанных файлов...")
    mixed_count = 0
    for i in range(1, 4):  # Создаем 3 смешанных файла
        if create_mixed_language_file(spanish_texts, italian_texts, mixed_folder, i):
            mixed_count += 1
    
    # Итоговая статистика
    print("\n" + "=" * 60)
    print("СКАЧИВАНИЕ ЗАВЕРШЕНО!")
    print("=" * 60)
    print(f"Испанские статьи: {spanish_count}/{len(spanish_titles)}")
    print(f"Итальянские статьи: {italian_count}/{len(italian_titles)}")
    print(f"Смешанные файлы: {mixed_count}/3")
    print(f"\nФайлы сохранены в:")
    print(f"  Испанские: {spanish_folder}/")
    print(f"  Итальянские: {italian_folder}/")
    print(f"  Смешанные: {mixed_folder}/")
    print("\nДля тестирования системы используйте файлы из папки html_docs/")
    
    return {
        'spanish': spanish_count,
        'italian': italian_count,
        'mixed': mixed_count
    }

def create_test_summary():
    """Создание файла с описанием тестовой коллекции"""
    summary = """# ТЕСТОВАЯ КОЛЛЕКЦИЯ ДЛЯ РАСПОЗНАВАНИЯ ЯЗЫКА

## Состав коллекции:
- Испанские HTML документы: 8 файлов
- Итальянские HTML документы: 8 файлов  
- Смешанные документы: 3 файла

## Источник:
Все документы скачаны с Википедии (Wikipedia)

## Структура папок:
html_docs/
├── spanish/      # Документы на испанском языке
├── italian/      # Документы на итальянском языке
└── mixed/        # Документы со смешанным текстом

## Использование в системе:
1. Запустите интерфейс Tkinter
2. Выберите файл из папки html_docs/
3. Нажмите "Detect Language"
4. Сравните результаты трех методов

## Примеры тем статей:
- История, наука, культура, география
- Известные личности, города, события
- Язык, литература, искусство
"""
    
    with open('html_docs/README.md', 'w', encoding='utf-8') as f:
        f.write(summary)
    
    print("\nСоздан файл описания: html_docs/README.md")

if __name__ == "__main__":
    # Запуск скачивания
    results = download_wikipedia_articles()
    
    # Создание файла описания
    create_test_summary()
    
    print("\nГотово! Теперь можно тестировать систему распознавания языка.")