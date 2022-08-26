FROM python:3.9

WORKDIR /opt

COPY requirements.txt requirements.txt

RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . /opt/app/

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80"]
