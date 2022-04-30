# Use the official lightweight Python image.
# https://hub.docker.com/_/python
FROM python:3.8-slim

# Copy local code to the container image.
ENV APP_HOME /app
WORKDIR $APP_HOME
COPY . ./
RUN pip install -r requirements.txt
ENV GOOGLE_APPLICATION_CREDENTIALS=/app/ubc-serverless-ghazal-9bede7ba1a47.json
ENTRYPOINT ["python3","main.py"]
