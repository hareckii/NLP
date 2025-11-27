import tkinter as tk
from tkinter import messagebox, filedialog
from tkinter import scrolledtext
import requests
from loguru import logger

from load_files_to_vdb import process_directory_sync
# from windows.metrics_window import EvaluationWindow


results = {
    1: [3, 1, 7, 2, 4],
    2: [8, 2, 5, 3]
}
qrels = {
    1: {1, 2},
    2: {2, 8, 9}
}
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Cooking Hub — информационно-поисковая система")
        self.geometry("900x600")
        self.configure(bg="#f5f5f5")

        # Контейнер для всех страниц
        container = tk.Frame(self, bg="#f5f5f5")
        container.pack(fill="both", expand=True)

        # Словарь страниц
        self.frames = {}

        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        for Page in (StartPage, SearchPage):
            frame = Page(container, self)
            self.frames[Page] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        # Показать стартовую страницу
        self.show_frame(StartPage)

        # menubar = tk.Menu(self)
        # eval_menu = tk.Menu(menubar, tearoff=0)
        # if results:
        #     eval_menu.add_command(label="Оценить по метрикам", command=lambda: EvaluationWindow(self))        
        #     menubar.add_cascade(label="Оценка", menu=eval_menu)
        #     self.config(menu=menubar)
        # else:
        #     messagebox.showwarning("Внимание", "Введите поисковый запрос.")
        #     return
            

    def show_frame(self, page_class):
        """Переключение между страницами"""
        frame = self.frames[page_class]
        frame.tkraise()

# ==============================================================
# Стартовая страница
# ==============================================================

class StartPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#f5f5f5")
        self.controller = controller

        # --- Центральный контейнер ---
        center_frame = tk.Frame(self, bg="#f5f5f5")
        center_frame.place(relx=0.5, rely=0.5, anchor="center")  # центр

        # --- Заголовок с эмодзи и текстом ---
        title_frame = tk.Frame(center_frame, bg="#f5f5f5")
        title_frame.pack(anchor="center", pady=(0, 10))

        emoji_label = tk.Label(
            title_frame,
            text="🍕",
            font=("Segoe UI", 36, "bold"),
            fg="#f84f4f",
            bg="#f5f5f5"
        )
        emoji_label.pack( padx=(0, 10),  side="left")

        title_label = tk.Label(
            title_frame,
            text="Cooking Hub",
            font=("Segoe UI", 36, "bold"),
            fg="#000000",
            bg="#f5f5f5"
        )
        title_label.pack( side="left")

        # --- Подзаголовок ---
        subtitle = tk.Label(
            center_frame,
            text="Ваш интеллектуальный кулинарный поисковик",
            font=("Arial", 14),
            bg="#f5f5f5",
            fg="#4d4d4d",
            wraplength=600,
            justify="center"
        )
        subtitle.pack(anchor="center", pady=(10, 30))

        # --- Кнопка перехода ---
        start_btn = tk.Button(
            center_frame,
            text="Начать поиск",
            font=("Arial", 14, "bold"),
            bg="#4d4d4d",
            fg="white",
            padx=25, pady=10,
            relief="flat",
            activebackground="#f84f4f",
            command=lambda: controller.show_frame(SearchPage)
        )
        start_btn.pack()

# ==============================================================
# Страница поиска (Cooking Hub)
# ==============================================================

class SearchPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#f5f5f5")
        self.controller = controller

        # ---------- Шапка ----------
        header = tk.Frame(self, bg="#f5f5f5")
        header.pack(anchor="center", pady=(10, 0))

        title_label = tk.Label(
            header,
            text="🍕",
            font=("Segoe UI", 24, "bold"),
            fg="#f84f4f",
            bg="#f5f5f5"
        )
        title_label.pack(padx=(0, 10), side="left")
        title2_label = tk.Label(
            header,
            text="Cooking Hub",
            font=("Segoe UI", 24, "bold"),
            fg="#000000",
            bg="#f5f5f5"
        )
        title2_label.pack(side="left")

        # Кнопка "Назад"
        tk.Button(self, text="Назад", bg="#e0e0e0", relief="flat",
                  command=lambda: controller.show_frame(StartPage)).place(x=10, y=10)

        # ---------- Строка поиска ----------
        top_frame = tk.Frame(self, bg="#f5f5f5")
        top_frame.pack(fill="x", padx=10, pady=5)

        tk.Label(top_frame, text="Поисковый запрос:", font=("Arial", 11), bg="#f5f5f5").pack(side="left")
        self.query_entry = tk.Entry(top_frame, font=("Arial", 11))
        self.query_entry.pack(side="left", fill="x", expand=True, padx=5)
        
        # Кнопка выбора папки
        tk.Button(top_frame, text="📁 Выбрать папку", font=("Arial", 10), 
                  command=self.select_folder, bg="#e8f4fd", relief="flat").pack(side="right", padx=(5, 0))
        
        tk.Button(top_frame, text="Поиск", font=("Arial", 11, "bold"), command=self.on_search).pack(side="right")
        self.query_entry.bind("<Return>", self.on_search)

        # ---------- LLM / пояснение ----------
        middle_frame = tk.Frame(self, bg="#f5f5f5")
        middle_frame.pack(fill="x", padx=10, pady=5)

        tk.Label(middle_frame, text="Ответ от ИИ", font=("Arial", 11), bg="#f5f5f5").pack(anchor="w")
        self.llm_output = tk.Text(middle_frame, height=4, font=("Consolas", 10), wrap="word", bg="white")
        self.llm_output.pack(fill="x", expand=False)

        # ---------- Информация о выбранной папке ----------
        self.folder_info_frame = tk.Frame(self, bg="#f5f5f5")
        self.folder_info_frame.pack(fill="x", padx=10, pady=(0, 5))
        
        self.folder_label = tk.Label(
            self.folder_info_frame, 
            text="Папка не выбрана", 
            font=("Arial", 9), 
            bg="#f5f5f5", 
            fg="#666666",
            wraplength=600
        )
        self.folder_label.pack(anchor="w")
        
        self.selected_folder_path = None

        # ---------- Результаты поиска ----------
        bottom_frame = tk.Frame(self, bg="#f5f5f5")
        bottom_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.canvas = tk.Canvas(bottom_frame, bg="#f5f5f5", highlightthickness=0)
        scrollbar = tk.Scrollbar(bottom_frame, orient="vertical", command=self.canvas.yview)
        scrollable_frame = tk.Frame(self.canvas, bg="#f5f5f5")

        scrollable_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.results_frame = tk.Frame(scrollable_frame, bg="#f5f5f5")
        self.results_frame.pack(fill="both", expand=True)

    def select_folder(self):
        """Выбор папки на устройстве"""
        folder_path = filedialog.askdirectory(
            title="Выберите папку с документами",
            initialdir="/home/hareckii/university/cooking_hub_docs"  # Можно изменить на нужную стартовую директорию
        )
        
        if folder_path:
            self.selected_folder_path = folder_path
    
            # Опционально: автоматически загрузить файлы из папки
            self.load_files_from_folder(folder_path)

    def load_files_from_folder(self, folder_path):
        """Загрузка файлов из выбранной папки (можно доработать)"""
        process_directory_sync(folder_path)

    # --- Логика поиска ---
    def on_search(self, event=None):
        url = "http://127.0.0.1:8000/documents/search/"
        url_llm = "http://127.0.0.1:8000/llm/ask"
        query = self.query_entry.get().strip()
        if not query:
            messagebox.showwarning("Внимание", "Введите поисковый запрос.")
            return
        
        # Если выбрана папка, можно добавить её в параметры поиска
        search_params = {"message": query}
        if self.selected_folder_path:
            search_params["folder_path"] = self.selected_folder_path
        
        try:
            response = requests.get(url=url, params=search_params)
            if response.status_code != 200:
                error_data = response.json()
                messagebox.showerror("Ошибка", f"Ошибка {response.status_code}: {error_data.get('detail', 'Неизвестная ошибка')}")
                return
            else:
                results = response.json()
            
            response_llm = requests.get(url=url_llm, params={"message": query})
            if response_llm.status_code != 200:
                error_data = response_llm.json()
                messagebox.showerror("Ошибка", f"Ошибка {response_llm.status_code}: {error_data.get('detail', 'Неизвестная ошибка')}")
                return
            else:
                result_llm = response_llm.json()
            
            if result_llm:
                self.llm_output.delete(1.0, tk.END)
                self.llm_output.insert(tk.END, f"LLM-ответ для запроса: " + result_llm)
            
            self.show_results(results)
            
        except requests.exceptions.ConnectionError:
            messagebox.showerror("Ошибка", "Не удалось подключиться к серверу. Проверьте, запущен ли сервер.")

    # --- Отображение результатов ---
    def show_results(self, results):
        logger.debug(f"Results: {results}")
        for widget in self.results_frame.winfo_children():
            widget.destroy()

        if not results:
            tk.Label(self.results_frame, text="Ничего не найдено.", font=("Arial", 11)).pack(anchor="w", pady=5)
            return

        for doc in results:
            card = tk.Frame(self.results_frame, bg="white", highlightbackground="#d9d9d9", highlightthickness=1, padx=10, pady=6)
            card.pack(fill="x", pady=5, anchor="w")

            title_label = tk.Label(card, text=doc["title"], fg="#1a0dab", cursor="hand2",
                                   font=("Arial", 12, "underline"), bg="white", anchor="w", justify="left")
            title_label.pack(anchor="w", fill="x")
            title_label.bind("<Button-1>", lambda e, p=doc["id"]: self.open_doc(p))

            snippet_label = tk.Label(card, text=doc["similarity"], wraplength=800, justify="left",
                                     font=("Arial", 10), bg="white", fg="#4d4d4d")
            snippet_label.pack(anchor="w", pady=2, fill="x")

    def open_doc(self, id):
        url = "http://127.0.0.1:8000/documents/document"
        response = requests.get(url=url, params={"id": id})
        if response.status_code != 200:
            error_data = response.json()
            messagebox.showerror("Ошибка", f"Ошибка {response.status_code}: {error_data.get('detail', 'Неизвестная ошибка')}")
        else:
            result = response.json()
            TextWindow(parent=self, title=result["title"], content=result["text"])

class TextWindow(tk.Toplevel):
    def __init__(self, parent, title: str, content: str):
        super().__init__(parent)
        self.title(title)
        self.geometry("800x600")
        self.configure(bg="#f5f5f5")

        # Заголовок
        header = tk.Label(
            self,
            text=title,
            font=("Segoe UI", 18, "bold"),
            fg="#333333",
            bg="#f5f5f5",
            wraplength=760,
            justify="center"
        )
        header.pack(pady=(10, 10))

        # Прокручиваемое текстовое поле
        text_box = scrolledtext.ScrolledText(
            self,
            wrap=tk.WORD,
            font=("Consolas", 12),
            bg="#ffffff",
            fg="#222222",
            relief="flat",
            padx=10,
            pady=10
        )
        text_box.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        # Вставляем текст
        text_box.insert("1.0", content)
        text_box.config(state="disabled")  # делаем поле нередактируемым

        # Кнопка закрытия
        close_btn = tk.Button(
            self,
            text="Закрыть",
            font=("Arial", 12),
            bg="#ff6666",
            fg="white",
            padx=20,
            pady=5,
            relief="flat",
            command=self.destroy
        )
        close_btn.pack(pady=(0, 15))






