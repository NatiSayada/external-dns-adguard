FROM python:3.10-alpine

WORKDIR /app

COPY adguard.py main.py config.py requirements.txt /app/

RUN pip install -r requirements.txt

CMD ["python", "main.py"]
