import requests
from bs4 import BeautifulSoup
import re
from methods import LanguageDetector
from database import get_session, LanguageProfile, AlphabetProfile
import time

def download_wikipedia_text(language_code, language_name, num_pages=10):
    """Скачивание текстов с Wikipedia для обучения"""
    print(f"Downloading {language_name} texts...")
    
    base_url = f"https://{language_code}.wikipedia.org"
    articles = []
    
    try:
        # Получаем случайные статьи
        for i in range(num_pages):
            url = f"{base_url}/wiki/Special:Random"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Извлекаем текст из параграфов
                paragraphs = soup.find_all('p')
                text = ' '.join([p.get_text() for p in paragraphs])
                
                # Очищаем текст
                text = re.sub(r'\[\d+\]', '', text)  # Удаляем ссылки на источники
                text = re.sub(r'\s+', ' ', text)     # Удаляем лишние пробелы
                
                if len(text) > 100:  # Минимальная длина текста
                    articles.append(text)
                    print(f"  Downloaded article {i+1}/{num_pages}")
                
            time.sleep(1)  # Задержка чтобы не перегружать сервер
            
    except Exception as e:
        print(f"Error downloading {language_name}: {str(e)}")
    
    return articles

def train_models():
    """Обучение моделей для испанского и итальянского языков"""
    detector = LanguageDetector()
    session = get_session()
    
    languages = [
        ('es', 'spanish'),
        ('it', 'italian')
    ]
    
    for lang_code, lang_name in languages:
        print(f"\nTraining for {lang_name}...")
        
        # Скачиваем тексты
        articles = download_wikipedia_text(lang_code, lang_name, num_pages=15)
        
        if not articles:
            print(f"No articles downloaded for {lang_name}")
            continue
        
        # Объединяем все тексты
        full_text = ' '.join(articles)
        
        # Обучаем N-грамм модель
        print("  Building N-gram profile...")
        ngram_profile = detector.build_ngram_profile(full_text)
        
        # Сохраняем N-грамм профиль в БД
        for ngram, data in ngram_profile.items():
            profile = LanguageProfile(
                language=lang_name,
                ngram=ngram,
                frequency=data['frequency'],
                rank=data['rank'],
                method='n-gram'
            )
            session.add(profile)
        
        # Обучаем алфавитную модель
        print("  Building alphabet profile...")
        alphabet_profile = detector.build_alphabet_profile(full_text)
        
        # Сохраняем алфавитный профиль в БД
        for char, freq in alphabet_profile.items():
            profile = AlphabetProfile(
                language=lang_name,
                character=char,
                frequency=freq
            )
            session.add(profile)
        
        session.commit()
        print(f"  {lang_name} profile saved to database")
    
    session.close()
    print("\nTraining completed!")

if __name__ == "__main__":
    # Запуск обучения моделей
    train_models()