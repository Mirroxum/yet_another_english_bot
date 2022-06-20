import logging
import os
import sys
from http import HTTPStatus

import requests
from dotenv import load_dotenv
from telegram.ext import Updater, MessageHandler, CommandHandler, Filters
from telegram import TelegramError

from self_exception import (JSONError, TGError,
                            RequestError, HTTPStatusNotOK)

load_dotenv()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(stream=sys.stdout)
handler.setFormatter(logging.Formatter(
    '%(asctime)s - %(lineno)d.%(levelname)s(%(funcName)s) - %(message)s'))
logger.addHandler(handler)

BOT_TOKEN = os.getenv('BOT_TOKEN')
URL = 'https://dictionary.skyeng.ru/api/public/v1/words/search'


def get_api_answer_search(search_word):
    """Делает запрос к API-сервиса.
    В качестве параметра функция получает слово с для поиска.
    В случае успешного запроса возвращает ответ API, преобразовав его
    из формата JSON к типам данных Python."""
    try:
        response = requests.get(URL, params={'search': search_word})
        if response.status_code != HTTPStatus.OK:
            raise HTTPStatusNotOK(
                f'API вернул код отличный от 200: {response.status_code}!')
        response_word = response.json()
    except HTTPStatusNotOK as e:
        raise HTTPStatusNotOK(
            'API вернул код отличный от 200',
            f'Статус: {response.status_code}!') from e
    except ConnectionError as e:
        raise ConnectionError(
            'Произошла ошибка при попытке запроса ',
            f'к API c параметром: {search_word}') from e
    except requests.exceptions.JSONDecodeError as e:
        raise JSONError(
            f'Сбой декодирования JSON из ответа: {response} ',
            f'с параметром: {search_word}') from e
    except requests.exceptions.RequestException as e:
        raise RequestError(
            'Ошибка вызванная request. При попытке сделать',
            f'запрос с параметром: {search_word}') from e
    else:
        logger.info('Ответ от сервера получен')
        return response_word


def check_response(response, seach_word):
    """Проверяет ответ API на корректность.
    Если ответ API соответствует ожиданиям,
    то функция возвращает словарь для вывода.
    """
    try:
        if not response:
            return False
        response_into = response.pop(0)
        response_first_meanings = response_into.get('meanings').pop(0)
        while (response_into.get('text') != seach_word
               and response_first_meanings.get(
                'translation').get('text') != seach_word):
            response_first_meanings = response_into.get('meanings').pop(0) 
        answer = {'id': response_first_meanings.get('id'),
                  'image': 'https:' + response_first_meanings.get('imageUrl'),
                  'voice': response_first_meanings.get('soundUrl'),
                  'transcription': response_first_meanings.get(
                    'transcription'),
                  'en_word': response_into.get('text'),
                  'ru_word': response_first_meanings.get(
                    'translation').get('text')}
        if None in answer.values():
            raise IndexError()
        return answer
    except TypeError as e:
        raise TypeError('Неверный тип переменных') from e
    except IndexError as e:
        raise IndexError('Ошибка при назначении переменных') from e


def send_translate_word(update, context):
    """Принимает сообщение.
    Оптравляет найденный вариант перевода"""
    try:
        chat = update.effective_chat
        response = check_response(get_api_answer_search(
            update.message.text), update.message.text)
        if not response:
            context.bot.send_message(chat.id, 'Я не знаю такого слова')
        else:
            transcription = response.get('transcription')
            en_word = response.get('en_word')
            ru_word = response.get('ru_word')
            message = f'{en_word} - [{transcription}] - {ru_word}'
            context.bot.send_photo(chat.id, response.get('image'))
            context.bot.send_voice(chat.id, response.get('voice'))
            context.bot.send_message(chat.id, message)
    except TelegramError as e:
        raise TGError(
            f'Cбой Telegram при отправке сообщения "{message}".') from e


def wake_up(update, context):
    """Стартовая функция. Отправляет сообщение - приветствие"""
    chat = update.effective_chat
    name = update.message.chat.first_name
    context.bot.send_message(
        chat_id=chat.id,
        text=(f'Привет, {name}. Пришли мне незнакомое тебе слово '
              'и я попробую его перевести'))


def check_tokens():
    """Проверяет доступность переменных окружения."""
    return BOT_TOKEN


def main():
    """Основная функцияю"""
    if not check_tokens():
        logger.critical('Отсутствуют обязательные переменные окружения')
        sys.exit('Отсутствуют обязательные переменные окружения')
    updater = Updater(token=BOT_TOKEN)
    logger.info('Инициализация прошла успешно')
    try:
        updater.dispatcher.add_handler(CommandHandler('start', wake_up))
        updater.dispatcher.add_handler(
            MessageHandler(Filters.text, send_translate_word))
        updater.start_polling(poll_interval=2.0)
        updater.idle()
    except Exception as error:
        message = (f'Сбой в работе программы. Ошибка:{error}')
        logger.error(message)


if __name__ == '__main__':
    main()
