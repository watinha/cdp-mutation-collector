FROM python:3.13.2-alpine3.21

WORKDIR ./

RUN pip3 install -U selenium

CMD ["ash"]
