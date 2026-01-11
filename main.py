import telebot
from telebot import types
import psycopg2
import os
from datetime import datetime, timedelta
import flask

TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
DATABASE_URL = os.environ.get('DATABASE_URL')

sub1 = os.environ.get('SUB1')
sub2 = os.environ.get('SUB2')
sub3 = os.environ.get('SUB3')
sub4 = os.environ.get('SUB4')
sub5 = os.environ.get('SUB5')
sub6 = os.environ.get('SUB6')

manager = os.environ.get('MANAGER')

users = [
2028669813,
1860232832,
1035549880,
5182980257,
1311981687,
5666816099,
1908881174,
5373611674,
1921531412,
5659929336,
458844134,
5919688416,
6460157463,
5514640451,
669900102,
2049375630,
5379643319,
1307179734
]

if not TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN environment variable is required")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is required")

bot = telebot.TeleBot(TOKEN)

def get_db_connection():
    return psycopg2.connect(DATABASE_URL)

def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS trial_users (
            user_id BIGINT PRIMARY KEY,
            trial_start TIMESTAMP NOT NULL,
            trial_expiry TIMESTAMP NOT NULL,
            trial_used BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    cur.close()
    conn.close()

def has_access(user_id):
    if user_id in users:
        return 'full'
    else:
        return None

def get_status_text(user_id):
    if user_id in users:
        return '⚡ Статус подписки - <b>Активная</b>'
    else:
        return f'❌ Подписка не активна.\n Обратитетсь к {manager}'
    
def get_main_menu_markup(user_id):
    if user_id in users:
        markup = types.InlineKeyboardMarkup()
        buttons = [
        ('👑 Щука', 'topic_1'), 
        ('Privio #1', 'topic_2'), ('Privio #2', 'topic_3'), ('Privio #3', 'topic_4'),
        ('Privio #4', 'topic_5'),
        ('Privio #5', 'topic_6'),
        ('ℹ️ Информация', 'topic_7'),
        ]
    markup.row(types.InlineKeyboardButton(buttons[0][0], callback_data=buttons[0][1]),
               types.InlineKeyboardButton(buttons[1][0], callback_data=buttons[1][1]))
    for text, data in buttons[2:]:
        markup.row(types.InlineKeyboardButton(text, callback_data=data))
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.chat.id
    bot.send_message(
        message.chat.id,
        f'👋 Привет, {message.from_user.first_name}!\n\n{get_status_text(user_id)}',
        parse_mode='html', reply_markup=get_main_menu_markup(user_id)
    )

topics = {
    'topic_1': '👑 Щука',
    'topic_2': 'Privio #1',
    'topic_3': 'Privio #2',
    'topic_4': 'Privio #3',
    'topic_5': 'Privio #4',
    'topic_6': 'Privio #5',
}

topic_buttons = {
    'topic_1': ['Безлимит'],
    'topic_2': ['50 ГБ'],
    'topic_3': ['50 ГБ'],
    'topic_4': ['50 ГБ'],
    'topic_5': ['10 ГБ'],
    'topic_6': ['10 ГБ']
}

topic_urls = {
    'topic_1': (f'{sub1}'),
    'topic_2': (f'{sub2}'),
    'topic_3': (f'{sub3}'),
    'topic_4': (f'{sub4}'),
    'topic_5': (f'{sub5}'),
    'topic_6': (f'{sub6}')
}

def get_topic_content(topic_id, content_idx):
    if topic_id not in topic_urls:
        return None
    url, count = topic_urls[topic_id]
    if content_idx < 1 or content_idx > count:
        return None
    return f'{url}\n\n🚀 (Инструкция)[https://teletype.in/@hundrik3/happ]'

@bot.callback_query_handler(func=lambda call: call.data == 'activate_trial')
def activate_trial_callback(call):
    user_id = call.message.chat.id
    if user_id in users:
        bot.answer_callback_query(call.id, '⚡ У вас уже есть полный доступ!')
        return
    else:
        bot.answer_callback_query(call.id, '❌ Ошибка')

@bot.callback_query_handler(func=lambda call: call.data == 'back_to_menu')
def back_to_menu_callback(call):
    user_id = call.message.chat.id
    bot.answer_callback_query(call.id)
    bot.edit_message_text(
        get_status_text(user_id),
        call.message.chat.id, call.message.message_id,
        parse_mode='html', reply_markup=get_main_menu_markup(user_id)
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith('topic_'))
def topic_callback(call):
    topic_id = call.data
    user_id = call.message.chat.id
    bot.answer_callback_query(call.id)
    
    if topic_id == 'topic_10':
        markup = types.InlineKeyboardMarkup()
        markup.row(types.InlineKeyboardButton('⬅️ Назад', callback_data='back_to_menu'))
        bot.edit_message_text( f'ℹ️ <b>Информация</b>\n\n6 подписок\n\n⭐ По вопросам: {manager}',
            call.message.chat.id, call.message.message_id, parse_mode='html', reply_markup=markup
        )
        return

@bot.callback_query_handler(func=lambda call: call.data.startswith('content_'))
def content_callback(call):
    bot.answer_callback_query(call.id)
    parts = call.data.split('_')
    if len(parts) < 4:
        return
    
    topic_id = f'{parts[1]}_{parts[2]}'
    content_idx = int(parts[3])
    user_id = call.message.chat.id
    
    if has_access(user_id, topic_id) is None:
        return
    
    content = get_topic_content(topic_id, content_idx)
    if content is None:
        bot.answer_callback_query(call.id, '❌ Контент не найден')
        return
    
    markup = types.InlineKeyboardMarkup()
    markup.row(types.InlineKeyboardButton('⬅️ Назад к разделу', callback_data=topic_id))
    markup.row(types.InlineKeyboardButton('🏠 Главное меню', callback_data='back_to_menu'))
    
    bot.edit_message_text(content, call.message.chat.id, call.message.message_id, parse_mode='html', reply_markup=markup)

WEBHOOK_HOST = os.environ.get('WEBHOOK_HOST')
WEBHOOK_PORT = int(os.environ.get('PORT', '10000'))

if WEBHOOK_HOST:
    app = flask.Flask(__name__)
    WEBHOOK_URL_BASE = f"https://{WEBHOOK_HOST}"
    WEBHOOK_URL_PATH = f"/{TOKEN}"
    
    @app.route(WEBHOOK_URL_PATH, methods=['POST'])
    def webhook():
        if flask.request.headers.get('content-type') == 'application/json':
            update = telebot.types.Update.de_json(flask.request.get_data().decode('utf-8'))
            bot.process_new_updates([update])
            return ''
        flask.abort(403)

if __name__ == '__main__':
    try:
        init_db()
        print("Database initialized.")
    except Exception as e:
        print(f"Error connecting to database: {e}")
        
    if WEBHOOK_HOST:
        bot.set_webhook(url=WEBHOOK_URL_BASE + WEBHOOK_URL_PATH)
        print(f"Webhook: {WEBHOOK_URL_BASE}{WEBHOOK_URL_PATH}")
        app.run(host='0.0.0.0', port=WEBHOOK_PORT)
    else:
        print('Starting in Polling mode...')
        bot.polling(none_stop=True)
