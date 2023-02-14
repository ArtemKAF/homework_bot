class BotSendMessageException(Exception):
    """Класс исключения ошибки отправки сообщения телеграм ботом."""

    pass


class NotFoundEndpointException(Exception):
    """Класс исключения недоступности Endpoint."""

    pass


class NotOkStatusCodeException(Exception):
    """Класс исключения статус кода отличного от 200."""

    pass
