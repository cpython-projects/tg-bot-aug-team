import telebot
from dotenv import load_dotenv
import os
from flask import Flask, request

from database_manager.database_manager import DatabaseManager

load_dotenv()

TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
bot = telebot.TeleBot(TOKEN)
# init Database Manager
db_manager = DatabaseManager()
app = Flask(__name__)


def get_list_of_courses(filename):
    res = {}
    with open(filename, 'r', encoding='utf-8') as f:
        for line in f:
            course_name, course_link = line.strip().split(';')
            course_name = course_name.strip()
            course_link = course_link.strip()
            res[course_name] = course_link
    return res


@bot.message_handler(commands=['courses'])
def all_courses(message):
    filename = os.path.join('data', 'courses.txt')
    courses = get_list_of_courses(filename)
    if not courses:
        bot.send_message(message.chat.id, 'Курсы не найдены')
        return
    keyboard = telebot.types.InlineKeyboardMarkup(row_width=1)
    for course_name, course_link in courses.items():
        url_button = telebot.types.InlineKeyboardButton(text=course_name, url=course_link)
        keyboard.add(url_button)
    bot.send_message(message.chat.id, text='Выберите курс', reply_markup=keyboard)


def find_courses_by_keyword(filename, keyword):
    keyword = keyword.lower()
    filtered_courses = {}

    with open(filename, 'r', encoding='utf-8') as f:
        for line in f:
            course_name, course_link = line.strip().split(';')
            course_name = course_name.strip()
            course_link = course_link.strip()

            if keyword in course_name.lower():
                filtered_courses[course_name] = course_link

    return filtered_courses


@bot.message_handler(commands=['findcourse'])
def find_course(message):
    try:
        keyword = message.text.split(maxsplit=1)[1].strip()
    except IndexError:
        bot.send_message(message.chat.id, 'Пожалуйста, введите ключевое слово после команды /findcourse')
        return

    filename = os.path.join('data', 'courses.txt')
    courses = find_courses_by_keyword(filename, keyword)

    if not courses:
        bot.send_message(message.chat.id, f'Курсы с ключевым словом "{keyword}" не найдены.')
        return

    keyboard = telebot.types.InlineKeyboardMarkup(row_width=1)
    for course_name, course_link in courses.items():
        url_button = telebot.types.InlineKeyboardButton(text=course_name, url=course_link)
        keyboard.add(url_button)

    bot.send_message(message.chat.id, text='Найденные курсы:', reply_markup=keyboard)


@bot.message_handler(commands=['registration'])
def registration_user_on_course(message):
    filename = os.path.join('data', 'courses.txt')
    courses = get_list_of_courses(filename)
    if not courses:
        bot.send_message(message.chat.id, 'Курсы не найдены')
        return
    keyboard = telebot.types.InlineKeyboardMarkup(row_width=1)
    for course_name, _ in courses.items():
        button = telebot.types.InlineKeyboardButton(text=course_name, callback_data=course_name)
        keyboard.add(button)
    bot.send_message(message.chat.id, text='Выберите курс', reply_markup=keyboard)


@bot.callback_query_handler(func=lambda call: True)
def handle_course_selection(call):
    # get user info from call
    course_name = call.data
    user_id = call.from_user.id
    username = call.from_user.username

    # save user data to db
    db_manager.save_user_registration(user_id, username, course_name)

    bot.send_message(call.message.chat.id, f'Вы успешно записались на курс: {course_name}')


@bot.message_handler(commands=['start'])
def send_welcome(message):
    pass


@bot.message_handler(commands=['help'])
def send_help(message):
    pass


@app.route('/' + TOKEN, methods=['POST'])
def get_message():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return 'Test Bot', 200


@app.route('/')
def webhook():
    bot.remove_webhook()
    bot.set_webhook(url='https://july-bot-606ff6a196f8.herokuapp.com/' + TOKEN)
    return 'Test Bot', 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))