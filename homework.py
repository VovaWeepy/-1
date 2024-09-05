import logging
import logging.config
import os
import time

import requests
import telegram
from dotenv import load_dotenv

load_dotenv()

#Настройка логирования
LOGGING_CONFIG = {
    'version': 1,
    'handlers': {
        'fileHandler': {
            'class': 'logging.handlers.RotatingFileHandler',
            'formatter': 'myFormatter',
            'filename': 'my_logger.log',
            'maxBytes': 50000000,
            'backupCount': 5,
            'encoding': 'utf-8'}},
    'loggers': {
        'info': {
            'handlers': ['fileHandler'],
            'level': 'INFO'},
        'debug': {
            'handlers': ['fileHandler'],
            'level': 'DEBUG'}},
    'formatters': {
        'myFormatter': {
            'format': '%(asctime)s, %(levelname)s, %(message)s'}}}

logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger('info')
logger = logging.getLogger('debug')
logger.info('Настройка логгирования окончена!')

#Загрузка токенов и идентификаторов
PRAKTIKUM_TOKEN = os.getenv('PRAKTIKUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')

#Эта функция принимает словарь homework, содержащий информацию о домашнем задании.
def parse_homework_status(homework):
    homework_name = homework.get('homework_name')
    status = homework.get('status')
    if homework_name is None or status is None:
        logger.error('Неверный ответ сервера')
        return 'Неверный ответ сервера'
    elif status == 'rejected':
        verdict = 'К сожалению в работе нашлись ошибки.'
    elif status == 'reviewing':
        verdict = 'Работа взята в ревью.'
    else:
        verdict = (
            'Ревьюеру всё понравилось, можно приступать к следующему уроку.')
    return f'У вас проверили работу "{homework_name}"!\n\n{verdict}'

#Эта функция отправляет запрос к API Яндекс.Практикум для получения статусов домашних заданий.
def get_homework_statuses(current_timestamp):
    current_timestamp = current_timestamp or int(time.time())
    url = 'https://praktikum.yandex.ru/api/user_api/homework_statuses/'
    headers = {'Authorization': f'OAuth {PRAKTIKUM_TOKEN}'}
    params = {'from_date': current_timestamp}
    try:
        homework_statuses = requests.get(url, headers=headers, params=params)
        return homework_statuses.json()
    except Exception as error:
        logger.error(f'Неверный ответ сервера: {error}')
        return {}

#Эта функция отправляет сообщение в Telegram с помощью Telegram Bot API.
def send_message(message, bot_client):
    return bot_client.send_message(chat_id=CHAT_ID, text=message)

#Создается экземпляр Telegram-бота. Запускается бесконечный цикл, который каждые 20 минут (1200 секунд) проверяет статусы домашних заданий.
def main():
    bot_client = telegram.Bot(token=TELEGRAM_TOKEN)
    logger.debug('Бот запущен!')
    current_timestamp = int(time.time())

    while True:
        try:
            new_homework = get_homework_statuses(current_timestamp)
            if new_homework.get('homeworks'):
                send_message(
                    parse_homework_status(
                        new_homework.get('homeworks')[0]), bot_client)
                logger.info('Сообщение отправлено!')
            current_timestamp = new_homework.get(
                'current_date', current_timestamp)
            time.sleep(1200)

        except Exception as error:
            logger.error(f'Бот столкнулся с ошибкой: {error}')
            send_message('Бот столкнулся с ошибкой', bot_client)
            time.sleep(300)


if __name__ == '__main__':
    main()
