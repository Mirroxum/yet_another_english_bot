class JSONError(Exception):
    """Ошибка обработки JSON."""

    pass


class RequestError(Exception):
    """Ошибка Request."""

    pass


class HTTPStatusNotOK(Exception):
    """API вернул код отличный от 200."""

    pass


class TGError(Exception):
    """Ошибка пакета python-telegram-bot."""

    pass

class DetectError(Exception):
    """Ошибка при определении языка текста."""

    pass

