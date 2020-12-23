#docker build -t address_api_web .

docker run -d -p 8000:8000 address_api_web:latest python manage.py runserver 0.0.0.0:8000