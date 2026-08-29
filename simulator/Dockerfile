FROM python:3.12-slim
WORKDIR /app
COPY simulator /app/simulator
RUN pip install --no-cache-dir paho-mqtt
CMD ["python","/app/simulator/run.py","--transport","mqtt","--rate","1"]
