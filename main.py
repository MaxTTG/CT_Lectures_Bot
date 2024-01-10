# Библиотека с ТГ-ботом
import telebot

# Работа с Google сервисами: GoogleDrive и YouTube
import functions
# Работа с базой данных ТГ-бота; используется TinyDB
import database
# Некоторые конфигурационные переменные
import config

# Для выполнения рассылки раз в день
import schedule
import threading
import time

'''
    @name       CT Lectures Bot
    @version    1.0 (10.01.2024)
    @author     Tarazanov Maxim M4139
'''

bot = telebot.TeleBot(config.CT_LECTURES_BOT_TOKEN)


################
# Слеш-команды #
################

# Начало работы
@bot.message_handler(commands=['start'])
def start(message: telebot.types.Message):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)

    buttonGDYT = telebot.types.KeyboardButton('Ссылки Google Drive / YouTube')
    markup.add(buttonGDYT)

    database.createUser(message.from_user.id)

    bot.send_message(message.chat.id, config.WELCOME_TEXT, reply_markup=markup, parse_mode='html')


# Установка папки курса
@bot.message_handler(commands=['set'])
def setGD(message: telebot.types.Message):
    newLink = message.text.split('/')[-1]
    try:
        if newLink not in database.getActiveFolders():
            bot.send_message(message.chat.id, 'Устанавливаю папку...\nНапишу ещё раз, как установлю!')
            database.setUserGD(message.from_user.id, newLink)
        text = 'Папка успешно была установлена'
    except Exception as e:
        text = 'Что-то пошло не так 😔\n' \
               'Попробуйте снова'
    bot.send_message(message.chat.id, text)


# Открыть папку курса
@bot.message_handler(commands=['open'])
def openGD(message: telebot.types.Message):
    message_text, markup = functions.getGDMessage(functions.links_to_ids([database.getUserGD(message.from_user.id)]))
    bot.send_message(message.chat.id, message_text, reply_markup=markup, parse_mode='html')


# Поиск на YouTube
@bot.message_handler(commands=['yt'])
def yt(message: telebot.types.Message):
    prompt = message.text.split(maxsplit=1)[1]
    items = functions.searchYT(prompt)
    if items:
        message_text = ''
        for item in items:
            message_text += 'Видео: ' if item['type'] == 'video' else 'Плейлист: '
            message_text += f'<a href="{item["url"]}">{item["title"]}</a>\n\n'
        bot.send_message(message.chat.id, message_text, parse_mode='html', disable_web_page_preview=True)
    else:
        bot.send_message(message.chat.id, f'По запросу "{prompt}" ничего не найдено 😔')


# Вывод помощи
@bot.message_handler(commands=['help', 'h'])
def help_(message: telebot.types.Message):
    bot.send_message(message.chat.id, config.HELP_TEXT, parse_mode='html')


########################################
# Сообщения в бота в свободном формате #
########################################

# Функция для работы с запросами в бота
@bot.message_handler()
def parseText(message: telebot.types.Message):
    if message.text == 'Ссылки Google Drive / YouTube':
        text = ''
        link = database.getUserGD(message.from_user.id)
        if link != '':
            text += f'<a href="https://drive.google.com/drive/folders/{link}">Google Drive</a>\n'
        text += f'<a href="{config.CT_LECTURES_YT}">CT Lectures YouTube</a>'
        bot.send_message(
            message.chat.id,
            text,
            parse_mode='html'
        )
    else:
        bot.send_message(message.chat.id, 'Не знаю, что требуется 😔')


###########################
# Кнопки сообщений в чате #
###########################
@bot.callback_query_handler(func=lambda cb: True)
def callback(cb: telebot.types.CallbackQuery):
    data = cb.data.split(' ')
    if data[0] == 'gd':
        message_text, markup = functions.getGDMessage(data[1:])
        bot.edit_message_text(message_text, cb.message.chat.id, cb.message.message_id, reply_markup=markup,
                              parse_mode='html')
    else:
        bot.send_message(cb.message.chat.id, 'Я не знаю что делать 😔')


################################
# Рассылка обновлений на диске #
################################
def cronBroadcast():
    active_folders = database.getActiveFolders()
    db_folders = database.getDBFolders()
    db_files = database.getDBFiles()

    newfiles = {}

    for folder in active_folders:
        if folder not in db_folders:
            print('Ошибка: у пользователя обнаружена неизвестная ссылка')
            continue
        curfiles = functions.getAllFilesFromGD(folder)
        for file in curfiles:
            if file not in db_files:
                if folder not in newfiles:
                    newfiles[folder] = []
                newfiles[folder].append(file)

    for folder in newfiles.keys():
        users = database.getUsersByFolder(folder)
        for user in users:
            message_text = 'Новые файлы в Google Drive:\n\n'
            for file in newfiles[folder]:
                database.addFile(folder, file)
                file = file.split('/')[-1]
                message_text += f'<a href="https://drive.google.com/file/d/{file}">{functions.getGDFile(file)}</a>\n\n'
            bot.send_message(user, message_text, parse_mode='html')


##############################
# Запуск потока для рассылки #
##############################
def runSchedulers(bctime: str = '00:00'):
    # Для теста рассылки
    # schedule.every(10).seconds.do(cronBroadcast)

    schedule.every().day.at(bctime).do(cronBroadcast)
    while True:
        schedule.run_pending()
        time.sleep(1)


##########################
# Запуск потока для бота #
##########################
def runBot():
    # Создание базы данных
    database.createDB()

    # Запуск Google Сервисов
    functions.runGoogleServices()

    # Непосредственно запуск бота
    bot.polling(non_stop=True)


##########
# main() #
##########
if __name__ == '__main__':
    t1 = threading.Thread(target=runBot)
    t2 = threading.Thread(target=runSchedulers)

    t1.start()
    t2.start()
