import logging
import os
import sys
from http import HTTPStatus

import requests
from dotenv import load_dotenv
from telegram.ext import Updater, MessageHandler, CommandHandler, Filters
from telegram import TelegramError

from self_exception import (JSONError, TGError,
                            RequestError, HTTPStatusNotOK,
                            DetectError)
from utils import detect

load_dotenv()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(stream=sys.stdout)
handler.setFormatter(logging.Formatter(
    '%(asctime)s - %(lineno)d.%(levelname)s(%(funcName)s) - %(message)s'))
logger.addHandler(handler)

BOT_TOKEN = os.getenv('BOT_TOKEN')
URL_SKYENG = 'https://dictionary.skyeng.ru/api/public/v1/words/search'
URL_GOG_TRANSLATE = 'https://translate.googleapis.com/translate_a/single'


def get_api_answer_search(url, params):
    """Делает запрос к API-сервиса.
    В качестве параметра функция получает слово с для поиска.
    В случае успешного запроса возвращает ответ API, преобразовав его
    из формата JSON к типам данных Python."""
    try:
        response = requests.get(url, params=params)
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
            f'к API c параметрами: {params}') from e
    except requests.exceptions.JSONDecodeError as e:
        raise JSONError(
            f'Сбой декодирования JSON из ответа: {response} ',
            f'с параметрами: {params}') from e
    except requests.exceptions.RequestException as e:
        raise RequestError(
            'Ошибка вызванная request. При попытке сделать',
            f'запрос с параметрами: {params}') from e
    else:
        logger.info('Ответ от сервера получен.')
        return response_word


def send_message(update, context, text=False, foto=False, voice=False):
    """Отправляет сообщения в ТГ"""
    try:
        chat = update.effective_chat
        if foto:
            context.bot.send_photo(chat.id, foto)
        if voice:
            context.bot.send_voice(chat.id, voice)
        if text:
            context.bot.send_message(chat.id, text)
    except TelegramError as e:
        raise TGError('Cбой Telegram при отправке сообщения.') from e


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
        if (response_into.get('text') != seach_word.lower()
            and response_first_meanings.get(
                'translation').get('text') != seach_word.lower()):
            for item in response_into.get('meanings'):
                if item.get('translation').get('text') == seach_word.lower():
                    response_first_meanings = item
                    continue
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
    search_word = update.message.text
    response = check_response(get_api_answer_search(URL_SKYENG,
                                                    {'search': search_word}), search_word)
    if not response:
        send_message(update, context, text='Я не знаю такого слова')
    else:
        transcription = response.get('transcription')
        en_word = response.get('en_word')
        ru_word = response.get('ru_word')
        message = f'{en_word} - [{transcription}] - {ru_word}'
        send_message(update, context,
                     text=message,
                     foto=response.get('image'),
                     voice=response.get('voice'))


def send_translate_sentence(update, context, sl='ru', tl='en'):
    """Переводит текст машинным переводом и отправляет сообщение"""
    params = {
        'client': 'gtx',
        'sl': sl,
        'tl': tl,
        'dt': 't',
        'q': update.message.text}
    data = get_api_answer_search(URL_GOG_TRANSLATE, params)
    message = ''.join(proposal[0] for proposal in data[0])
    send_message(update, context, text=message)


def wake_up(update, context):
    """Стартовая функция. Отправляет сообщение - приветствие"""
    name = update.message.chat.first_name
    message = (f'Привет, {name}. Пришли мне незнакомое тебе слово '
               'или предложение и я попробую его перевести')
    send_message(update, context, text=message)


def check_tokens():
    """Проверяет доступность переменных окружения."""
    return BOT_TOKEN

def check_message(update, context):
    """Проверяем сообщение текст или слово."""
    text = update.message.text.strip()
    if ' ' not in text:
        send_translate_word(update, context)
    else:
        try:
            lang = detect(text)
            if lang == 'ru':
                send_translate_sentence(update, context, sl='ru', tl='en')
            elif lang == 'en':
               send_translate_sentence(update, context, sl='en', tl='ru')
            else:
                raise DetectError() 
        except DetectError as e:
            raise DetectError(f'Ошибка при определении языка текста. Текст:{text}') from e


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
            MessageHandler(Filters.text, check_message))
        updater.start_polling(poll_interval=2.0)
        updater.idle()
    except Exception as error:
        message = (f'Сбой в работе программы. Ошибка:{error}')
        logger.error(message)


if __name__ == '__main__':
    main()
