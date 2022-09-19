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

2. Cоздать и активировать виртуальное окружение:

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
3. Установить зависимости из файла requirements.txt:

```bash
python -m pip install --upgrade pip
```

```bash
pip install -r requirements.txt
```

4. Выполнить миграции:

```bash
python manage.py migrate
```

5. Запустить проект:

```bash
python manage.py runserver
```

## Системные требования

python==3.7.0

Django==2.2.16

mixer==7.1.2

Pillow==8.3.1

pytest==6.2.4

pytest-django==4.4.0

pytest-pythonpath==0.7.3

requests==2.26.0

six==1.16.0

sorl-thumbnail==12.7.0

Faker==12.0.1
