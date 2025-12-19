# Файл: models.py
import re
from collections import Counter
import torch
import torch.nn as nn
import torch.optim as optim
import pickle
import sqlite3
import logging

logger = logging.getLogger(__name__)

class NgramModel:
    def __init__(self, max_n=5, top_k=400):
        self.max_n = max_n
        self.top_k = top_k

    def get_ngrams(self, text):
        text = re.sub(r'[^a-zA-Z\' ]', ' ', text.lower())
        text = re.sub(r'\s+', ' ', text).strip()
        text = ' ' + text + ' '
        counts = Counter()
        for n in range(1, self.max_n + 1):
            for i in range(len(text) - n + 1):
                ngram = text[i:i + n]
                counts[ngram] += 1
        sorted_ngrams = [ng for ng, _ in counts.most_common(self.top_k)]
        return sorted_ngrams

    def get_distance(self, doc_profile, cat_profile):
        cat_dict = {ng: rank for rank, ng in enumerate(cat_profile, 1)}
        distance = 0
        for rank_d, ng in enumerate(doc_profile, 1):
            rank_c = cat_dict.get(ng, len(cat_profile) + 1)
            distance += abs(rank_d - rank_c)
        return distance

class LanguageModel(nn.Module):
    def __init__(self, input_size):
        super().__init__()
        self.fc1 = nn.Linear(input_size, 32)
        self.relu = nn.ReLU()
        self.fc2 = nn.Linear(32, 2)

    def forward(self, x):
        x = self.fc1(x)
        x = self.relu(x)
        x = self.fc2(x)
        return x

class ModelTrainer:
    def __init__(self, data_loader):
        self.data_loader = data_loader

    def train(self):
        spanish_text = self.data_loader.download_training_data('spanish')
        italian_text = self.data_loader.download_training_data('italian')

        conn = sqlite3.connect('lang_detect.db')
        cur = conn.cursor()
        cur.execute('''CREATE TABLE IF NOT EXISTS profiles
                       (method TEXT, language TEXT, ngram TEXT, rank INTEGER)''')

        ngram_model = NgramModel(max_n=5)
        alpha_model = NgramModel(max_n=1)
        for method, model in [('ngram', ngram_model), ('alpha', alpha_model)]:
            for lang, text in [('spanish', spanish_text), ('italian', italian_text)]:
                prof = model.get_ngrams(text)
                cur.execute(f"DELETE FROM profiles WHERE method='{method}' AND language='{lang}'")
                for r, ng in enumerate(prof, 1):
                    cur.execute("INSERT INTO profiles VALUES (?, ?, ?, ?)", (method, lang, ng, r))
        conn.commit()
        conn.close()

        spanish_samples = self.data_loader.get_samples('spanish')
        italian_samples = self.data_loader.get_samples('italian')
        all_samples = spanish_samples + italian_samples
        all_chars = set(c.lower() for s in all_samples for c in s if c.isalpha() or c in " '")
        vocab = sorted(all_chars)
        vocab_size = len(vocab)
        index = {c: i for i, c in enumerate(vocab)}
        with open('vocab.pkl', 'wb') as f:
            pickle.dump(index, f)

        X = [self.get_feature(s, index, vocab_size) for s in all_samples]
        y = [0] * len(spanish_samples) + [1] * len(italian_samples)
        X = torch.tensor(X, dtype=torch.float32)
        y = torch.tensor(y, dtype=torch.long)

        model = LanguageModel(vocab_size)
        optimizer = optim.Adam(model.parameters(), lr=0.001)
        loss_fn = nn.CrossEntropyLoss()

        for epoch in range(100):
            optimizer.zero_grad()
            out = model(X)
            loss = loss_fn(out, y)
            loss.backward()
            optimizer.step()

        torch.save(model.state_dict(), 'model.pth')

    def get_feature(self, text, index, vocab_size):
        text = text.lower()
        counts = Counter(c for c in text if c.isalpha() or c in " '")
        total = sum(counts.values())
        vec = [0.0] * vocab_size
        for c, cnt in counts.items():
            if c in index:
                vec[index[c]] = cnt / total if total > 0 else 0
        return vec