FROM python:3.10.12-alpine3.18

COPY requirements.txt /temp/requirements.txt

COPY mailing /mailing

WORKDIR /mailing

EXPOSE 8800

RUN pip3 install -r /temp/requirements.txt
RUN adduser --disabled-password mailing

USER mailing