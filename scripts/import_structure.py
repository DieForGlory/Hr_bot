import os
import urllib.request


def download_dejavu():
    os.makedirs("assets/fonts", exist_ok=True)
    os.makedirs("data/pdfs", exist_ok=True)

    font_url = "https://raw.githubusercontent.com/fpdf-project/fpdf2/master/test/fonts/DejaVuSans.ttf"
    font_path = "assets/fonts/DejaVuSans.ttf"

    if not os.path.exists(font_path):
        try:
            urllib.request.urlretrieve(font_url, font_path)
            print("Файл шрифта успешно загружен.")
        except Exception as e:
            print(f"Ошибка при скачивании: {e}")


if __name__ == "__main__":
    download_dejavu()