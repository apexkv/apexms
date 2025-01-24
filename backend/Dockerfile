FROM python:3.12.8-alpine3.20

ENV PYTHONUNBUFFERED 1

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . /app/

RUN python manage.py makemigrations

RUN python manage.py migrate

EXPOSE 14186

CMD ["python", "manage.py", "runserver"]