FROM python:3.7-slim
WORKDIR /app
COPY requirements.txt .
RUN pip3 install -r requirements.txt --no-cache-dir
COPY . .
ENV BOT_TOKEN="5412427057:AAE6CzrszERLPukyftYuoeNbjgf-kZPIh0o"
CMD ["python", "yet_another_english_bot.py"]