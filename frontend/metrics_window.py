import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas as pd
import numpy as np
from math import log2
import requests

# ======================
# ==== МЕТРИКИ =========
# ======================

def precision(retrieved, relevant):
    if not retrieved:
        return 0.0
    return len(set(retrieved) & set(relevant)) / len(retrieved)

def recall(retrieved, relevant):
    if not relevant:
        return 0.0
    return len(set(retrieved) & set(relevant)) / len(relevant)

def average_precision(ranked, relevant):
    """Average Precision для одного запроса"""
    if not relevant:
        return 0.0
    hits, sum_prec = 0, 0.0
    for i, d in enumerate(ranked, start=1):
        if d in relevant:
            hits += 1
            sum_prec += hits / i
    return sum_prec / len(relevant) if relevant else 0.0

def mean_average_precision(results, qrels):
    """MAP — средний AP по всем запросам"""
    aps = []
    for qid, ranked in results.items():
        aps.append(average_precision(ranked, qrels.get(qid, set())))
    return np.mean(aps) if aps else 0.0

def ndcg_at_k(ranked, relevant, k=10):
    def dcg(rel_list):
        return sum((1/log2(i+2)) for i, r in enumerate(rel_list) if r)
    rel_vector = [1 if d in relevant else 0 for d in ranked[:k]]
    ideal_vector = sorted(rel_vector, reverse=True)
    idcg = dcg(ideal_vector)
    return dcg(rel_vector)/idcg if idcg else 0.0


# ======================
# ==== ТЕСТОВЫЕ ДАННЫЕ =
# ======================

documents = {
    1: "яблоко груша банан",
    2: "банан апельсин мандарин",
    3: "кошка собака мышь",
    4: "собака лает кошка спит",
    5: "автомобиль мотор бензин колесо",
    6: "поезд вагон рельсы",
    7: "самолет небо облако",
    8: "молоко хлеб сыр",
    9: "река озеро вода рыба",
    10: "гора снег лед вершина"
}

queries = {
    1: "банан",
    2: "кошка собака",
    3: "поезд",
    4: "вода рыба",
    5: "гора снег"
}

# Эталон релевантности (qrels)
qrels = {
    1: {1, 2},
    2: {3, 4},
    3: {6},
    4: {9},
    5: {10}
}

# Смоделированные результаты поиска (упорядоченные doc_ids)
# results = {
#     1: [2, 1, 3, 4, 5],
#     2: [4, 3, 1, 2, 5],
#     3: [6, 2, 9, 10],
#     4: [9, 1, 3, 7],
#     5: [10, 8, 9, 2]
# }
url = "http://127.0.0.1:8000/search/ask"
result1 = [doc["id"] for doc in requests.get(url=url, params={"message": queries[1]}).json()]
result2 = [doc["id"] for doc in requests.get(url=url, params={"message": queries[2]}).json()]
result3 = [doc["id"] for doc in requests.get(url=url, params={"message": queries[3]}).json()]
result4 = [doc["id"] for doc in requests.get(url=url, params={"message": queries[4]}).json()]
result5 = [doc["id"] for doc in requests.get(url=url, params={"message": queries[5]}).json()]
results = {1: result1, 
            2: result2, 
            3: result3, 
            4: result4, 
            5: result5}
print(results)


# ======================
# ==== GUI =============
# ======================

class EvaluationWindow(tk.Toplevel):
    def __init__(self, root):
        self.root = root
        super().__init__()
        self.title("Оценка работы поисковой системы")
        self.geometry("1000x700")
        self.configure(bg="#f5f5f5")

        tk.Label(self, text="Оценка качества поиска", font=("Segoe UI", 20, "bold"), bg="#f5f5f5").pack(pady=10)

        tk.Button(self, text="Запустить тест",
                  font=("Arial", 14, "bold"), command=self.run_test).pack(pady=10)

        self.table_frame = tk.Frame(self, bg="#f5f5f5")
        self.table_frame.pack(fill="both", expand=True, padx=10, pady=10)

    def run_test(self):
        df = self.compute_metrics(results, qrels)
        self.show_table(df)
        self.show_confusion_matrix(results, qrels)
        self.show_document_details()

    def compute_metrics(self, results, qrels):
        """Подсчёт Precision, Recall, AP, nDCG для всех запросов"""
        rows = []
        for qid, ranked in results.items():
            rel = qrels.get(qid, set())
            rows.append({
                "Query": qid,
                "Precision": precision(ranked, rel),
                "Recall": recall(ranked, rel),
                "AP": average_precision(ranked, rel),
                "nDCG@10": ndcg_at_k(ranked, rel, 10)
            })

        df = pd.DataFrame(rows).set_index("Query")
        df.loc["MEAN"] = df.mean()
        return df

    def show_table(self, df):
        """Вывод таблицы с метриками"""
        for widget in self.table_frame.winfo_children():
            widget.destroy()

        tk.Label(self.table_frame, text="Результаты теста", font=("Arial", 14, "bold"), bg="#f5f5f5").pack(pady=5)

        tv = ttk.Treeview(self.table_frame, columns=list(df.columns), show="headings", height=8)
        for col in df.columns:
            tv.heading(col, text=col)
            tv.column(col, width=150, anchor="center")

        for idx, row in df.iterrows():
            tv.insert("", "end", iid=str(idx),
                      values=[f"{val:.3f}" for val in row.values])

        tv.pack(fill="x", padx=10, pady=5)

        map_val = mean_average_precision(results, qrels)
        tk.Label(self.table_frame, text=f"Mean Average Precision (MAP): {map_val:.3f}",
                 font=("Arial", 12, "bold"), bg="#f5f5f5").pack(pady=5)

    def show_confusion_matrix(self, results, qrels):
        """Построение матрицы ошибок (объединённой по всем запросам)"""
        all_tp = all_fp = all_fn = 0

        for qid, ranked in results.items():
            rel = qrels.get(qid, set())
            retrieved = set(ranked)
            tp = len(retrieved & rel)
            fp = len(retrieved - rel)
            fn = len(rel - retrieved)
            all_tp += tp
            all_fp += fp
            all_fn += fn

        # Матрица 2x2
        confusion = np.array([[all_tp, all_fp],
                              [all_fn, 0]])  # TN не имеет смысла здесь

        fig, ax = plt.subplots(figsize=(3,3))
        ax.imshow(confusion, cmap="Blues")
        ax.set_xticks([0,1])
        ax.set_yticks([0,1])
        ax.set_xticklabels(["Релевант", "Нерелевант"])
        ax.set_yticklabels(["Релевант", "Нерелевант"])
        ax.set_xlabel("Истинное значение")
        ax.set_ylabel("Предсказано системой")

        for (i, j), val in np.ndenumerate(confusion):
            ax.text(j, i, f"{val}", ha="center", va="center", color="black", fontsize=12)

        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=self.table_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(side="right", padx=10, pady=10)

    
    def show_document_details(self):
        """Отображение информации о запросах, релевантных документах и результатах системы"""
        details_frame = tk.Frame(self.table_frame, bg="#f5f5f5")
        details_frame.pack(side="left", fill="both", expand=True, padx=10)

        tk.Label(details_frame, text="Запросы и релевантные документы", font=("Arial", 14, "bold"), bg="#f5f5f5").pack(pady=5)

        # Создание таблицы с прокруткой
        columns = ["Запрос", "Релевантные документы", "Результаты системы"]
        tree = ttk.Treeview(details_frame, columns=columns, show="headings", height=10)

        tree.heading("Запрос", text="Запрос")
        tree.heading("Релевантные документы", text="Релевантные документы")
        tree.heading("Результаты системы", text="Результаты системы")

        # Прокрутка
        scrollbar = ttk.Scrollbar(details_frame, orient="vertical", command=tree.yview)
        tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

        tree.pack(fill="both", expand=True)

        # Заполнение таблицы
        for qid, query in queries.items():
            rel_docs = ", ".join(map(str, qrels.get(qid, [])))
            results_docs = ", ".join(map(str, results.get(qid, [])))
            tree.insert("", "end", values=(query, rel_docs, results_docs))


if __name__ == "__main__":
    app = EvaluationWindow("root")
    app.mainloop()
