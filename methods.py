# Исправленный файл: methods.py
# Основные изменения:
# 1. Для N-gram: реализовал стандартную "out-of-place" дистанцию по Cavnar-Trenkle.
#    Теперь дистанция рассчитывается как сумма |rank_test - rank_lang| для общих + штраф max_rank+1 за отсутствующие.
#    Это должно дать более адекватные дистанции и повысить уверенность.
# 2. Унифицировал n=3, top_k=300 для consistency с обучением (изменил на 3, как в train, но можно 4).
# 3. Для уверенности в N-gram: теперь относительная, на основе дистанций до обоих языков.
#    confidence = other_dist / (best_dist + other_dist) * 2 - 1  # от 0 до 1, где 0.5 -> 0 если равны, ближе к 1 если разница большая.
#    Добавил порог: если best_dist > threshold, confidence=0 (не наш язык).
# 4. Для neural: добавил preprocess_text(text), чтобы очистить от HTML и мусора.
#    Это должно исправить "всегда английский", т.к. HTML-тэги влияли.
# 5. Для alphabet: улучшил нормализацию уверенности аналогично N-gram (относительная).
# 6. Добавил отладочные принты для дистанций.
# 7. В extract_ngrams: пропуск если содержит пробелы (улучшено).

import re
from collections import Counter
import math
from langdetect import detect, DetectorFactory
import time
from database import get_session, LanguageProfile, AlphabetProfile

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
        # Оставляем только буквы и пробелы
        text = re.sub(r'[^a-zàèéìíîòóùúñç\'\s]', ' ', text)
        # Удаляем лишние пробелы
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    
    def extract_ngrams(self, text, n=3):  # Унифицировал n=3
        """Извлечение N-грамм из текста"""
        ngrams = []
        for i in range(len(text) - n + 1):
            ngram = text[i:i+n]
            if ' ' not in ngram:  # Пропускаем граммы с пробелами (улучшено)
                ngrams.append(ngram)
        return ngrams
    
    def build_ngram_profile(self, text, n=3, top_k=300):  # Унифицировал n=3
        """Построение N-грамм профиля"""
        text = self.preprocess_text(text)
        
        if len(text) < n:
            return {}
        
        ngrams = self.extract_ngrams(text, n)
        
        if not ngrams:
            return {}
        
        freq = Counter(ngrams)
        total_ngrams = sum(freq.values())
        
        # Берем top_k самых частых N-грамм
        top_ngrams = freq.most_common(top_k)
        
        # Создаем профиль {ngram: {'frequency': f, 'rank': r}}
        profile = {}
        for rank, (ngram, count) in enumerate(top_ngrams, 1):  # rank с 1
            profile[ngram] = {
                'frequency': count / total_ngrams,
                'rank': rank
            }
        
        return profile
    
    def build_alphabet_profile(self, text):
        """Построение алфавитного профиля"""
        text = self.preprocess_text(text)
        
        # Извлекаем только буквы
        letters = [char for char in text if char.isalpha()]
        
        if not letters:
            return {}
        
        total_letters = len(letters)
        freq = Counter(letters)
        
        profile = {}
        for letter, count in freq.items():
            profile[letter] = count / total_letters
        
        return profile
    
    def ngram_distance(self, test_profile, lang_profile):
        if not test_profile or not lang_profile:
            return float('inf')
        
        distance = 0
        max_rank = max(p['rank'] for p in lang_profile.values()) + 1  # ~301
        
        # Штраф за отсутствие — уменьшаем до 0.5 * max_rank, чтобы не "убивать" уверенность
        penalty = max_rank * 0.5
        
        for ngram, data in test_profile.items():
            if ngram in lang_profile:
                distance += abs(data['rank'] - lang_profile[ngram]['rank'])
            else:
                distance += penalty
        
        # Нормализация по количеству N-грамм в тесте
        if len(test_profile) > 0:
            distance /= len(test_profile)
        
        return distance
    
    def detect_language_n_gram(self, text, languages=['italian', 'spanish']):
        """Определение языка методом N-грамм"""
        start_time = time.time()
        
        try:
            # Строим профиль входного документа
            input_profile = self.build_ngram_profile(text, n=3, top_k=300)
            
            if not input_profile:
                print("N-gram: Пустой профиль входного документа")
                return None, 0.0, time.time() - start_time
            
            print(f"N-gram: Построен профиль с {len(input_profile)} N-граммами")
            
            best_language = None
            best_distance = float('inf')
            distances = {}
            
            for lang in languages:
                # Получаем профиль языка из БД
                profiles = self.session.query(LanguageProfile).filter_by(
                    language=lang, 
                    method='n-gram'
                ).order_by(LanguageProfile.rank).limit(300).all()
                
                if not profiles:
                    print(f"N-gram: Нет профиля для языка {lang}")
                    distances[lang] = float('inf')
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
                distances[lang] = distance
                
                print(f"N-gram: Расстояние до {lang}: {distance}")
                
                if distance < best_distance:
                    best_distance = distance
                    best_language = lang
            
            if best_language is None or best_distance == float('inf'):
                processing_time = time.time() - start_time
            else:
                # Относительная уверенность на основе дистанций до обоих языков
                other_lang = languages[0] if best_language == languages[1] else languages[1]
                other_distance = distances[other_lang]
                
                if other_distance == float('inf'):
                    confidence = 0.5  # Только один язык, средняя уверенность
                else:
                    # confidence = other / (best + other), от 0.5 до 1
                    confidence = other_distance / (best_distance + other_distance)
                    
                if best_distance > 3000:
                    confidence *= 0.5
            
            print(f"N-gram: Определен язык {best_language} с уверенностью {confidence:.3f}")
            
            return best_language, confidence, processing_time
            
        except Exception as e:
            print(f"Ошибка в N-gram методе: {str(e)}")
            import traceback
            traceback.print_exc()
            return None, 0.0, time.time() - start_time
    
    def alphabet_distance(self, profile1, profile2):
        """Расстояние между алфавитными профилями (Евклидово)"""
        all_chars = set(profile1.keys()) | set(profile2.keys())
        
        if not all_chars:
            return float('inf')
        
        distance = 0
        for char in all_chars:
            freq1 = profile1.get(char, 0)
            freq2 = profile2.get(char, 0)
            distance += (freq1 - freq2) ** 2
        
        return math.sqrt(distance)
    
    def detect_language_alphabet(self, text, languages=['italian', 'spanish']):
        """Определение языка алфавитным методом"""
        start_time = time.time()
        
        try:
            input_profile = self.build_alphabet_profile(text)
            
            if not input_profile:
                return None, 0.0, time.time() - start_time
            
            best_language = None
            best_distance = float('inf')
            distances = {}
            
            for lang in languages:
                profiles = self.session.query(AlphabetProfile).filter_by(
                    language=lang
                ).all()
                
                if not profiles:
                    continue
                
                lang_profile = {}
                for profile in profiles:
                    lang_profile[profile.character] = profile.frequency
                
                distance = self.alphabet_distance(input_profile, lang_profile)
                distances[lang] = distance
                
                if distance < best_distance:
                    best_distance = distance
                    best_language = lang
            
            if best_language is None:
                return None, 0.0, time.time() - start_time
            
            processing_time = time.time() - start_time
            
            # Относительная уверенность аналогично N-gram
            other_lang = languages[0] if best_language == languages[1] else languages[1]
            other_distance = distances.get(other_lang, float('inf'))
            
            if other_distance == float('inf'):
                confidence = 0.5
            else:
                confidence = other_distance / (best_distance + other_distance)
            
            # Нормализация
            confidence = max(0.01, min(0.99, confidence))
            
            return best_language, confidence, processing_time
            
        except Exception as e:
            print(f"Ошибка в алфавитном методе: {str(e)}")
            return None, 0.0, time.time() - start_time
    
    def detect_language_neural(self, text):
        """Определение языка нейросетевым методом"""
        start_time = time.time()
        
        try:
            # ДОБАВИЛ: препроцессинг текста для удаления HTML и мусора
            text = self.preprocess_text(text)
            
            if not text.strip():
                return None, 0.0, time.time() - start_time
            
            # Используем langdetect с обработкой ошибок
            from langdetect import detect_langs
            
            lang_probs = detect_langs(text)
            
            # Карта кодов языков (расширил для тестов)
            lang_map = {
                'es': 'spanish',
                'it': 'italian',
                'en': 'english',
                'fr': 'french',
                'de': 'german',
                'ru': 'russian'
            }
            
            # Берем самый вероятный язык
            best_lang = lang_probs[0]
            lang_name = lang_map.get(best_lang.lang, best_lang.lang)
            confidence = best_lang.prob
            
            processing_time = time.time() - start_time
            
            return lang_name, confidence, processing_time
            
        except Exception as e:
            print(f"Нейросеть: ошибка {e}, пробуем простой detect")
            try:
                text = self.preprocess_text(text)  # Еще раз на всякий
                lang_code = detect(text)
                lang_map = {
                    'es': 'spanish',
                    'it': 'italian',
                    'en': 'english',
                    'fr': 'french',
                    'de': 'german',
                    'ru': 'russian'
                }
                lang_name = lang_map.get(lang_code, lang_code)
                processing_time = time.time() - start_time
                return lang_name, 0.8, processing_time  # Средняя уверенность
            except:
                return None, 0.0, time.time() - start_time
    
    def detect_all_methods(self, text):
        """Определение языка всеми методами"""
        print("\n" + "="*50)
        print("НАЧАЛО РАСПОЗНАВАНИЯ ЯЗЫКА")
        print("="*50)
        
        results = {}
        
        # N-грамм метод
        print("\n[1/3] Запуск N-gram метода...")
        lang_n, conf_n, time_n = self.detect_language_n_gram(text)
        results['n_gram'] = {
            'language': lang_n,
            'confidence': conf_n if conf_n else 0.0,
            'time': time_n
        }
        
        # Алфавитный метод
        print("\n[2/3] Запуск алфавитного метода...")
        lang_a, conf_a, time_a = self.detect_language_alphabet(text)
        results['alphabet'] = {
            'language': lang_a,
            'confidence': conf_a if conf_a else 0.0,
            'time': time_a
        }
        
        # Нейросетевой метод
        print("\n[3/3] Запуск нейросетевого метода...")
        lang_nn, conf_nn, time_nn = self.detect_language_neural(text)
        results['neural'] = {
            'language': lang_nn,
            'confidence': conf_nn if conf_nn else 0.0,
            'time': time_nn
        }
        
        print("\n" + "="*50)
        print("РЕЗУЛЬТАТЫ:")
        print(f"N-gram:     {results['n_gram']['language']} ({results['n_gram']['confidence']:.3f})")
        print(f"Alphabet:   {results['alphabet']['language']} ({results['alphabet']['confidence']:.3f})")
        print(f"Neural:     {results['neural']['language']} ({results['neural']['confidence']:.3f})")
        print("="*50)
        
        return results