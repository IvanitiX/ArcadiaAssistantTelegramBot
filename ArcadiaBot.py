#!/usr/bin/python

# This is a simple echo bot using the decorator mechanism.
# It echoes any incoming text messages.

import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

import requests
import time
from pydub import AudioSegment


API_TOKEN = 'CAMBIA-ESTO'

bot = telebot.TeleBot(API_TOKEN)

def tts(text):
    print(text)
    query = requests.post('http://localhost:8000/tts',json={"text_to_read": text})
    with open('tts.wav','wb') as file:
        file.write(query.content)
        file.close()
    AudioSegment.from_wav('tts.wav').export('tts.ogg',format='ogg')
    return telebot.types.InputFile('tts.ogg')

@bot.inline_handler(lambda a: False)
def send_tts(chat_id, text):
    bot.send_audio(chat_id,tts(text),caption="He leído el mensaje por ti.")

def gen_speak_button_wikipedia_markup(url):
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    markup.add(InlineKeyboardButton("¿Necesitas que te lo cuente?", callback_data="cb_speak"))
    markup.add(InlineKeyboardButton("Aquí el artículo", url=url))
    return markup

def gen_speak_button_markup():
    markup = InlineKeyboardMarkup()
    markup.row_width = 1
    markup.add(InlineKeyboardButton("¿Necesitas que te lo cuente?", callback_data="cb_speak"))
    return markup

def gen_ask_arcadia_button_markup():
    markup = InlineKeyboardMarkup()
    markup.row_width = 1
    markup.add(InlineKeyboardButton("¿Necesitas una respuesta?", callback_data="cb_ask"))
    return markup

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.data == "cb_ask":
        print(call.message.text)
        bot.answer_callback_query(call.id, answer_arcadia_query(call.message))
    elif call.data == "cb_speak":
        bot.answer_callback_query(call.id, send_tts(call.message.chat.id,call.message.text))

# Handle '/start' and '/help'
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, """\
                ¡Hola! Soy Arcadia.\n
Intentaré responderte a las cuestiones que tengas. Para ello, sólo escribe tu mensaje empezando por mi nombre.\n
Prueba con 'Arcadia, háblame de ti.'
                """)

@bot.message_handler(commands=['help'])
def send_help(message):
    bot.reply_to(message, """\
                Con que necesitas ayuda, ¿no?\n
Puedes preguntarme cualquier cosa en texto escribiendo un texto que empiece con la palabra "Arcadia".\n
Puedes transcribir un audio citando el audio y escribiendo /transcribe.\n
También puedes convertir un texto en audio citando el texto y escribiendo /speak.
                """)


@bot.message_handler(regexp='[Aa]rcadia.*')
def answer_arcadia_query(message):
    print('___')
    print(message.text)
    query = requests.post('http://localhost:8000/ask-arcadia-text',json={'query':message.text})
    if query.ok:
        query_response = query.json()['response']
        response = ''
        source = None
        for line in query_response:
            if '[<>]' not in line and '[>]' not in line:
                response = response.join(line)
            elif '[<>]' in line:
                source = line.split(' ',1)[1]

        if source:
            bot.reply_to(message, response, reply_markup=gen_speak_button_wikipedia_markup(source))
        else:
            bot.reply_to(message, response, reply_markup=gen_speak_button_markup())
    else:
        bot.reply_to(message,'¡Oh. no! No puedo conectarme con mi libro de respuestas.')

@bot.message_handler(commands=['speak'])
def response_to_tts(message):
    if hasattr(message,'reply_to_message') and hasattr(message.reply_to_message,'text'):
        bot.send_audio(message.chat.id,tts(message.reply_to_message.text),caption="He leído el mensaje por ti.")
    else:
        bot.reply_to(message,'No has citado ningún mensaje que pueda leer')

@bot.message_handler(commands=['transcribe'])
def response_to_sr(message):
    if hasattr(message,'reply_to_message') and hasattr(message.reply_to_message,'voice') and hasattr(message.reply_to_message.voice,'file_id'):
        file_info = bot.get_file(message.reply_to_message.voice.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        with open('sr.ogg', 'wb') as new_file:
            new_file.write(downloaded_file)
            new_file.close()
        sr = AudioSegment.from_ogg('sr.ogg')
        sr.set_channels(1)
        sr.set_sample_width(4)
        sr.export('sr.wav',format='wav',codec='pcm_s16le',parameters=['-ar','16000'])
        query = requests.post('http://localhost:8000/sr',files={'audio': open('sr.wav', 'rb')})
        if query.json()['transcript'] != ' ':
            bot.reply_to(message,query.json()['transcript'],reply_markup=gen_ask_arcadia_button_markup())
        else:
            print('Vacío')
    else:
        bot.reply_to(message,'No has citado ningún audio que pueda transcribir')

@bot.message_handler(func=lambda message: False)
def echo_message(message):
    print(message)


bot.infinity_polling()