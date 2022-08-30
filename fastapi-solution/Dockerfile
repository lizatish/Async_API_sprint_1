FROM python:3.9

WORKDIR /opt

COPY requirements.txt requirements.txt

RUN pip install --no-cache-dir --upgrade pip && pip install -r requirements.txt

COPY . /opt/app/

ENV PYTHONPATH "${PYTHONPATH}:/opt/app/src/"

CMD ["uvicorn", "app.src.main:app", "--host", "0.0.0.0", "--port", "8000"]
