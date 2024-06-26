FROM python:3.12-bookworm

RUN apt update && apt install -y ffmpeg

RUN pip install pyTelegramBotAPI
RUN pip install pydub
RUN pip install python-dotenv

COPY ./ .

ENTRYPOINT ["python3", "ArcadiaBot.py"]