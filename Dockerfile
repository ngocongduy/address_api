FROM python:3.8
ENV PYTHONUNBUFFERED=1
RUN mkdir /code
WORKDIR /code
COPY requirements.txt /code/
RUN pip install -r requirements.txt
COPY . /code/
# Assure a logs folder in working dir otherwise the server will fail to run
RUN mkdir ./logs
RUN ls