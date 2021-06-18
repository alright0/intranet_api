FROM python:3.9.5
RUN apt-get update
RUN apt-get upgrade -y
RUN apt-get install -y python3-pip
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
ENV TZ Europe/Moscow
EXPOSE 8989
ENTRYPOINT ["python3"]
CMD ["manage.py"]
