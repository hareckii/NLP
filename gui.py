# Файл: gui.py
import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from ttkthemes import ThemedTk
import threading
from tkinter.scrolledtext import ScrolledText
from data_loader import DataLoader
from models import ModelTrainer
from analyzer import Analyzer

class App:
    def __init__(self):
        self.root = ThemedTk(theme="arc")
        self.root.title("Автоматическое распознавание языка")
        self.root.geometry("800x600")
        self.root.resizable(True, True)

        main_frame = ttk.Frame(self.root, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main_frame, text="Лабораторная работа №2: Распознавание языка текста (Вариант 3)", font=("Helvetica", 14, "bold")).pack(pady=10)

        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=10)

        ttk.Button(btn_frame, text="Построить профили", command=self.build_profiles).pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text="Загрузить тестовую коллекцию", command=self.analyze_collection).pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text="Помощь", command=self.show_help).pack(side=tk.LEFT, padx=10)

        self.progress = ttk.Progressbar(main_frame, maximum=100, mode='determinate')
        self.progress.pack(fill=tk.X, pady=10)

        result_frame = ttk.Frame(main_frame)
        result_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        self.result_text = ScrolledText(result_frame, height=20, wrap='word', font=("Consolas", 10))
        self.result_text.pack(fill=tk.BOTH, expand=True)

        self.data_loader = DataLoader()
        self.model_trainer = ModelTrainer(self.data_loader)
        self.analyzer = Analyzer()

    def build_profiles(self):
        self.progress['value'] = 0
        threading.Thread(target=self.model_trainer.train).start()

    def analyze_collection(self):
        folder_path = filedialog.askdirectory(title="Выберите папку с тестовыми HTML-файлами")
        if not folder_path:
            return

        collection_results = []
        files = [f for f in os.listdir(folder_path) if f.lower().endswith('.html')]
        for f in files:
            file_path = os.path.join(folder_path, f)
            result = self.analyzer.analyze_file(file_path)
            if result:
                collection_results.append(result)

        if not collection_results:
            messagebox.showwarning("Предупреждение", "Нет HTML-файлов в папке")
            return

        stats = self.analyzer.compute_stats(collection_results)
        output_text = self.analyzer.format_output(collection_results, stats)
        self.result_text.insert(tk.END, output_text + "\n" + "-"*80 + "\n")
        self.result_text.see(tk.END)
        self.save_results(output_text)

    def save_results(self, text):
        file_path = filedialog.asksaveasfilename(defaultextension=".txt")
        if file_path:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(text)
            messagebox.showinfo("Успех", "Результаты сохранены!")

    def show_help(self):
        help_text = "Инструкция:\n1. Построить профили — загрузит данные и обучит модель.\n2. Загрузить коллекцию — анализ папки с HTML-файлами.\nРезультаты в окне с прокруткой, можно сохранить."
        messagebox.showinfo("Помощь", help_text)

    def run(self):
        self.root.mainloop()