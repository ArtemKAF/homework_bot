class BotSendMessageException(Exception):
    """Класс исключения ошибки отправки сообщения телеграм ботом."""

    pass


class RequestAPIYandexPracticumTimeout(Exception):
    """Класс исключения таймаута запроса к API Yandex Practicum."""

    pass


class RequestAPIYandexPracticumConnectionError(Exception):
    """Класс исключения ошибки соединения с API Yandex Practicum."""

    pass


class RequestAPIYandexPracticumException(Exception):
    """Класс исключения непредвиденной ошибки запроса API Yandex Practicum."""

    pass


class NotFoundEndpointException(Exception):
    """Класс исключения недоступности Endpoint."""

    pass


class NotOkStatusCodeException(Exception):
    """Класс исключения статус кода отличного от 200."""

    pass
