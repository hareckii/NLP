import re
from collections import Counter
import string
from langdetect import detect, DetectorFactory
import time
from database import get_session, LanguageProfile, AlphabetProfile

# Для воспроизводимости langdetect
DetectorFactory.seed = 0

class LanguageDetector:
    def __init__(self):
        self.session = get_session()
    
    def preprocess_text(self, text):
        """Предварительная обработка текста"""
        # Удаление HTML тегов
        text = re.sub(r'<[^>]+>', ' ', text)
        # Приведение к нижнему регистру
        text = text.lower()
        # Удаление лишних пробелов
        text = ' '.join(text.split())
        return text
    
    def extract_ngrams(self, text, n=5):
        """Извлечение N-грамм из текста"""
        ngrams = []
        for i in range(len(text) - n + 1):
            ngrams.append(text[i:i+n])
        return ngrams
    
    def build_ngram_profile(self, text, n=5, top_k=300):
        """Построение N-грамм профиля"""
        text = self.preprocess_text(text)
        ngrams = self.extract_ngrams(text, n)
        freq = Counter(ngrams)
        
        # Получаем top_k самых частых N-грамм
        top_ngrams = freq.most_common(top_k)
        
        # Создаем профиль с рангами
        profile = {}
        for rank, (ngram, count) in enumerate(top_ngrams):
            profile[ngram] = {
                'frequency': count / len(ngrams),
                'rank': rank
            }
        
        return profile
    
    def ngram_distance(self, profile1, profile2):
        """Расчет расстояния между N-грамм профилями (Out Of Place)"""
        distance = 0
        
        for ngram, data1 in profile1.items():
            if ngram in profile2:
                rank1 = data1['rank']
                rank2 = profile2[ngram]['rank']
                distance += abs(rank1 - rank2)
            else:
                # Если N-грамма отсутствует, добавляем максимальный ранг
                distance += len(profile1)
        
        # Добавляем N-граммы из profile2, которых нет в profile1
        for ngram in profile2:
            if ngram not in profile1:
                distance += len(profile2)
        
        return distance
    
    def detect_language_n_gram(self, text, languages=['spanish', 'italian']):
        """Определение языка методом N-грамм"""
        start_time = time.time()
        
        # Строим профиль входного документа
        input_profile = self.build_ngram_profile(text)
        
        min_distance = float('inf')
        detected_language = None
        
        # Загружаем профили языков из базы данных
        for lang in languages:
            # Получаем профиль языка из БД
            profiles = self.session.query(LanguageProfile).filter_by(
                language=lang, 
                method='n-gram'
            ).all()
            
            if not profiles:
                continue
            
            # Собираем профиль из БД
            lang_profile = {}
            for profile in profiles:
                lang_profile[profile.ngram] = {
                    'frequency': profile.frequency,
                    'rank': profile.rank
                }
            
            # Вычисляем расстояние
            distance = self.ngram_distance(input_profile, lang_profile)
            
            if distance < min_distance:
                min_distance = distance
                detected_language = lang
        
        processing_time = time.time() - start_time
        
        # Нормализуем уверенность (чем меньше расстояние, тем выше уверенность)
        confidence = 1.0 / (1.0 + min_distance/1000) if min_distance > 0 else 1.0
        
        return detected_language, confidence, processing_time
    
    def build_alphabet_profile(self, text):
        """Построение алфавитного профиля"""
        text = self.preprocess_text(text)
        
        # Удаляем все, кроме букв
        letters = [char for char in text if char.isalpha()]
        total_letters = len(letters)
        
        if total_letters == 0:
            return {}
        
        # Считаем частоты букв
        freq = Counter(letters)
        profile = {}
        
        for letter, count in freq.items():
            profile[letter] = count / total_letters
        
        return profile
    
    def alphabet_distance(self, profile1, profile2):
        """Расстояние между алфавитными профилями (евклидово)"""
        all_chars = set(profile1.keys()) | set(profile2.keys())
        distance = 0
        
        for char in all_chars:
            freq1 = profile1.get(char, 0)
            freq2 = profile2.get(char, 0)
            distance += (freq1 - freq2) ** 2
        
        return distance ** 0.5
    
    def detect_language_alphabet(self, text, languages=['spanish', 'italian']):
        """Определение языка алфавитным методом"""
        start_time = time.time()
        
        # Строим профиль входного документа
        input_profile = self.build_alphabet_profile(text)
        
        if not input_profile:
            return None, 0.0, time.time() - start_time
        
        min_distance = float('inf')
        detected_language = None
        
        for lang in languages:
            # Получаем профиль языка из БД
            profiles = self.session.query(AlphabetProfile).filter_by(
                language=lang
            ).all()
            
            if not profiles:
                continue
            
            # Собираем профиль из БД
            lang_profile = {}
            for profile in profiles:
                lang_profile[profile.character] = profile.frequency
            
            # Вычисляем расстояние
            distance = self.alphabet_distance(input_profile, lang_profile)
            
            if distance < min_distance:
                min_distance = distance
                detected_language = lang
        
        processing_time = time.time() - start_time
        
        # Нормализуем уверенность
        confidence = 1.0 / (1.0 + min_distance) if min_distance > 0 else 1.0
        
        return detected_language, confidence, processing_time
    
    def detect_language_neural(self, text):
        """Определение языка нейросетевым методом (используем langdetect)"""
        start_time = time.time()
        
        try:
            # langdetect возвращает код языка (например, 'es', 'it')
            lang_code = detect(text)
            
            # Преобразуем код в полное название
            lang_map = {
                'es': 'spanish',
                'it': 'italian',
                'en': 'english',
                'fr': 'french',
                'de': 'german',
                'ru': 'russian'
            }
            
            detected_language = lang_map.get(lang_code, lang_code)
            
            # langdetect не возвращает уверенность, но мы можем эмулировать
            processing_time = time.time() - start_time
            
            # Для langdetect фиксированная уверенность (так как нет вероятности)
            confidence = 0.95
            
            return detected_language, confidence, processing_time
        except:
            return None, 0.0, time.time() - start_time
    
    def detect_all_methods(self, text):
        """Определение языка всеми методами"""
        results = {}
        
        # N-грамм метод
        lang_n, conf_n, time_n = self.detect_language_n_gram(text)
        results['n_gram'] = {
            'language': lang_n,
            'confidence': conf_n,
            'time': time_n
        }
        
        # Алфавитный метод
        lang_a, conf_a, time_a = self.detect_language_alphabet(text)
        results['alphabet'] = {
            'language': lang_a,
            'confidence': conf_a,
            'time': time_a
        }
        
        # Нейросетевой метод
        lang_nn, conf_nn, time_nn = self.detect_language_neural(text)
        results['neural'] = {
            'language': lang_nn,
            'confidence': conf_nn,
            'time': time_nn
        }
        
        return results  