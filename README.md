Клонируем проект:
git clone https://github.com/TheFluxx/hw05_final.git

Переходим в папку с проектом:
cd hw05_final/yatube

Устанавливаем виртуальное окружение:
python -m venv venv

Активируем виртуальное окружение:
source venv/Scripts/activate

Для деактивации виртуального окружения выполним (после работы):
deactivate

Устанавливаем зависимости:
python -m pip install --upgrade pip
pip install -r requirements.txt

Применяем миграции:
python yatube/manage.py makemigrations
python yatube/manage.py migrate

Создаем супер пользователя:
python yatube/manage.py createsuperuser

Запускаем проект:
python manage.py runserver
