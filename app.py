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


def main_user_keyboard():
    '''
    Function creates a keybord to ease the user's interaction. 
    Keyboard displaying is triggered with the "/start" command. 
    The keyboard remains displayed untill reply_markup is redefined in any other function.
    You can add new buttons right bellow if needed.
    Use func=lambda message: message.text == 'YOUR_BUTTON_TEXT_HERE' in your @bot.message_handler to trigger bot replies. 
    '''
    keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)

    button_courses_list = telebot.types.KeyboardButton('Список курсов')
    buttor_course_program = telebot.types.KeyboardButton('Программа курса')
    button_course_cost = telebot.types.KeyboardButton('Стоимость курса')
    button_course_apply = telebot.types.KeyboardButton('Записаться на курс')
    button_review = telebot.types.KeyboardButton('Оставить отзыв')
    button_help = telebot.types.KeyboardButton('Help')

    keyboard.add(button_courses_list, buttor_course_program, button_course_cost, button_course_apply, button_review, button_help)

    return keyboard


@bot.message_handler(commands=['available_courses'])
def send_available_courses(message):
    filename = os.path.join('data', 'schedule.txt')

    if not os.path.exists(filename):
        bot.send_message(message.chat.id, "Файл с курсами не найден.")
        return

    courses = load_dates(filename)
    available_courses = {course: date for course, date in courses.items() if
                         date.strip() != '-' and date.strip() != 'x'}

    if available_courses:
        response_text = '\n'.join([f"{course}: {date}" for course, date in available_courses.items()])
    else:
        response_text = "Нет доступных курсов."

    bot.send_message(message.chat.id, response_text)


def load_dates(filename):
    courses = {}
    with open(filename, 'r', encoding='utf-8') as f:
        for line in f:
            course, date = line.strip().split(';', 1)
            courses[course] = date
    return courses


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
            if course_name.lower() in name.lower():
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
    bot.send_message(message.chat.id, text='Выберите интересующий вас курс, чтоб узнать его программу', reply_markup=keyboard)

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

@bot.message_handler(func=lambda message: message.text == 'Записаться на курс')
def registration_user_on_course(message):
    '''
    Responds with a list of courses and asks the user to select a course for registration.
    '''
    filename = os.path.join('data', 'courses.txt')
    courses = get_list_of_courses(filename)
    if not courses:
        bot.send_message(message.chat.id, 'Курсы не найдены')
        return
    keyboard = telebot.types.InlineKeyboardMarkup(row_width=1)
    for course_name, _ in courses.items():
        button = telebot.types.InlineKeyboardButton(text=course_name, callback_data=f'register_{course_name}')
        keyboard.add(button)
    bot.send_message(message.chat.id, 'Запись на какой курс вас интересует?', reply_markup=keyboard)


@bot.callback_query_handler(func=lambda call: call.data.startswith('register_'))
def handle_course_selection(call):
    '''
    Registers the user for the selected course and sends a confirmation message.
    '''
    course_name = call.data.split('register_')[1]
    user_id = call.from_user.id
    username = call.from_user.username

    db_manager.save_user_registration(user_id, username, course_name)

    bot.send_message(call.message.chat.id, f'Вы успешно записались на курс: {course_name}!\nС вами свяжутся в телеграмм в ближайшее время.')

@bot.message_handler(func=lambda message: message.text == 'Стоимость курса')
def ask_for_course_price(message):
    '''
    Responds with a list of courses and asks the user to select a course to get its price.
    '''
    filename = os.path.join('data', 'courses.txt')
    courses = get_list_of_courses(filename) 

    if not courses:
        bot.send_message(message.chat.id, 'Курсы не найдены')
        return

    keyboard = telebot.types.InlineKeyboardMarkup(row_width=1)
    for course_name, _ in courses.items():
        button = telebot.types.InlineKeyboardButton(text=course_name, callback_data=f'price_{course_name}')
        keyboard.add(button)

    bot.send_message(message.chat.id, 'Стоимость какого курса вас интересует?', reply_markup=keyboard)


@bot.callback_query_handler(func=lambda call: call.data.startswith('price_'))
def send_course_price(call):
    '''
    Sends the price of the selected course after the user clicks on the course button.
    '''
    course_name = call.data.split('price_')[1]
    filename = os.path.join('data', 'price-list.txt')
    price = get_course_prices(filename, course_name)

    if price is None:
        bot.send_message(call.message.chat.id, f'Стоимость курса "{course_name}" не найдена.')
    else:
        price_message = f'Цены для курса "{course_name}":\n'
        for level, price in price.items():
            price_message += f'{level}: {price}\n'
        bot.send_message(call.message.chat.id, price_message)


@bot.message_handler(commands=['start'])
def send_welcome(message):
    '''
    1. Greeting reply and keyboard displaying. Trigger is a user's "/start" command message.
    '''
    welcome_answer = '''
👋 Вас приветствует бот Prog Academy!
Если желаете получить информацию о всех возможностях данного бота, нажмите *Help*

Пожалуйста, выберите интересующий вас пункт меню и мы приступим. 😊
''' 
    bot.send_message(message.chat.id, welcome_answer, parse_mode='Markdown', reply_markup=main_user_keyboard())


@bot.message_handler(func=lambda message: message.text == '/help' or message.text == 'Help')
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


@bot.message_handler(func=lambda message: message.text == 'Оставить отзыв')
def leave_review(message):
    '''
    Sends a link to the DOU page for leaving a review when the user presses the "Оставить отзыв" button.
    '''
    review_message = '''
Вы уже прошли курс у нас? Если да, то будем рады вашему отзыву на нашей страничке на сайте DOU!
[https://jobs.dou.ua/companies/progkievua/reviews/](https://jobs.dou.ua/companies/progkievua/reviews/)
'''
    bot.send_message(message.chat.id, review_message, parse_mode='Markdown')



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
