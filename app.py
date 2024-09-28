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

@bot.message_handler(commands=['available_courses'])
def send_available_courses(message):
    filename = os.path.join('data', 'schedule.txt')
    courses = load_courses(filename)
    available_courses = {course: date for course, date in courses.items() if date != '-' and date != 'x'}

    if available_courses:
        response_text = '\n'.join([f"{course}: {date}" for course, date in available_courses.items()])
    else:
        response_text = "Нет доступных курсов."

    bot.send_message(message.chat.id, response_text)


def load_courses(filename):
    courses = {}
    with open(filename, 'r', encoding='utf-8') as file:
        for line in file:
            name, dates = line.strip().split(';')
            courses[name] = dates
    return courses

def get_list_of_courses(filename):
    res = {}
    with open(filename, 'r', encoding='utf-8') as f:
        for line in f:
            course_name, course_link = line.strip().split(';')
            course_name = course_name.strip()
            course_link = course_link.strip()
            res[course_name] = course_link
    return res

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

def get_course_prices(filename, course_name):
    prices = {}
    with open(filename, 'r', encoding='utf-8') as f:
        for line in f:
            parts = line.strip().split(';')
            name = parts[0].strip()
            if name.lower() == course_name.lower():
                for price_part in parts[1:]:
                    level, price = price_part.split(':')
                    prices[level.strip()] = price.strip()
                return prices
    return None

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
        button = telebot.types.InlineKeyboardButton(text=course_name,
                                                    callback_data=f'register_{course_name}')
        keyboard.add(button)
    bot.send_message(message.chat.id, text='Выберите курс', reply_markup=keyboard)


@bot.callback_query_handler(func=lambda call: call.data.startswith('register_'))
def handle_course_selection(call):
    # get user info from call
    course_name = call.data.split('register_')[1]
    user_id = call.from_user.id
    username = call.from_user.username

    # save user data to db
    db_manager.save_user_registration(user_id, username, course_name)

    bot.send_message(call.message.chat.id, f'Вы успешно записались на курс: {course_name}')

@bot.message_handler(commands=['courseprice'])
def course_price(message):
    try:
        course_name = message.text.split(maxsplit=1)[1].strip()
    except IndexError:
        bot.send_message(message.chat.id, 'Пожалуйста, введите название курса после команды /courseprice')
        return

    filename = os.path.join('data', 'price-list.txt')
    prices = get_course_prices(filename, course_name)

    if prices is None:
        bot.send_message(message.chat.id, f'Стоимость курса "{course_name}" не найдена.')
    else:
        price_message = f'Цены для курса "{course_name}":\n'
        for level, price in prices.items():
            price_message += f'{level}: {price}\n'
        bot.send_message(message.chat.id, price_message)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    '''
    Greeting reply. Trigger is a user's "/start" command message. Informational purpose only.
    '''
    welcome_answer = '''
👋 Вас приветствует бот Prog Academy!
Если желаете получить информацию о всех возможностях данного бота, нажмите *Help*

Пожалуйста, выберите интересующий вас пункт меню и мы приступим. 😊
''' 
    bot.send_message(message.chat.id, welcome_answer, parse_mode='Markdown')

@bot.message_handler(commands=['help'])
def send_help(message):
    '''
    A reply with a description of all the bot's functions. Trigger is a user's "/help" command message. Informational purpose only.
    '''
    help_answer = '''
Вот что вы можете сделать:
1️⃣ Просмотреть доступные курсы и получить всю информацию о них (Описание, продолжительность, дата старта, стоимость)
2️⃣ Записаться на курс, если запись открыта
3️⃣ Прочитать отзывы и оставить свои
4️⃣ Если останутся вопросы, связаться со службой поддержки и проконсультироваться

Пожалуйста, выберите интересующий вас пункт меню и мы приступим. 😊 
'''
    bot.send_message(message.chat.id, help_answer, parse_mode='Markdown')

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
