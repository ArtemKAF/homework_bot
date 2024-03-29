import logging
import logging.config
import time
from http import HTTPStatus

import requests
import telegram

import exceptions
from conflogging import LOGGING_CONFIG
from constants import (ENDPOINT, HEADERS, HOMEWORK_VERDICTS, PRACTICUM_TOKEN,
                       RETRY_PERIOD, TELEGRAM_CHAT_ID, TELEGRAM_TOKEN, TIMEOUT)

logging.config.dictConfig(LOGGING_CONFIG)

logger = logging.getLogger(__name__)
logger.debug("Ведение журнала настроено.")


def check_tokens(tokens):
    """Проверяет наличие обязательных токенов."""
    result = True
    for token, value in tokens.items():
        if not value or value.isspace():
            logger.critical(
                f"{token} - обязательный токен. Его значение {value} "
                "некорректно."
            )
            result = False
    return result


def send_message(bot, message):
    """Отправляет сообщение в чат пользователя Telegram."""
    try:
        logger.debug(f"Бот отправляет сообщение: {message}")
        bot.send_message(TELEGRAM_CHAT_ID, message)
    except Exception as error:
        logger.error(error)
        raise exceptions.BotSendMessageException(
            f"При попытке отправить телеграм ботом сообщения: {message}, "
            f"произошла ошибка {error}."
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
    except requests.exceptions.Timeout as error:
        raise exceptions.RequestAPIYandexPracticumTimeout(
            f"Превышен лимит выполнения запроса: {error}"
        )
    except requests.exceptions.ConnectionError as error:
        raise exceptions.RequestAPIYandexPracticumConnectionError(
            f"Ошибка соединения с API: {error}"
        )
    except requests.RequestException as error:
        raise exceptions.RequestAPIYandexPracticumException(
            f"Непредвиденные ошибки в получении ответа: {error}"
        )
    if response.status_code == HTTPStatus.NOT_FOUND:
        raise exceptions.NotFoundEndpointException(
            f"Эндпоинт {ENDPOINT} не найден. "
            f"URL: {response.url}\nЗаголовки: {response.headers}\n"
            f"Текст ответа: {response.text}\n"
            f"Код ответа: {response.status_code}"
        )
    if response.status_code != HTTPStatus.OK:
        raise exceptions.NotOkStatusCodeException(
            f"Статус-код ответа от {ENDPOINT} отличен от 200.\n"
            f"URL: {response.url}\nЗаголовки: {response.headers}\n"
            f"Текст ответа: {response.text}\n"
            f"Код ответа: {response.status_code}"
        )
    return response.json()


def check_response(response):
    """Проверяет результат ответа на запрос к API Yandex Practicum."""
    if not response:
        raise TypeError("Нет ответа от API")
    if not isinstance(response, dict):
        raise TypeError(
            "Информация в ответе предоставлена не в виде словаря"
        )
    if response.get("homeworks") is None:
        raise KeyError(
            "В ответе отсутствует информация о домашних работах."
        )
    if not isinstance(response.get("homeworks"), list):
        raise TypeError(
            "Информация о домашних работах в ответе предоставлена "
            "не в виде списка."
        )


def parse_status(homework):
    """Парсинг результата проверки домашнего задания."""
    if not homework.get("homework_name"):
        raise KeyError("В информации о домашней работе отсутствует ее имя.")
    homework_name = homework.get("homework_name")
    if not homework.get("status"):
        raise KeyError("В информации о домашней работе отсутствует статус")
    if homework.get("status") not in HOMEWORK_VERDICTS.keys():
        raise ValueError(
            f"Статус проверки домашнего задяния: {homework.get('status')} "
            "не соответствует ожидаемым."
        )
    verdict = HOMEWORK_VERDICTS.get(homework.get("status"))
    return f"Изменился статус проверки работы \"{homework_name}\". {verdict}"


def warning_telegram(message, last_message, bot):
    """Отправка сообщения в телеграм, отличного от предудущего."""
    if message != last_message:
        last_message = message
        send_message(bot, message)


def main():
    """Основная логика работы бота."""
    tokens = {
        "PRACTICUM_TOKEN": PRACTICUM_TOKEN,
        "TELEGRAM_TOKEN": TELEGRAM_TOKEN,
        "TELEGRAM_CHAT_ID": TELEGRAM_CHAT_ID,
    }
    exit() if not check_tokens(tokens) else None

    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())

    logger.info("Бот готов к работе и запущен.")
    send_message(bot, "Начинаю работу.")

    last_message = ""

    while True:
        try:
            response = get_api_answer(timestamp)
            check_response(response)
            timestamp = response.get("current_date")
            for homework in response.get("homeworks"):
                message = parse_status(homework)
                logger.info(message)
                warning_telegram(message, last_message, bot)
        except exceptions.BotSendMessageException as error:
            logger.error(error)
        except exceptions.RequestAPIYandexPracticumTimeout as error:
            logger.warning(error)
            warning_telegram(error, last_message, bot)
        except exceptions.RequestAPIYandexPracticumConnectionError as error:
            logger.critical(error)
            warning_telegram(error, last_message, bot)
        except exceptions.RequestAPIYandexPracticumException as error:
            logger.error(error)
            warning_telegram(error, last_message, bot)
        except (
            exceptions.NotFoundEndpointException,
            exceptions.NotOkStatusCodeException
        ) as error:
            message = f"Нежелательный статус ответа от API: {error}"
            logger.error(message)
            warning_telegram(message, last_message, bot)
        except Exception as error:
            message = f"Сбой в работе программы: {error}"
            logger.error(message)
            warning_telegram(message, last_message, bot)
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
