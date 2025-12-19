# Файл: main.py
import logging
from gui import App

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(message)s', datefmt='%H:%M:%S')

if __name__ == "__main__":
    app = App()
    app.run()