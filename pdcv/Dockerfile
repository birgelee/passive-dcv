FROM python:3.11-bookworm


WORKDIR /code



COPY ./requirements.txt /code/requirements.txt


RUN apt update
RUN apt install python3 python3-venv libaugeas0 -y

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

RUN ln -s /opt/certbot/bin/certbot /usr/bin/certbot


COPY ./app /code/app

# VOLUME /code/available_perspectives.yaml

EXPOSE 80

CMD ["fastapi", "run", "app/main.py", "--workers", "30", "--proxy-headers",  "--port", "80"]

