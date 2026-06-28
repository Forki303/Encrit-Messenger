<p align="center">
  <img src="Encrit.png" alt="Encrit Messenger" width="128" height="128">
</p>

<h1 align="center">Encrit Messenger</h1>

<p align="center">
  Your messages. Your rules.
</p>

<p align="center">
  <a href="README.md"><img src="https://img.shields.io/badge/🇷🇺-Русский-blue" alt="Русский"></a>
  <a href="README_EN.md"><img src="https://img.shields.io/badge/🇬🇧-English-green" alt="English"></a>
</p>

## Возможности

* Шифрование всех сообщений
* Локальный сервер — данные не уходят в облако
* Защита паролем — только люди с паролем могут читать сообщения
* Простой и понятный интерфейс

## Скачивание

1. Перейдите в раздел [Releases](https://github.com/Forki303/Encrit-Messenger/releases).
2. Скачайте нужный файл:
   - **Windows** — `.exe`
   - **Linux** — исполняемый файл (без расширения)
3. Запустите программу.

Ничего дополнительно устанавливать не нужно.

### Альтернатива: сборка вручную

```bash
git clone https://github.com/Forki303/Encrit-Messenger.git
cd Encrit-Messenger
pip install -r requirements.txt
pyinstaller --noconsole --onefile --name "Encrit Messenger" --icon Encrit.png --add-data="Encrit.png:." main.py
```

Готовый файл появится в папке `dist/`.

## Первый запуск

1. Задайте никнейм и пароль в боковой панели.
2. Нажмите **Start Server** чтобы создать чат, либо **Connect** чтобы подключиться к существующему.
3. Общайтесь — все сообщения шифруются автоматически.

## Как это работает

* Сервер запускается на одном из участников.
* Другие подключаются по IP и порту.
* Все сообщения шифруются на стороне отправителя и расшифровываются на стороне получателя.
* Сервер видит только зашифрованные данные — прочитать их без пароля невозможно.

## Безопасность

* Шифрование на базе `PBKDF2` + `HMAC-SHA256`
* Пароль не передаётся по сети
* Сервер не имеет доступа к расшифрованным сообщениям

## Структура проекта

```
├── main.py          # Точка входа
├── gui.py           # Интерфейс (PySide6 / Qt)
├── crypto.py        # Шифрование и расшифровка
├── network.py       # Сетевая часть (клиент/сервер)
├── requirements.txt # Зависимости
├── Encrit.png       # Иконка приложения
└── docs/            # Сайт проекта
```
