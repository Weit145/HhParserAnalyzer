import telebot
from telebot import types
TOKEN = '7991127371:AAGsy0CX82kA_cly_wEq0W-GmJQ2DPW-axs'
# TOKEN = '5915864844:AAGq_aEAn98b-u6kuOHIxbheYUgVrOv9Xnk'
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def start_message(message):
    bot.send_message(message.chat.id, "Ты самая красивая девушка на свете, я тебя люблю!")
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    item1 = types.KeyboardButton("Нажми и увидишь сюрприз")
    markup.add(item1)
    bot.send_message(message.chat.id, "?", reply_markup=markup)


@bot.message_handler(content_types='text')
def message_reply(message):
    if message.text=="Нажми и увидишь сюрприз":
        try:
            with open("we.jpg", "rb") as photo:
                bot.send_photo(message.chat.id, photo)
        except FileNotFoundError:
            bot.send_message(message.chat.id, "Файл с изображением не найден!")
bot.infinity_polling()