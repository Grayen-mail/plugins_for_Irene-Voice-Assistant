# Text normalizer plugin for russian TTS
# required online and access to any AI model
# author: Sergey Savin aka Grayen
"""
    Подготовка текста к озвучиванию на русских моделях TTS.
Т.к. многие модели либо пропускают некоторые символы (в лучшем случае),
либо останавливаются с генерацией исключения. Производится перевод слов
на русский и замена символов словами.
"""
import os
from pyexpat.errors import messages

import logging
import re
import openai

from vacore import VACore

modname = os.path.basename(__file__)[:-3]  # calculating modname
logger = logging.getLogger(__name__)


# функция на старте
def start(core: VACore):
    manifest = {
        "name": "Normalizer text with AI",
        "version": "0.1",
        "require_online": True,

        "normalizer": {
            "prepare_with_AI": (init, normalize)  # первая функция инициализации, вторая - реализация нормализации
        },

        "description": "Подготовка текста к озвучиванию на русских моделях TTS.\n"
                       "Замена символов и перевод на русский\n",

        "options_label": {
            "apiKey": "API-ключ",
            "apiBaseUrl": "URL для подключения",
            "model": "ID модели",
        },

        "default_options": {
            "apiKey": "",
            "apiBaseUrl": "https://api.vsegpt.ru/v1",
            "model": "openai/gpt-4o-mini",
        },

    }
    return manifest


def start_with_options(core: VACore, manifest: dict):
    pass


def init(core: VACore):
    pass


def normalize(core: VACore, text: str):
    """
    Подготовка текста к озвучиванию
    """
    logger.debug(f"Текст до преобразований: {text}")

    # Если в строке только кириллица и пунктуация - оставляем как есть
    if not bool(re.search(r'[^,.?!;:"() ЁА-Яа-яё]', text)):
        logger.debug(f"Текст не требует нормализации: {text}")
        return text

    options = core.plugin_options(modname)

    if core.isOnline is False:
        logger.error("Для работы плагина требуется подключение к интернету. Текст не нормализован.")
        return text

    if options.get("apiKey") is None:
        logger.error("API-ключ не указан. Текст не нормализован.")
        return text

    if options.get("apiBaseUrl") is None:
        options["apiBaseUrl"] = "https://api.vsegpt.ru/v1"
        logger.info("Подключаемся к серверу по умолчанию: " + options["apiBaseUrl"])

    if options.get("model") is None:
        options["model"] = "openai/gpt-4o-mini"
        logger.info("Используемая модель по умолчанию: " + options["model"])

    openai.api_key = options["apiKey"]
    openai.api_base = options["apiBaseUrl"]

    messages = []
    messages.append({"role": "system",
                     "content": '''Ты выполняешь функцию подготовки текста для произношения на модели Text-To-Speach, которая понимает только русский текст.
                            Отвечай только на русском языке.
                            Если встретятся фразы на английском языке - переведи их на русский. 
                            Если встретятся аббревиатуры на английском языке преобразуй их в произношение на русском, например PC преобразовать в ПиСи, GT преобразовать в ДжиТи.
                            Все цифры преобразовать в слова.
                            Необходимо преобразовать текст в соответствии с правилами русского языка. Например, если в тексте встретится "от пятнадцать до двадцать один градус" изменить на "от пятнадцати до двадцати одного градуса", "ему 22 лет" изменить на "ему 22 года".'''})
    messages.append({"role": "user", "content": text})
    try:
        response = openai.ChatCompletion.create(
            model=options["model"],
            messages=messages,
            temperature=0.1,
            n=1,
            max_tokens=2000,
        )
    except Exception as e:
        logger.error(f"Ошибка при работе с OpenAI: {e}")
        return text

    if response.choices[0].message.content is not None:
        logger.debug(f"Ответ от OpenAI: {response.choices[0].message.content}")
        return response["choices"][0]["message"].content
    else:
        logger.error("Не удалось получить ответ от OpenAI")
        return text


if  __name__ == "__main__":
    print("This module is a plugin for Irene Voice Assistant and should be placed in the `plugins` folder instead of running directly")
