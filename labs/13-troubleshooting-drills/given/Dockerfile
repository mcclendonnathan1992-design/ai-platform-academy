FROM python:latest
WORKDIR /srv
ADD https://example.com/app.tar.gz /srv/
COPY . .
RUN pip install -r requirements.txt
CMD ["python", "app.py"]
