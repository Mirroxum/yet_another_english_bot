# yet_another_english_bot

Бот-словарь для Telegram. Можно отправить слово или предложение на русском или английском языке. В ответ пришлёт перевод, визуализацию и аудо-файл с произношением.

Потестировать можно в Telegram:
@yet_another_english_bot

###Установка
Клонируем репозиторий на локальную машину:

```
git clone git@github.com:Mirroxum/yet_another_english_bot.git
```

Создаем виртуальное окружение:

```
python -m venv venv
```

Устанавливаем зависимости:

```
pip install -r requirements.txt
```
После создайте в корневой директории файл с названием "```.env```" и поместите в него:
```
BOT_TOKEN = "Ваш бот-токен"

```
