FROM python:3.10

WORKDIR /app

COPY  . .
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8051

CMD uvicorn main:app --host=0.0.0.0  --port 8051