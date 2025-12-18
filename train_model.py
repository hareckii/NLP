# Исправленный файл: train_model.py
# Изменения:
# 1. Унифицировал n=3, top_k=300.
# 2. Увеличил num_pages=30 для большего корпуса (лучше профили).
# 3. В download: улучшил очистку текста.
# 4. Добавил больше популярных страниц для качества.

import requests
from bs4 import BeautifulSoup
import re
from methods import LanguageDetector
from database import get_session, LanguageProfile, AlphabetProfile
import time
import random

def download_wikipedia_text(language_code, language_name, num_pages=30):
    """Скачивание текстов с Wikipedia для обучения"""
    print(f"Downloading {language_name} texts...")
    
    base_url = f"https://{language_code}.wikipedia.org"
    articles = []
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        for i in range(num_pages):
            # Расширенный список популярных статей
            popular_pages = [
                "Main_Page",
                "Italy" if language_code == 'it' else "Spain",
                "Rome" if language_code == 'it' else "Madrid",
                "Italian_language" if language_code == 'it' else "Spanish_language",
                "Pizza" if language_code == 'it' else "Flamenco",
                "Venice" if language_code == 'it' else "Barcelona",
                "Leonardo_da_Vinci" if language_code == 'it' else "Salvador_Dalí",
                "Colosseum" if language_code == 'it' else "Sagrada_Família",
                "Pasta" if language_code == 'it' else "Paella",
                "Vatican_City" if language_code == 'it' else "Prado_Museum",
            ]
            
            if i < len(popular_pages):
                page_title = popular_pages[i]
            else:
                api_url_random = f"{base_url}/w/api.php?action=query&list=random&rnnamespace=0&rnlimit=1&format=json"
                random_response = requests.get(api_url_random, headers=headers, timeout=10)
                
                if random_response.status_code != 200:
                    continue
                
                random_data = random_response.json()
                if 'query' in random_data and 'random' in random_data['query']:
                    page_title = random_data['query']['random'][0]['title']
                else:
                    continue
            
            print(f"  Получена статья {i+1}/{num_pages}: {page_title}")
            
            page_url = f"{base_url}/w/api.php?action=parse&page={page_title}&format=json&prop=text&redirects=true"
            response = requests.get(page_url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if 'parse' in data and 'text' in data['parse']:
                    html_content = data['parse']['text']['*']
                    soup = BeautifulSoup(html_content, 'html.parser')
                    
                    # Улучшенная очистка
                    for element in soup.find_all(['sup', 'table', 'div.navbox', 
                                                  'span.mw-editsection', 'div.reflist',
                                                  'ol.references', 'div.thumb', 'script', 'style']):
                        element.decompose()
                    
                    text = soup.get_text(separator=' ', strip=True)
                    
                    text = re.sub(r'\[\d+\]', '', text)
                    text = re.sub(r'\s+', ' ', text)
                    text = re.sub(r'<[^>]+>', ' ', text)
                    
                    text = text.lower()
                    text = re.sub(r'[^a-zàèéìíîòóùúñç\'\s]', ' ', text)
                    text = re.sub(r'\s+', ' ', text).strip()
                    
                    if len(text) > 1000:  # Увеличил min длину
                        articles.append(text)
                        print(f"    Добавлено: {len(text)} символов")
            
            time.sleep(random.uniform(1, 3))  # Увеличил паузу для избежания бана
            
    except Exception as e:
        print(f"Error downloading {language_name}: {str(e)}")
    
    print(f"  Всего загружено {len(articles)} статей для {language_name}")
    return articles

def train_models():
    """Обучение моделей"""
    detector = LanguageDetector()
    session = get_session()
    
    languages = [
        ('it', 'italian'),
        ('es', 'spanish')
    ]
    
    for lang_code, lang_name in languages:
        print(f"\n{'='*60}")
        print(f"Training for {lang_name.upper()}")
        print('='*60)
        
        articles = download_wikipedia_text(lang_code, lang_name, num_pages=30)
        
        if not articles:
            print(f"No articles downloaded for {lang_name}")
            continue
        
        full_text = ' '.join(articles)
        print(f"Общий размер текста: {len(full_text):,} символов")
        
        if len(full_text) < 20000:
            print(f"Слишком мало текста для {lang_name}, пропускаем...")
            continue
        
        print("  Building N-gram profile (n=3)...")
        ngram_profile = detector.build_ngram_profile(full_text, n=3, top_k=300)
        
        if not ngram_profile:
            print(f"  Не удалось построить N-gram профиль для {lang_name}")
            continue
        
        print(f"  Saving {len(ngram_profile)} N-grams to DB...")
        count = 0
        for ngram, data in ngram_profile.items():
            profile = LanguageProfile(
                language=lang_name,
                ngram=ngram,
                frequency=data['frequency'],
                rank=data['rank'],
                method='n-gram'
            )
            session.add(profile)
            count += 1
            
            if count % 50 == 0:
                session.flush()
        
        print("  Building alphabet profile...")
        alphabet_profile = detector.build_alphabet_profile(full_text)
        
        print(f"  Saving {len(alphabet_profile)} alphabet characters...")
        for char, freq in alphabet_profile.items():
            profile = AlphabetProfile(
                language=lang_name,
                character=char,
                frequency=freq
            )
            session.add(profile)
        
        session.commit()
        print(f"  {lang_name} profile saved to database ({count} N-grams)")
    
    session.close()
    print("\n" + "="*60)
    print("TRAINING COMPLETED!")
    print("="*60)

if __name__ == "__main__":
    train_models()