#FROM python:latest
#FROM python:3.9.6-alpine
FROM 980e9fce048c
#SHELL ["/bin/bash", "-c"]
#RUN /usr/local/bin/python -m pip install --upgrade pip
RUN python -m pip install --upgrade pip
#RUN /usr/local/bin/python --version
RUN python --version
#RUN pip install setuptools==58
ENV PYTHONUNBUFFERED 1

RUN mkdir adifect-app
WORKDIR adifect-app
#ENV VIRTUAL_ENV=/adifect-app/venv
#RUN python3 -m venv $VIRTUAL_ENV

ADD . /adifect-app
RUN addgroup -S adifect-app && adduser -S adifect-app -G adifect-app
RUN pip install --no-cache-dir -r requirements.txt && \
        pip install gunicorn && \
        pip install telnyx

RUN chmod +x gunicorn.sh
EXPOSE 8000
ENTRYPOINT ["./gunicorn.sh"]
