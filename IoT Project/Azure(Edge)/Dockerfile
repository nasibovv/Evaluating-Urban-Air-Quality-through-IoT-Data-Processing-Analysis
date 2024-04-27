FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY Data_Preprocessing.py Data_Preprocessing.py

CMD ["python", "Data_Preprocessing.py"]
