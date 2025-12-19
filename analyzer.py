# Файл: analyzer.py
from typing import Counter
from bs4 import BeautifulSoup
import time
import torch
import pickle
import sqlite3
import os
from models import NgramModel, LanguageModel

class Analyzer:
    def __init__(self):
        self.ngram_model = NgramModel(max_n=5)
        self.alpha_model = NgramModel(max_n=1)
        self.languages = {'spanish': 'Испанский', 'italian': 'Итальянский'}

    def analyze_file(self, file_path):
        conn = sqlite3.connect('lang_detect.db')
        model = None
        index = None
        vocab_size = None
        if os.path.exists('model.pth') and os.path.exists('vocab.pkl'):
            with open('vocab.pkl', 'rb') as f:
                index = pickle.load(f)
            vocab_size = len(index)
            model = LanguageModel(vocab_size)
            model.load_state_dict(torch.load('model.pth', map_location=torch.device('cpu')))
            model.eval()

        text = self.get_text_from_html(file_path)
        if not text.strip():
            return None

        methods = ['ngram', 'alpha', 'neural']
        results = {}
        times = {}
        confidences = {}
        for method in methods:
            start_time = time.time()
            if method == 'neural':
                if model is None:
                    results[method] = "Модель не обучена"
                    confidences[method] = 0.0
                else:
                    vec = self.get_feature(text, index, vocab_size)
                    out = model(torch.tensor([vec], dtype=torch.float32))
                    probs = torch.softmax(out, dim=1).detach().numpy()[0]
                    pred = torch.argmax(out, dim=1).item()
                    lang = 'spanish' if pred == 0 else 'italian'
                    results[method] = self.languages[lang]
                    confidences[method] = probs[pred]
            else:
                model_instance = self.ngram_model if method == 'ngram' else self.alpha_model
                doc_profile = model_instance.get_ngrams(text)
                dist_sp = model_instance.get_distance(doc_profile, self.load_profile(conn.cursor(), method, 'spanish'))
                dist_it = model_instance.get_distance(doc_profile, self.load_profile(conn.cursor(), method, 'italian'))
                dist_total = dist_sp + dist_it if dist_sp + dist_it > 0 else 1
                lang = 'spanish' if dist_sp < dist_it else 'italian'
                results[method] = self.languages[lang]
                confidences[method] = 1 - (min(dist_sp, dist_it) / dist_total)
            times[method] = time.time() - start_time

        true_lang = self.determine_true_lang(file_path)
        conn.close()
        return {'file': file_path, 'results': results, 'times': times, 'confidences': confidences, 'true_lang': true_lang}

    def get_text_from_html(self, file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f, 'html.parser')
        return soup.get_text()

    def get_feature(self, text, index, vocab_size):
        text = text.lower()
        counts = Counter(c for c in text if c.isalpha() or c in " '")
        total = sum(counts.values())
        vec = [0.0] * vocab_size
        for c, cnt in counts.items():
            if c in index:
                vec[index[c]] = cnt / total if total > 0 else 0
        return vec

    def load_profile(self, cur, method, lang):
        cur.execute("SELECT ngram FROM profiles WHERE method=? AND language=? ORDER BY rank ASC", (method, lang))
        return [row[0] for row in cur.fetchall()]

    def determine_true_lang(self, file_path):
        fname = os.path.basename(file_path).lower()
        dirname = os.path.dirname(file_path).lower()
        if 'spanish' in fname or 'es' in fname or 'spanish' in dirname or 'es' in dirname:
            return 'spanish'
        elif 'italian' in fname or 'it' in fname or 'italian' in dirname or 'it' in dirname:
            return 'italian'
        return None

    def compute_stats(self, collection_results):
        stats = {'ngram': {'correct': 0, 'total': 0, 'time': 0, 'conf': 0},
                 'alpha': {'correct': 0, 'total': 0, 'time': 0, 'conf': 0},
                 'neural': {'correct': 0, 'total': 0, 'time': 0, 'conf': 0}}
        for res in collection_results:
            if res['true_lang']:
                for method in stats:
                    if res['results'][method] != "Модель не обучена":
                        stats[method]['total'] += 1
                        if res['results'][method] == self.languages[res['true_lang']]:
                            stats[method]['correct'] += 1
                        stats[method]['time'] += res['times'][method]
                        stats[method]['conf'] += res['confidences'][method]
        return stats

    def format_output(self, collection_results, stats):
        output_text = "Результаты анализа коллекции:\n\n"
        for res in collection_results:
            output_text += f"Файл: {res['file']}\n"
            for method in ['ngram', 'alpha', 'neural']:
                output_text += f"{method.capitalize()}: {res['results'][method]} (уверенность: {res['confidences'][method]:.2f}, время: {res['times'][method]:.4f} сек)\n"
            output_text += "\n"

        output_text += "Сводная статистика:\n"
        for method in stats:
            if stats[method]['total'] > 0:
                accuracy = stats[method]['correct'] / stats[method]['total'] * 100
                avg_time = stats[method]['time'] / stats[method]['total']
                avg_conf = stats[method]['conf'] / stats[method]['total']
                output_text += f"{method.capitalize()}: Точность {accuracy:.2f}% ({stats[method]['correct']}/{stats[method]['total']}), Ср. время {avg_time:.4f} сек, Ср. уверенность {avg_conf:.2f}\n"
        return output_text