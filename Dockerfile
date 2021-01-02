FROM python:3

WORKDIR /app
COPY . /app
RUN pip install -r /app/requirements.txt
ENTRYPOINT [ "python", "/app/cube.py" ]
#CMD [ "python", "/app/cube.py" ]
