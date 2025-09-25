# Проект YaMDb
YaMDb - приложение сбора отзывов пользователей на произведения. Произведения делятся на категории, также произведению может быть присвоен жанр. Ознакомившись с произведением, пользователи могут оставить текстовый отзыв и оценку из которой формируется рейтинг. Пользователи могут оставлять комментарии к отзывам. В приложении реализовано разделение ролей пользователей, что позволяет разграничивать доступ.
Через бэкенд проекта (API) можно управлять данными подключив к ресурсу фронтенд приложение, мобильное приложение или чат-бота.

---

## Технологический стек

- Python
- Django
- Django REST Framework
- Simple JWT

---

## Как запустить проект:
Клонировать репозиторий и перейти в него в командной строке:
```
git clone https://github.com/shibaevvv/api-yamdb
```
```
cd api_yamdb
```
Cоздать и активировать виртуальное окружение:
```
python3 -m venv venv | python -m venv venv
```
```
source env/bin/activate | source venv/Scripts/activate
```
```
python3 -m pip install --upgrade pip | python -m pip install --upgrade pip
```
Установить зависимости из файла requirements.txt:
```
pip install -r requirements.txt
```
Перейти в каталог api_yamdb и выполнить миграции:
```
python3 manage.py migrate | python manage.py migrate
```
Запустить проект:
```
python3 manage.py runserver | python manage.py runserver
```

---

## Примеры запросов:

### Регистрация нового пользователя
#### POST
```
/api/v1/auth/signup/
```
```
{
  "email": "user@example.com",
  "username": "string"
}
```
Ответ:
```
{
  "email": "string",
  "username": "string"
}
```


### Получение списка всех произведений
#### GET
```
/api/v1/titles/
```
Ответ:
```
{
  "count": 0,
  "next": "string",
  "previous": "string",
  "results": [
    {
      "id": 0,
      "name": "string",
      "year": 0,
      "rating": 0,
      "description": "string",
      "genre": [
        {
          "name": "string",
          "slug": "string"
        }
      ],
      "category": {
        "name": "string",
        "slug": "string"
      }
    }
  ]
}
```

### Добавление жанра администратором
#### POST
```
/api/v1/genres/
```
```
{
  "name": "string",
  "slug": "string"
}
```
Ответ:
```
{
  "name": "string",
  "slug": "string"
}
```

## Полная документация
Подробная документация в формате openapi доступны в файле проекта api-yamdb/api_yamdb/static/redoc.yaml.
Также в браузере по адресу http://localhost:port/redoc/ (необходимо запустить проект).

---

### Авторы

- [Владимир Шибаев](https://github.com/shibaevvv/api-yamdb)
- [Владейщикова Полина](https://github.com/name0692)
- [Онищенко Александр](https://github.com/Alex-on1)