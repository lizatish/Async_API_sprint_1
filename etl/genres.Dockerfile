FROM python:3.9

WORKDIR /opt

COPY requirements.txt requirements.txt

RUN pip install --no-cache-dir --upgrade pip && pip install -r requirements.txt

COPY . /opt/app/
ENV PYTHONPATH "${PYTHONPATH}:/opt/app/"

EXPOSE 8000
ENTRYPOINT ["python", "app/genres/main.py"]
