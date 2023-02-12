import logging
import sys
import time
from http import HTTPStatus

import requests
import telegram

import exceptions
from constants import (ENDPOINT, HEADERS, HOMEWORK_VERDICTS, PRACTICUM_TOKEN,
                       RETRY_PERIOD, TELEGRAM_CHAT_ID, TELEGRAM_TOKEN, TIMEOUT)

log_handler = logging.StreamHandler(sys.stdout)
log_handler.setFormatter(
    logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(log_handler)


def check_tokens(TOKENS):
    """Проверяет наличие обязательных токенов."""
    for token, value in TOKENS.items():
        if not value or value.isspace():
            raise ValueError(
                f"{token} - обязательный токен. Его значение {value} "
                "некорректно."
            )


def send_message(bot, message):
    """Отправляет сообщение в чат пользователя Telegram."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logger.debug(f"Бот отправил сообщение: {message}")
    except Exception as error:
        logger.error(
            f"Сбой при отправке сообщения ботом: {error}"
        )


def get_api_answer(timestamp: int):
    """Отправляет запрос к API Yandex Practicum."""
    try:
        response = requests.get(
            url=ENDPOINT,
            headers=HEADERS,
            params={"from_date": timestamp},
            timeout=TIMEOUT,
        )
        logger.debug(
            f"Выполнен запрос к {ENDPOINT} \n\t c параметром from_date: "
            f"{timestamp}.\n Результат запроса: {response.text} \n"
        )
        if response.status_code == HTTPStatus.NOT_FOUND:
            raise exceptions.NotFoundEndpointException(
                f"Эндпоинт {ENDPOINT} не найден. "
                f"Код ответа: {response.status_code}"
            )
        if response.status_code != HTTPStatus.OK:
            raise exceptions.NotOkStatusCodeException(
                f"Статус-код ответа от {ENDPOINT} отличен от 200. "
                f"Код ответа: {response.status_code}"
            )
        return response.json()
    except requests.exceptions.Timeout as error:
        logger.warning(f"Превышен лимит выполнения запроса: {error}")
    except requests.exceptions.ConnectionError as error:
        logger.critical(f"Ошибка соединения с API: {error}")
    except requests.RequestException as error:
        logger.error(f"Непредвиденные ошибки в получении ответа: {error}")


def check_response(response):
    """Проверяет результат ответа на запрос к API Yandex Practicum."""
    if not response:
        raise TypeError("Нет ответа от API")
    elif not isinstance(response, dict):
        raise TypeError(
            "Инормация в ответе предоставлена не в виде словаря"
        )
    elif response.get("homeworks") is None:
        raise KeyError(
            "В ответе отсутствует информация о домашних работах."
        )
    elif not isinstance(response.get("homeworks"), list):
        raise TypeError(
            "Информация о домашних работах в ответе предоставлена "
            "не в виде списка."
        )


def parse_status(homework):
    """Парсинг результата проверки домашнего задания."""
    if not homework.get("homework_name"):
        raise KeyError("В информации о домашней работе отсутствует ее имя.")
    homework_name = homework.get("homework_name")
    if (not homework.get("status")
            or (homework.get("status") not in HOMEWORK_VERDICTS.keys())):
        raise KeyError(
            "В информации о домашней работе отсутствует статус или его "
            "значение не соответствует ожидаемым."
        )
    verdict = HOMEWORK_VERDICTS.get(homework.get("status"))
    return f"Изменился статус проверки работы \"{homework_name}\". {verdict}"


def warning_telegram(message, telegram_messages, bot):
    """Отправка нового сообщения в телеграм."""
    if message not in telegram_messages:
        send_message(bot, message)
        telegram_messages.add(message)


def main():
    """Основная логика работы бота."""
    TOKENS = {
        "PRACTICUM_TOKEN": PRACTICUM_TOKEN,
        "TELEGRAM_TOKEN": TELEGRAM_TOKEN,
        "TELEGRAM_CHAT_ID": TELEGRAM_CHAT_ID,
    }

    try:
        check_tokens(TOKENS)
    except ValueError as error:
        logger.critical(error)
        exit()

    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())

    logger.info("Бот готов к работе и запущен.")
    send_message(bot, "Начинаю работу.")

    telegram_messages = set()
    while True:
        try:
            response = get_api_answer(timestamp)
            check_response(response)
            timestamp = response.get("current_date")
            for homework in response.get("homeworks"):
                result = parse_status(homework)
                logger.info(result)
                warning_telegram(result, telegram_messages, bot)
        except (
            exceptions.NotFoundEndpointException,
            exceptions.NotOkStatusCodeException
        ) as error:
            message = f"Нежелательный статус ответа от API: {error}"
            logger.error(message)
            warning_telegram(message, telegram_messages, bot)
        except Exception as error:
            message = f"Сбой в работе программы: {error}"
            logger.error(message)
            warning_telegram(message, telegram_messages, bot)
        time.sleep(RETRY_PERIOD)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Работа ассистента останавливается...")
        exit()
    except Exception as error:
        logger.critical(f"Ошибка верхнего уровня: {error}")
        exit()
