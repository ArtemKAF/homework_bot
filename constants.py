import os

from dotenv import load_dotenv

load_dotenv()


PRACTICUM_TOKEN = str(os.getenv("PRACTICUM_TOKEN"))
TELEGRAM_TOKEN = str(os.getenv("TELEGRAM_TOKEN"))
TELEGRAM_CHAT_ID = str(os.getenv("TELEGRAM_CHAT_ID"))

RETRY_PERIOD = 600
TIMEOUT = 15
ENDPOINT = "https://practicum.yandex.ru/api/user_api/homework_statuses/"
HEADERS = {"Authorization": f"OAuth {PRACTICUM_TOKEN}"}

HOMEWORK_VERDICTS = {
    "approved": "Работа проверена: ревьюеру всё понравилось. Ура!",
    "reviewing": "Работа взята на проверку ревьюером.",
    "rejected": "Работа проверена: у ревьюера есть замечания."
}


if __name__ == "__main__":
    ...
