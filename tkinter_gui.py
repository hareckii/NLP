import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import requests
import json
import threading
import os

class LanguageDetectionGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Automatic Language Detection System")
        self.root.geometry("900x700")
        
        # URL API
        self.api_url = "http://localhost:8000"
        
        self.setup_ui()
        
    def setup_ui(self):
        # Создаем вкладки
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Вкладка для детекции
        detection_frame = ttk.Frame(notebook)
        notebook.add(detection_frame, text="Language Detection")
        
        # Вкладка для статистики
        stats_frame = ttk.Frame(notebook)
        notebook.add(stats_frame, text="Statistics")
        
        # Вкладка для документов
        docs_frame = ttk.Frame(notebook)
        notebook.add(docs_frame, text="Documents")
        
        # Настройка вкладки детекции
        self.setup_detection_tab(detection_frame)
        
        # Настройка вкладки статистики
        self.setup_stats_tab(stats_frame)
        
        # Настройка вкладки документов
        self.setup_docs_tab(docs_frame)
        
        # Панель статуса
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
    def setup_detection_tab(self, parent):
        # Заголовок
        title_label = ttk.Label(parent, text="Automatic Language Detection", font=("Arial", 16, "bold"))
        title_label.pack(pady=10)
        
        # Фрейм для загрузки файла
        file_frame = ttk.LabelFrame(parent, text="Upload Document", padding=10)
        file_frame.pack(fill=tk.X, padx=20, pady=10)
        
        self.file_path_var = tk.StringVar()
        file_entry = ttk.Entry(file_frame, textvariable=self.file_path_var, width=60)
        file_entry.pack(side=tk.LEFT, padx=(0, 10))
        
        browse_btn = ttk.Button(file_frame, text="Browse...", command=self.browse_file)
        browse_btn.pack(side=tk.LEFT)
        
        # Кнопка детекции
        detect_btn = ttk.Button(parent, text="Detect Language", command=self.detect_language)
        detect_btn.pack(pady=10)
        
        # Фрейм для результатов
        results_frame = ttk.LabelFrame(parent, text="Detection Results", padding=10)
        results_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Создаем Treeview для результатов
        columns = ("Method", "Language", "Confidence", "Time (ms)")
        self.results_tree = ttk.Treeview(results_frame, columns=columns, show="headings", height=3)
        
        for col in columns:
            self.results_tree.heading(col, text=col)
            self.results_tree.column(col, width=150)
        
        self.results_tree.pack(fill=tk.BOTH, expand=True)
        
        # Фрейм для текста
        text_frame = ttk.LabelFrame(parent, text="Document Content", padding=10)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        self.text_display = scrolledtext.ScrolledText(text_frame, height=10)
        self.text_display.pack(fill=tk.BOTH, expand=True)
        
    def setup_stats_tab(self, parent):
        # Заголовок
        title_label = ttk.Label(parent, text="System Statistics", font=("Arial", 16, "bold"))
        title_label.pack(pady=10)
        
        # Кнопка обновления статистики
        refresh_btn = ttk.Button(parent, text="Refresh Statistics", command=self.refresh_statistics)
        refresh_btn.pack(pady=10)
        
        # Фрейм для статистики
        stats_frame = ttk.LabelFrame(parent, text="Performance Metrics", padding=10)
        stats_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Treeview для статистики
        columns = ("Method", "Total Detections", "Avg Confidence", "Avg Time (ms)")
        self.stats_tree = ttk.Treeview(stats_frame, columns=columns, show="headings")
        
        for col in columns:
            self.stats_tree.heading(col, text=col)
            self.stats_tree.column(col, width=150)
        
        self.stats_tree.pack(fill=tk.BOTH, expand=True)
        
        # Общая статистика
        self.total_docs_var = tk.StringVar()
        total_label = ttk.Label(parent, textvariable=self.total_docs_var, font=("Arial", 10))
        total_label.pack(pady=5)
        
    def setup_docs_tab(self, parent):
        # Заголовок
        title_label = ttk.Label(parent, text="Document History", font=("Arial", 16, "bold"))
        title_label.pack(pady=10)
        
        # Кнопка обновления
        refresh_btn = ttk.Button(parent, text="Refresh Documents", command=self.refresh_documents)
        refresh_btn.pack(pady=10)
        
        # Treeview для документов
        columns = ("ID", "Filename", "N-gram", "Alphabet", "Neural", "Date")
        self.docs_tree = ttk.Treeview(parent, columns=columns, show="headings", height=15)
        
        column_widths = [50, 200, 100, 100, 100, 150]
        for i, col in enumerate(columns):
            self.docs_tree.heading(col, text=col)
            self.docs_tree.column(col, width=column_widths[i])
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=self.docs_tree.yview)
        self.docs_tree.configure(yscrollcommand=scrollbar.set)
        
        self.docs_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(20, 0), pady=10)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 20), pady=10)
        
    def browse_file(self):
        filename = filedialog.askopenfilename(
            title="Select document",
            filetypes=[("HTML files", "*.html"), ("Text files", "*.txt"), ("All files", "*.*")]
        )
        if filename:
            self.file_path_var.set(filename)
            
            # Показать содержимое файла
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    content = f.read()
                    self.text_display.delete(1.0, tk.END)
                    self.text_display.insert(1.0, content[:5000])  # Показываем первые 5000 символов
            except Exception as e:
                messagebox.showerror("Error", f"Cannot read file: {str(e)}")
    
    def detect_language(self):
        filepath = self.file_path_var.get()
        if not filepath or not os.path.exists(filepath):
            messagebox.showwarning("Warning", "Please select a file first")
            return
        
        def detection_thread():
            self.status_var.set("Processing...")
            
            try:
                with open(filepath, 'rb') as f:
                    files = {'file': f}
                    response = requests.post(f"{self.api_url}/detect/", files=files)
                    
                if response.status_code == 200:
                    result = response.json()
                    self.display_results(result)
                    self.status_var.set("Detection completed")
                else:
                    messagebox.showerror("Error", f"API error: {response.status_code}")
                    self.status_var.set("Error occurred")
                    
            except Exception as e:
                messagebox.showerror("Error", f"Connection error: {str(e)}")
                self.status_var.set("Connection failed")
        
        # Запускаем в отдельном потоке
        thread = threading.Thread(target=detection_thread)
        thread.daemon = True
        thread.start()
    
    def display_results(self, result):
        # Очищаем предыдущие результаты
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
        
        # Добавляем новые результаты
        results_data = result['results']
        
        for method, data in results_data.items():
            method_name = {
                'n_gram': 'N-gram',
                'alphabet': 'Alphabet',
                'neural': 'Neural Network'
            }.get(method, method)
            
            language = data['language'] or "Unknown"
            confidence = f"{data['confidence']:.3f}"
            time_ms = f"{data['time']*1000:.2f}"
            
            self.results_tree.insert("", tk.END, values=(method_name, language, confidence, time_ms))
        
        # Обновляем статистику
        self.refresh_statistics()
        self.refresh_documents()
    
    def refresh_statistics(self):
        try:
            response = requests.get(f"{self.api_url}/stats/")
            if response.status_code == 200:
                stats = response.json()
                
                # Обновляем общее количество
                self.total_docs_var.set(f"Total documents processed: {stats['total_documents']}")
                
                # Очищаем treeview
                for item in self.stats_tree.get_children():
                    self.stats_tree.delete(item)
                
                # Добавляем статистику по методам
                for method, data in stats['statistics'].items():
                    method_name = {
                        'n_gram': 'N-gram',
                        'alphabet': 'Alphabet',
                        'neural': 'Neural Network'
                    }.get(method, method)
                    
                    self.stats_tree.insert("", tk.END, values=(
                        method_name,
                        data['total_detections'],
                        f"{data['average_confidence']:.3f}",
                        f"{data['average_time']*1000:.2f}"
                    ))
                
        except Exception as e:
            messagebox.showerror("Error", f"Cannot fetch statistics: {str(e)}")
    
    def refresh_documents(self):
        try:
            response = requests.get(f"{self.api_url}/documents/")
            if response.status_code == 200:
                documents = response.json()
                
                # Очищаем treeview
                for item in self.docs_tree.get_children():
                    self.docs_tree.delete(item)
                
                # Добавляем документы
                for doc in documents:
                    self.docs_tree.insert("", tk.END, values=(
                        doc['id'],
                        doc['filename'],
                        doc['languages']['n_gram'] or "N/A",
                        doc['languages']['alphabet'] or "N/A",
                        doc['languages']['neural'] or "N/A",
                        doc['timestamp'][:19]  # Берем только дату и время
                    ))
                
        except Exception as e:
            messagebox.showerror("Error", f"Cannot fetch documents: {str(e)}")

def main():
    root = tk.Tk()
    app = LanguageDetectionGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()