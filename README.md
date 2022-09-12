# Yatube - платформа для публикации блогов

Проект разработан по MVT архитектуре, используется пагинация постов и кэширование. Регистрация реализована с верификацией данных, возможна смена и восстановление пароля через почту. 

## Инструкция по установке и запуску проекта

1. Клонировать репозиторий и перейти в него в командной строке:

```bash
git clone https://github.com/IrinaPolt/hw05_final.git
```

```bash
cd api_yamdb
```

Cоздать и активировать виртуальное окружение:

```bash
python -m venv venv
```
Linux и MacOS:
```bash
source env/bin/activate
```
Windows:
```
source venv/Scripts/activate
```
Установить зависимости из файла requirements.txt:

```bash
python -m pip install --upgrade pip
```

```bash
pip install -r requirements.txt
```

Выполнить миграции:

```bash
python manage.py migrate
```

Запустить проект:

```bash
python manage.py runserver
```