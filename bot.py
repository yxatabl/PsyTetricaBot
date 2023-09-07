from aiogram import Bot, executor, types, Dispatcher
from aiogram.utils import exceptions
from aiogram.contrib.fsm_storage.memory import MemoryStorage
import sqlite3 as sql
import logging
import time
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv
from oauth2client.service_account import ServiceAccountCredentials
import gspread
import os


load_dotenv()

# ENV VARS
CURRENT_PATH = os.path.dirname(os.path.abspath(__file__)) + '/'
DB_PATH = CURRENT_PATH + 'db.db'
DB_CONFIG_PATH = CURRENT_PATH + 'db_config.sql'
PHOTOS_PATH = CURRENT_PATH + 'photos'
CONGIF_PATH = CURRENT_PATH + 'config.json'
GOOGLE_PATH = CURRENT_PATH + 'google_cred.json'

with open(CONGIF_PATH) as config_file:
    config_data = json.load(config_file)

TKN = config_data["tg_token"]
GSH_ID = config_data["google_sheet_id"]

register_docx_files = ["ДОГОВОР ПУБЛИЧНОЙ ОФЕРТЫ.docx", "ПОЛЬЗОВАТЕЛЬСКОЕ СОГЛАШЕНИЕ.docx",
                       "СОГЛАСИЕ_НА_ОБРАБОТКУ_И_ПЕРЕДАЧУ_ДАННЫХ.docx"]

scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
google_credentials = ServiceAccountCredentials.from_json_keyfile_name(GOOGLE_PATH, scope)
google_client = gspread.authorize(google_credentials)

spreadsheet = google_client.open_by_key(GSH_ID)

LOG_PATH = CURRENT_PATH + 'log.log'
# LOGGING
logging.basicConfig(level=logging.INFO, filename=LOG_PATH, filemode='w',
                    format="%(asctime)s %(levelname)s %(message)s")

# BOT INIT
bot = Bot(TKN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# DB INIT
conn = sql.connect(DB_PATH)
cur = conn.cursor()
with open(DB_CONFIG_PATH, 'r') as file:
    cur.executescript(file.read())

def prepare_psycho_table():
    cur.execute('''  
        SELECT t1.id, t1.nickname, t1.rating, t1.desc, GROUP_CONCAT(t3.name, ', ') AS categories
        FROM Psycho t1
        LEFT JOIN (SELECT DISTINCT category, psycho FROM PsychoCategories) AS t2 ON t1.id = t2.psycho
        LEFT JOIN (SELECT id, name FROM Categories) AS t3 ON t2.category = t3.id
        GROUP BY t1.id;
     ''')
    return cur.fetchall()

def prepare_psycho_google_sheet():
    if spreadsheet:
        worksheet = spreadsheet.get_worksheet(0)
        worksheet.clear()
        rows = prepare_psycho_table()
        if rows and len(rows) > 0:
            worksheet.update('A1', rows)

# DB METHODS
def get_user(id: int):
    cur.execute(''' SELECT * FROM Users WHERE id=?''', [id])
    return cur.fetchone()


def get_users():
    cur.execute(''' SELECT * FROM Users ''')
    return cur.fetchall()


def add_user(id, name=None, age=None):
    if name:
        cur.execute(''' UPDATE Users SET nickname=? WHERE id=?''', [name, id])
    elif age:
        cur.execute(''' UPDATE Users SET age=? WHERE id=? ''', [age, id])
    else:
        cur.execute(''' INSERT INTO Users(id, banned, reg_date, ban_time) VALUES (?, ?, ?, ?) ''',
                    [id, False, time.time(), 0.0])
    conn.commit()


def get_psychos(id=None):
    if id:
        cur.execute(''' SELECT * FROM Psycho WHERE id=?''', [id])
        return cur.fetchone()
    else:
        cur.execute(''' SELECT * FROM Psycho''')
        return cur.fetchall()


# def get_psychos_by_categories_ids(ids: str):
#     cur.execute(''' SELECT DISTINCT psycho FROM PsychoCategories WHERE category IN (?) ''', [ids])
#     return cur.fetchall()

def get_psychos_by_categories_ids(ids: str):
    category_ids_arr = ids.split(" ")
    if len(category_ids_arr) > 1:
        category_ids_arr = list(map(int, category_ids_arr))

    if len(category_ids_arr) == 1:
        cur.execute(
            ''' SELECT DISTINCT psycho, COUNT(psycho) AS distinct_psycho FROM PsychoCategories WHERE category IN (?) GROUP BY psycho ''', [category_ids_arr[0]])
    elif len(category_ids_arr) == 2:
        cur.execute(
            ''' SELECT DISTINCT psycho, COUNT(psycho) AS distinct_psycho FROM PsychoCategories WHERE category IN (?, ?) GROUP BY psycho ''', [category_ids_arr[0], category_ids_arr[1]])
    elif len(category_ids_arr) == 3:
        cur.execute(
            ''' SELECT DISTINCT psycho, COUNT(psycho) AS distinct_psycho FROM PsychoCategories WHERE category IN (?, ?, ?) GROUP BY psycho ''', [category_ids_arr[0], category_ids_arr[1], category_ids_arr[2]])
    elif len(category_ids_arr) == 4:
        cur.execute(
            ''' SELECT DISTINCT psycho, COUNT(psycho) AS distinct_psycho FROM PsychoCategories WHERE category IN (?, ?, ?, ?) GROUP BY psycho ''', [category_ids_arr[0], category_ids_arr[1], category_ids_arr[2], category_ids_arr[3]])
    elif len(category_ids_arr) == 5:
        cur.execute(
            ''' SELECT DISTINCT psycho, COUNT(psycho) AS distinct_psycho FROM PsychoCategories WHERE category IN (?, ?, ?, ?, ?) GROUP BY psycho ''', [category_ids_arr[0], category_ids_arr[1], category_ids_arr[2], category_ids_arr[3], category_ids_arr[4]])
    else:
        cur.execute(
            ''' SELECT DISTINCT psycho, COUNT(psycho) AS distinct_psycho FROM PsychoCategories WHERE category > 0 GROUP BY psycho ''')
    return cur.fetchall()


def set_psycho_category(psycho: int, cat: int):
    cur.execute(''' INSERT INTO PsychoCategories(psycho, category) VALUES (?, ?) ''', [psycho, cat])
    conn.commit()

def get_psycho_categories(psycho: int):
    cur.execute(''' SELECT category FROM PsychoCategories WHERE psycho=? ''', [psycho])
    return cur.fetchall()

def delete_psycho_category(psycho: int):
    cur.execute(''' DELETE FROM PsychoCategories WHERE psycho=? ''', [psycho])
    conn.commit()


def check_if_psychos_category_exist(psycho: int, category: int):
    cur.execute(''' SELECT * FROM PsychoCategories WHERE psycho=? AND category=? ''', [psycho, category])
    return cur.fetchone()


# SELECT cate_id,COUNT(DISTINCT(pub_lang)), ROUND(AVG(no_page),2)
# FROM book_mast
# GROUP BY cate_id;

# SELECT column_name, COUNT(column_name) AS count
# FROM table_name
# GROUP BY column_name
# HAVING COUNT(column_name) = (SELECT MAX(cnt) FROM (SELECT COUNT(column_name) AS cnt FROM table_name GROUP BY column_name) AS subquery);

def update_rating(psycho_id: int):
    cur.execute(''' SELECT rating FROM Sessions WHERE psycho=? AND finished=1 ''', [psycho_id])
    ratings = cur.fetchall()
    s = 0
    k = 0
    for rat in ratings:
        s += rat[0]
        k += 1
    if k == 0:
        cur.execute(''' UPDATE Psycho SET rating=? WHERE id=? ''', [0, psycho_id])
    else:
        cur.execute(''' UPDATE Psycho SET rating=? WHERE id=? ''', [round(s / k, 2), psycho_id])
    conn.commit()


def add_request(user, problem=None):
    if problem:
        cur.execute(''' UPDATE Requests SET problem=? WHERE user=? ''', [problem, user])
    else:
        cur.execute(''' INSERT INTO Requests(user, confirmed, occupied) VALUES (?, ?, ?) ''', [user, False, False])
    conn.commit()


def update_request(id: int, problem=None):
    if problem:
        cur.execute(''' UPDATE Requests SET problem=? WHERE id=? ''', [problem, id])
        conn.commit()


def add_psychos_to_request(id: int, psychos=None):
    if psychos:
        cur.execute(''' UPDATE Requests SET psychos=? WHERE id=? ''', [psychos, id])
        conn.commit()


def get_last_request_by_user_id(user: int):
    cur.execute(''' SELECT * FROM Requests WHERE user=? ORDER BY ROWID DESC LIMIT 1''', [user])
    return cur.fetchone()


def remove_request(id=None, request_id=None):
    if request_id:
        cur.execute(''' DELETE FROM Requests WHERE id=? ''', [request_id])
    else:
        cur.execute(''' DELETE FROM Requests WHERE user=? ''', [id])
    conn.commit()


def set_request_occupied(id: int):
    cur.execute(''' UPDATE Requests SET occupied=? WHERE id=? ''', [True, id])
    conn.commit()


def accept_request(id: int):
    cur.execute(''' UPDATE Requests SET confirmed=? WHERE id=? ''', [True, id])
    conn.commit()


def get_request_by_id(id: int):
    cur.execute(''' SELECT * FROM Requests WHERE id=? ''', [id])
    return cur.fetchone()


def get_requests(user=None):
    if user:
        cur.execute(''' SELECT * FROM Requests WHERE user=? ''', [user])
        return cur.fetchone()
    else:
        cur.execute(''' SELECT * FROM Requests ''')
        return cur.fetchall()

def get_not_occupied_requests():
    cur.execute(''' SELECT * FROM Requests WHERE occupied != ? ''', [True])
    return cur.fetchall()

def get_request_categories_by_req_id(requests_id: int):
    cur.execute(''' SELECT * FROM RequestsCategories WHERE requests_id=? ''', [requests_id])
    return cur.fetchall()


def delete_request_categories(user: int):
    cur.execute(''' DELETE FROM RequestsCategories WHERE user=? ''', [user])
    conn.commit()

def add_request_category(user: int, requests_id: int, category_id: int):
    cur.execute(''' INSERT INTO RequestsCategories(user, requests_id, category_id) VALUES (?, ?, ?) ''', [user, requests_id, category_id])
    conn.commit()

def add_techRequest(user, problem=None, user_nickname=None):
    if problem:
        cur.execute(''' UPDATE TechRequests SET problem=?, user_nickname=? WHERE user=? ''',
                    [problem, user_nickname, user])
    else:
        cur.execute(''' INSERT INTO TechRequests(user) VALUES (?) ''', [user])
    conn.commit()


def remove_techRequest(id: int):
    cur.execute(''' DELETE FROM TechRequests WHERE id=? ''', [id])
    conn.commit()


def get_techRequests(user=None):
    if user:
        cur.execute(''' SELECT * FROM TechRequests WHERE user=? ''', [user])
        return cur.fetchone()
    else:
        cur.execute(''' SELECT * FROM TEchRequests ''')
        return cur.fetchall()


def get_admins():
    cur.execute(''' SELECT * FROM Admins ''')
    res = []
    for adm in cur.fetchall():
        res.append(adm[0])
    return res


def add_admin(id: int):
    cur.execute(''' INSERT INTO Admins VALUES (?) ''', [id])
    conn.commit()


def remove_admin(id: int):
    cur.execute(''' DELETE FROM Admins WHERE id=? ''', [id])
    conn.commit()

def add_session(request_id: int, psycho: int):
    cur.execute(''' SELECT * FROM Requests WHERE id=? ''', [request_id])
    req = cur.fetchone()
    cur.execute(''' DELETE FROM Requests WHERE id=? ''', [request_id])
    cur.execute(''' INSERT INTO Sessions(user, psycho, date, finished) VALUES (?, ?, ?, ?)''', [req[1], psycho, time.time(), False])
    conn.commit()
    update_rating(psycho)
    return req

def get_sessions(user=None, member=None):
    if user:
        cur.execute(''' SELECT * FROM Sessions WHERE user=? ''', [user])
        return cur.fetchall()
    elif member:
        cur.execute(''' SELECT * FROM Sessions WHERE (user=? OR psycho=?) AND finished=? ''', [member, member, False])
        return cur.fetchone()


def end_session(psycho: int):
    cur.execute(''' UPDATE Sessions SET finished=? WHERE psycho=? AND finished=? ''', [True, psycho, False])
    conn.commit()


def set_rating(session: int, rating: int):
    cur.execute(''' UPDATE Sessions SET rating=? WHERE id=? ''', [rating, session])
    conn.commit()


def get_banned():
    cur.execute(''' SELECT * FROM Users WHERE banned=1 ''')
    return cur.fetchall()


def unban(id: int):
    cur.execute(''' UPDATE Users SET banned=0, ban_time=0.0 WHERE id=?''', [id])
    conn.commit()


def ban(id: int):
    cur.execute(''' UPDATE Users SET banned=1, ban_time=? WHERE id=?''', [time.time(), id])
    conn.commit()


def add_psycho(id: int, name=None, links=None, price=None, info=None, withWho=None, withoutWho=None, user_name=None,
               requisites=None, verified=None):
    if name:
        cur.execute(''' UPDATE Applicants SET name=? WHERE id=? ''', [name, id])
    elif links:
        cur.execute(''' UPDATE Applicants SET links=? WHERE id=? ''', [links, id])
    elif price:
        cur.execute(''' UPDATE Applicants SET price=? WHERE id=? ''', [price, id])
    elif info:
        cur.execute(''' UPDATE Applicants SET info=? WHERE id=? ''', [info, id])
    elif withWho:
        cur.execute(''' UPDATE Applicants SET withWHo=? WHERE id=? ''', [withWho, id])
    elif withoutWho:
        cur.execute(''' UPDATE Applicants SET withoutWho=? WHERE id=? ''', [withoutWho, id])
    elif requisites:
        cur.execute(''' UPDATE Applicants SET requisites=? WHERE id=? ''', [requisites, id])
    else:
        if verified == None:
            cur.execute(''' INSERT INTO Applicants(id, username) VALUES (?, ?)''', [id, user_name])
        elif verified:
            cur.execute(''' SELECT * FROM Applicants WHERE id=? ''', [id])
            app = cur.fetchone()
            if app:
                cur.execute(''' INSERT INTO Psycho VALUES (?, ?, ?, 0.0) ''', [app[0], app[1], app[4]])
                cur.execute(''' DELETE FROM Applicants WHERE id=? ''', [id])
        else:
            cur.execute(''' DELETE FROM Applicants WHERE id=? ''', [id])
    conn.commit()


def delete_psycho(id: int):
    cur.execute(''' DELETE FROM Psycho WHERE id=? ''', [id])
    cur.execute(''' DELETE FROM Photos WHERE psycho=? ''', [id])
    conn.commit()


def is_applicant(id: int):
    cur.execute(''' SELECT * FROM Applicants WHERE id=? ''', [id])
    return cur.fetchone()


def get_applicants():
    cur.execute(''' SELECT * FROM Applicants ''')
    return cur.fetchall()


def get_applicant(id: int):
    cur.execute(''' SELECT * FROM Applicants WHERE id=? ''', [id])
    return cur.fetchone()


def remove_applicant(id: int):
    cur.execute(''' DELETE FROM Applicants WHERE id=? ''', [id])
    cur.execute(''' DELETE FROM Photos WHERE psycho=? ''', [id])
    conn.commit()


def get_stat():
    cur.execute(''' SELECT count(*) FROM Users ''')
    users = cur.fetchone()[0]
    cur.execute(''' SELECT count(*) FROM Psycho ''')
    psycho = cur.fetchone()[0]
    cur.execute(''' SELECT date FROM Sessions ''')
    ses = cur.fetchall()
    today_sessions = 0
    month_sessions = 0
    a = datetime.now()
    for session in ses:
        b = datetime.fromtimestamp(session[0])
        if a.year == b.year:
            if a.month == b.month:
                month_sessions += 1
                if a.day == b.day:
                    today_sessions += 1
    return (users, psycho, today_sessions, month_sessions)


def get_stat_file():
    pass


def add_photos(psycho: int, photo_ids: list[str]):
    for photo in photo_ids:
        cur.execute(''' INSERT INTO Photos VALUES (?, ?) ''', [photo, psycho])
    conn.commit()


def get_photos(psycho: int):
    cur.execute(''' SELECT id FROM Photos WHERE psycho=? ''', [psycho])
    res = []
    for el in cur.fetchall():
        res.append(el[0])
    return res


def get_categories():
    cur.execute(''' SELECT * FROM Categories ''')
    return cur.fetchall()


def get_categories_lev0():
    cur.execute(''' SELECT * FROM Categories WHERE parent=0 ''')
    return cur.fetchall()


def get_subcategories_by_parent(parent: int):
    cur.execute(''' SELECT * FROM Categories WHERE parent=? ''', [parent])
    return cur.fetchall()


def get_category_by_id(id: int):
    cur.execute(''' SELECT * FROM Categories WHERE id=? ''', [id])
    return cur.fetchone()


# PANELS
global main_menu
main_menu = types.ReplyKeyboardMarkup([['👨‍💼 Пригласить психолога'], ['👨‍🔧 Техподдержка', '🕘 История сессий']],
                                      resize_keyboard=True, one_time_keyboard=True)

global user_presession_menu
user_presession_menu = types.ReplyKeyboardMarkup([['⬅️ К категориям', '✅ Продолжить']],
                                                 resize_keyboard=True, one_time_keyboard=True)

global psycho_menu
psycho_menu = types.ReplyKeyboardMarkup([['Активные заявки'], ['👨‍💼 Информация', '📖 Рабочие категории']], resize_keyboard=True,
                                        one_time_keyboard=True)

global psycho_cat_menu_level1
psycho_cat_menu_level1 = types.ReplyKeyboardMarkup([['❎ Отмена', '✅ Сохранить Категории']], resize_keyboard=True,
                                                   one_time_keyboard=True)

global aplicant_cat_menu_level1
aplicant_cat_menu_level1 = types.ReplyKeyboardMarkup([['✅ Сохранить Категории']], resize_keyboard=True,
                                                     one_time_keyboard=True)

global psycho_cat_menu_level2
psycho_cat_menu_level2 = types.ReplyKeyboardMarkup([['⬅️ Назад', '✅ Сохранить Категории']], resize_keyboard=True,
                                                   one_time_keyboard=True)

global psycho_active_session_menu
psycho_active_session_menu = types.ReplyKeyboardMarkup([['❎ Остановить Сессию']], resize_keyboard=True,
                                                       one_time_keyboard=True)

global admin_menu
admin_menu = types.ReplyKeyboardMarkup([['Обращения', 'Баны'], ['📝 Статистика']], resize_keyboard=True,
                                       one_time_keyboard=True)


def set_user_main_cat(id: int, cat_id: int):
    cur.execute(''' UPDATE Users SET temp_main_cat=? WHERE id=? ''', [cat_id, id])
    conn.commit()


def get_user_main_cat(id: int):
    cur.execute(''' SELECT temp_main_cat FROM Users WHERE id=? ''', [id])
    temp_main_cat = cur.fetchone()[0]
    return temp_main_cat


def append_user_cats(id: int, cat_id: int):
    user_cats = get_user_cats(id)
    user_cats.append(cat_id)
    temp_cats = ' '.join(map(str, user_cats))
    cur.execute(''' UPDATE Users SET temp_cats=? WHERE id=? ''', [temp_cats, id])
    conn.commit()


def set_user_cats(id: int, cats: list):
    if len(cats) > 0:
        temp_cats = ' '.join(map(str, cats))
        cur.execute(''' UPDATE Users SET temp_cats=? WHERE id=? ''', [temp_cats, id])
        conn.commit()


def get_user_cats(id: int):
    cur.execute(''' SELECT temp_cats FROM Users WHERE id=? ''', [id])
    temp_cats = cur.fetchone()[0]
    if temp_cats:
        temp_cats = temp_cats.split(" ")
        if len(temp_cats) > 0:
            temp_cats = list(map(int, temp_cats))
        else:
            temp_cats = []
    else:
        temp_cats = []
    return temp_cats


def set_psy_cats(cats: list):
    global psy_cats
    psy_cats = cats


# CHAT HANDLER
@dp.message_handler(content_types=[types.ContentType.ANIMATION,
                                   types.ContentType.AUDIO,
                                   types.ContentType.VIDEO,
                                   types.ContentType.VIDEO_NOTE,
                                   types.ContentType.STICKER,
                                   types.ContentType.VOICE,
                                   types.ContentType.DOCUMENT
                                   ])
async def files(msg: types.Message):
    session = get_sessions(member=msg.from_user.id)
    if session:
        session = list(session)
        # Здесь надо еще будет добавление в лог чата
        session.pop(session.index(msg.from_user.id))
        to = session[1]
        await bot.copy_message(to, msg.from_user.id, msg.message_id)


@dp.message_handler(content_types=[types.ContentType.PHOTO])
async def photo(msg: types.Message):
    session = get_sessions(member=msg.from_user.id)
    app = is_applicant(msg.from_user.id)
    if session:
        session = list(session)
        # Здесь надо еще будет добавление в лог чата
        session.pop(session.index(msg.from_user.id))
        to = session[1]
        await bot.copy_message(to, msg.from_user.id, msg.message_id)
    elif app:
        if app[8] == '1':
            k = types.InlineKeyboardMarkup()
            k.add(types.InlineKeyboardButton("Подтвердить", callback_data=f"approve{msg.from_user.id}"))
            for admin in get_admins():
                await bot.send_photo(admin, msg.photo[0].file_id, caption="Подтвердите транзакцию", reply_markup=k)
            await msg.answer("Ожидайте подтверждение оплаты")
        else:
            add_photos(msg.from_user.id, [msg.photo[0].file_id])


@dp.message_handler(commands=['stop'])
async def stop_chat(msg: types.Message):
    session = get_sessions(member=msg.from_user.id)
    if session:
        if get_psychos(msg.from_user.id):
            end_session(msg.from_user.id)
            k = types.InlineKeyboardMarkup()
            for i in range(5):
                k.add(types.InlineKeyboardButton(f"{(5 - i) * '⭐️'}", callback_data=f"&{session[0]}&{5 - i}"))
            try:
                await bot.send_message(session[1], "Психолог завершил сессию! Укажите Вашу оценку данной сессии:",
                                       reply_markup=k)
            except exceptions.BotBlocked:
                pass
            except exceptions.ChatNotFound:
                pass
            except exceptions.RetryAfter as e:
                pass
            except exceptions.UserDeactivated:
                pass
            except exceptions.TelegramAPIError:
                pass
            await msg.answer("Сессия завершена!\nМеню психолога", reply_markup=psycho_menu)


# COMMANDS HANDLER
@dp.message_handler(commands=['evaluationTest'])
async def evaluation_test(msg: types.Message):
    k = types.InlineKeyboardMarkup()
    for i in range(5):
        k.add(types.InlineKeyboardButton(f"{(5 - i) * '⭐️'}", callback_data=f"evaluationTest{5 - i}"))
    await msg.answer("Психолог завершил сессию! Укажите Вашу оценку данной сессии:",
                     reply_markup=k)


@dp.message_handler(commands=['showMenuTest'])
async def show_menu_test(msg: types.Message):
    await msg.answer("Главное меню", reply_markup=main_menu)


@dp.message_handler(commands=['start'])
async def start(msg: types.Message):
    if not (get_sessions(member=msg.from_user.id)):
        usr = get_user(msg.from_user.id)
        if usr:
            if not (usr[3]):
                if usr[1] == None:
                    add_user(msg.from_user.id, name=msg.text.strip())
                    await msg.answer("Сколько Вам лет?")
                elif usr[2] == None:
                    age = int(msg.text)
                    add_user(msg.from_user.id, age=age)
                    await msg.answer("Добро пожаловать!\nГлавное меню", reply_markup=main_menu)
                else:
                    await msg.answer("Добро пожаловать!\nГлавное меню", reply_markup=main_menu)
        else:
            # REGISTRATION
            add_user(msg.from_user.id)
            await msg.answer(
                f"Здесь есть психолог, который вас услышит💚\n\n"
                f"Заполните простую анкету и мы подберем психолога, специализирующегося на вашем запросе.\n\n"
                f"Мы понимаем, найти подходящего психолога – это сложно. Не каждый специалист работает с вашей конкретной проблемой, и, даже если работает, результаты могут быть не всегда эффективными.\n\n"
                f"Для этого мы создали сервис PsyTetrica✨\n\n"
                f"Мы предложим вам профессионала с опытом работы, который специализируется именно на вашем запросе.\n\n"
                f"1️⃣Заполните простую анкету и мгновенно получите психолога с опытом работы в вашей области.\n\n"
                f"Заполните информацию о себе, напишите запрос и выберите от 2 до 5 категории запросов.\n\n"
                f"Более 1,500 человек уже воспользовались услугами PsyTetrica за последний месяц!\n\n"
                f"2️⃣Прямо в чате вы можете познакомится с психологом и задать вопросы о терапии.\n\n"
                f"Все наши специалисты посещают обязательные интервизии от ведущего психолога сервиса. У нас есть более 100 проверенных психологов.\n\n"
                f"3️⃣Запишитесь на онлайн-сессию с психологом прямо в боте, в дальнейшем вы можете связаться со специалистом в удобном для вас мессенджере\n\n"
                f"Запись через PsyTetrica гарантирует вашу безопасность и сохранность данных, обращение анонимно, пока вы не выберете психолога.\n\n"
                f"PsyTetrica делает процесс психотерапии удобным. Мы берем на себя все организационные вопросы, чтобы вы могли сосредоточиться на самом главном – на себе и своих эмоциях💙"
                f"Не забудьте подписаться на наш канал: https://t.me/chat_psytetrica")

            chat_id = msg.chat.id
            for file_path in register_docx_files:
                with open(file_path, "rb") as docx_file:
                    await bot.send_document(chat_id=chat_id, document=docx_file)

            await msg.answer("Как к Вам обращаться?")


@dp.message_handler(commands=['done'])
async def done(msg: types.Message):
    if is_applicant(msg.from_user.id):
        await msg.answer("Ваша заявка принята на рассмотрение! Ожидайте ответа от администратора")

        k = types.InlineKeyboardMarkup()

        for categories in get_categories_lev0():
            k.add(types.InlineKeyboardButton(categories[2], callback_data=f"psyCatChoose={categories[0]}"))
        await msg.delete()
        await msg.answer("А пока, укажите с какими категориями Вы работаете:", reply_markup=k)
        if get_psychos(msg.from_user.id):
            await msg.answer("Основные Категории", reply_markup=psycho_cat_menu_level1)
        else:
            await msg.answer("Основные Категории", reply_markup=aplicant_cat_menu_level1)

        for admin_usr in get_admins():
            try:
                await bot.send_message(admin_usr,
                                       "Новая заявка на добавление психолога! Посмотреть заявки - /adminApplicants")
            except exceptions.BotBlocked:
                pass
            except exceptions.ChatNotFound:
                pass
            except exceptions.RetryAfter as e:
                pass
            except exceptions.UserDeactivated:
                pass
            except exceptions.TelegramAPIError:
                pass


@dp.message_handler(commands=['work'])
async def work(msg: types.Message):
    if not (get_sessions(member=msg.from_user.id)):
        psycho = get_psychos(msg.from_user.id)
        if psycho:
            await msg.answer("Меню психолога", reply_markup=psycho_menu)


@dp.message_handler(commands=['requests'])
async def requests(msg: types.Message):
    if not (get_sessions(member=msg.from_user.id)):
        psycho = get_psychos(msg.from_user.id)
        if psycho:
            reqs = get_not_occupied_requests()
            n = 0
            for req in reqs:
                request_psychos = req[4]
                if request_psychos:
                    request_psychos = request_psychos.split(" ")
                    if len(request_psychos) > 0:
                        request_psychos = list(map(int, request_psychos))
                        if psycho[0] in request_psychos:
                            if req[3]:
                                n += 1
                                request_cats = get_request_categories_by_req_id(req[0])
                                prepared_request_cats = []

                                for request_cat_id in request_cats:
                                    category_by_id = get_category_by_id(request_cat_id[3])
                                    prepared_request_cats.append(category_by_id[2])

                                if len(prepared_request_cats) > 0:
                                    prepared_request_cats = ', '.join(prepared_request_cats)
                                else:
                                    prepared_request_cats = 'Без категорий'
                                user = get_user(req[1])
                                k = types.InlineKeyboardMarkup()
                                k.add(types.InlineKeyboardButton("Принять", callback_data=f"?{req[0]}"))
                                await msg.answer(
                                    f"Заявка #{req[0]}\nИмя: {user[1]}\nВозраст: {user[2]}\nКатегории: {prepared_request_cats}\nПроблема: {req[2]}\n✅ Заявка открыта",
                                    reply_markup=k)
            if n == 0:
                await msg.answer("Активных заявок нет!", reply_markup=psycho_menu)
            else:
                await msg.answer("Меню психолога", reply_markup=psycho_menu)
@dp.message_handler(commands=['apply'])
async def apply(msg: types.Message):
    if get_user(msg.from_user.id):
        if not (get_sessions(member=msg.from_user.id)):
            applicants = get_applicants()
            is_app = False
            for app in applicants:
                if msg.from_user.id == app[0]:
                    is_app = True
                    break
            if is_app:
                await msg.answer("Вы уже подали заявку!")
            elif get_psychos(msg.from_user.id):
                await msg.answer("Вы уже психолог!")
            else:
                add_psycho(msg.from_user.id, user_name=msg.from_user.mention)
                await msg.answer(
                    "Сейчас Вы должны будете заполнить анкету, после проверки которой, Вы сможете начать работать!")
                await msg.answer("Введите ваши фамилию и имя")


@dp.message_handler(commands=['newRequests'])
async def newRequests(msg: types.Message):
    if not (get_sessions(member=msg.from_user.id)):
        if msg.from_user.id in get_admins():
            reqs = get_requests()
            n = 0
            for req in reqs:
                if not (req[3]):
                    user = get_user(req[1])
                    request_cats = get_request_categories_by_req_id(req[0])
                    prepared_request_cats = []

                    for request_cat_id in request_cats:
                        category_by_id = get_category_by_id(request_cat_id[3])
                        prepared_request_cats.append(category_by_id[2])

                    if len(prepared_request_cats) > 0:
                        prepared_request_cats = ', '.join(prepared_request_cats)
                    else:
                        prepared_request_cats = 'Без категорий'
                    n += 1
                    k = types.InlineKeyboardMarkup(row_width=2)
                    k.add(types.InlineKeyboardButton("✅", callback_data=f"+{req[0]}"))
                    k.add(types.InlineKeyboardButton("⛔️", callback_data=f"-{req[0]}"))
                    await msg.answer(
                        f"Заявка #{req[0]}\nПроблема: {req[2]}\nИнформация о пользователе\nИмя: {user[1]}\nВозраст: {user[2]}\nКатегории: {prepared_request_cats}",
                        reply_markup=k)
            if n == 0:
                await msg.answer("Нет необработанных заявок!")


@dp.message_handler(commands=['admin'])
async def admin(msg: types.Message):
    if not (get_sessions(member=msg.from_user.id)):
        if msg.from_user.id in get_admins():
            await msg.answer("Админпанель", reply_markup=admin_menu)


@dp.message_handler(commands=['addAdmin'])
async def addAdmin(msg: types.Message):
    if not (get_sessions(member=msg.from_user.id)):
        if msg.from_user.id in get_admins():
            admin_id = int(msg.text.replace('/addAdmin', '').strip())
            if admin_id in get_admins():
                await msg.answer("Пользователь уже является модератором!")
            else:
                try:
                    await bot.send_message(admin_id,
                                           "Вы теперь модератор сервиса! Для доступа к меню, введите команду - /admin")
                    add_admin(admin_id)
                    await msg.answer("Админ добавлен!")
                except exceptions.ChatNotFound:
                    await msg.answer("Не удалось добавить модератора, возможно Вы неправтльно ввели его id!")


@dp.message_handler(commands=['deleteAdmin'])
async def deleteAdmin(msg: types.Message):
    if not (get_sessions(member=msg.from_user.id)):
        if msg.from_user.id in get_admins():
            remove_admin(int(msg.text.replace('/deleteAdmin', '').strip()))
            await msg.answer("Админ удален!")


@dp.message_handler(commands=['adminApplicants'])
async def adminApplicants(msg: types.Message):
    if not (get_sessions(member=msg.from_user.id)):
        if msg.from_user.id in get_admins():
            apps = get_applicants()
            if len(apps) == 0:
                await msg.answer("Нет новых заявлений!")
            else:
                for app in apps:
                    k = types.InlineKeyboardMarkup()
                    k.row(types.InlineKeyboardButton("Одобрить", callback_data=f"accept{app[0]}"),
                          types.InlineKeyboardButton("Отклонить", callback_data=f"deny{app[0]}"))
                    group = types.MediaGroup()
                    if len(get_photos(app[0])) > 0:
                        kol = 0
                        for el in get_photos(app[0]):
                            kol += 1
                            group.attach_photo(el)
                            if kol == 10:
                                break
                        await bot.send_media_group(msg.from_user.id, group)
                    await msg.answer(
                        f"Заявка {app[7]}\nИмя - {app[1]}\nСсылки: {app[2]}\nЦена сессии: {app[3]}\nОписание:\n{app[4]}\nС кем работаю: {app[5]}\nС кем не работаю: {app[6]}",
                        reply_markup=k)


@dp.message_handler(commands=['techRequests'])
async def techRequests(msg: types.Message):
    if not (get_sessions(member=msg.from_user.id)):
        if msg.from_user.id in get_admins():
            if len(get_techRequests()) > 0:
                for req in get_techRequests():
                    k = types.InlineKeyboardMarkup()
                    k.add(types.InlineKeyboardButton("Завершено", callback_data=f"!{req[0]}"))
                    await msg.answer(f"Обращение #{req[0]}\nПользователь: {req[2]}({req[1]})\nПроблема: {req[3]}",
                                     reply_markup=k)
            else:
                await msg.answer("Нет новых обращений!")


@dp.message_handler(commands=['deletePsycho'])
async def deletePsycho(msg: types.Message):
    psycho_id = int(msg.text.replace('/deletePsycho', '').strip())
    delete_psycho(psycho_id)
    await msg.answer("Психолог удален!")


@dp.message_handler(commands=['ban'])
async def ban_user(msg: types.Message):
    if msg.from_user.id in get_admins():
        try:
            ban(int(msg.text.replace("/ban", "")))
            await msg.answer("Пользователь забанен!")
        except ValueError:
            await msg.answer("Неверный формат id пользователя!")


@dp.message_handler(commands=['post'])
async def post(msg: types.Message):
    if msg.from_user.id in get_admins():
        try:
            post = msg.reply_to_message.message_id
            await msg.answer("Рассылка началась!")
            a, b = 0, 0
            for user in get_users():
                b += 1
                try:
                    await bot.copy_message(user[0], msg.from_user.id, post)
                    a += 1
                except Exception:
                    pass
            await msg.answer(f"Рассылка завершена!({a}/{b} пользователей получили объявление)")
        except AttributeError:
            await msg.answer("Вы не ссылаетесь ни на кое сообщение!")


async def clear_chat_10_min(msg: types.Message):
    # Calculate the DateTime object for the time 10 minutes ago
    time_threshold = datetime.now() - timedelta(minutes=10)

    # Get the chat ID
    chat_id = msg.chat.id

    # Fetch all messages for the last 10 minutes
    messages = await bot.get_chat_history(chat_id, limit=100)

    # Iterate through each message and delete if its date is within the time threshold
    for message in messages:
        if message.date < time_threshold:
            await bot.delete_message(chat_id, message.message_id)


# TEXT HANDLER
@dp.message_handler(content_types=['text'])
async def text(msg: types.Message):
    # USERS TEXT
    user_id = msg.from_user.id
    usr = get_user(user_id)
    chat_id = msg.chat.id
    message_id = msg.message_id
    if usr:
        match msg.text:
            case '⬅️ К категориям':
                k = types.InlineKeyboardMarkup()

                for categories in get_categories_lev0():
                    k.add(types.InlineKeyboardButton(categories[2], callback_data=f"=categoryChoose={categories[0]}"))

                await bot.delete_message(chat_id, message_id=message_id - 2)
                await bot.delete_message(chat_id, message_id=message_id - 1)
                await msg.delete()

                await msg.answer("Что бы Вы хотели обсудить в первую очередь? (выберите до 5 категорий)",
                                 reply_markup=k)
            case '✅ Продолжить':
                cats_arr = get_user_cats(user_id)
                k = types.InlineKeyboardMarkup()

                await bot.delete_message(chat_id, message_id=message_id - 2)
                await bot.delete_message(chat_id, message_id=message_id - 1)
                await msg.delete()

                if cats_arr and len(cats_arr) < 2:
                    for categories in get_categories_lev0():
                        k.add(
                            types.InlineKeyboardButton(categories[2], callback_data=f"=categoryChoose={categories[0]}"))

                    await msg.answer("Что бы Вы хотели обсудить в первую очередь? (выберите до 5 категорий)",
                                     reply_markup=k)
                else:
                    prepare_cats = get_user_cats(user_id)
                    # prepare_cats = list(set(get_user_cats()))
                    for category in prepare_cats:
                        cat_arr = get_category_by_id(category)
                        category_name = "✅ " + cat_arr[2]
                        k.add(types.InlineKeyboardButton(category_name, callback_data="void"))

                    try:
                        await bot.send_message(chat_id, "Выбранные темы:", reply_markup=k)
                        await bot.send_message(chat_id, "Опишите Вашу проблему:", reply_markup=types.ReplyKeyboardRemove())
                    except exceptions.BotBlocked:
                        pass
                    except exceptions.ChatNotFound:
                        pass
                    except exceptions.RetryAfter as e:
                        pass
                    except exceptions.UserDeactivated:
                        pass
                    except exceptions.TelegramAPIError:
                        pass
                    # add_request(user_id)
                    last_req = get_last_request_by_user_id(user_id)
                    # await bot.send_message(chat_id, "ыыыыыы")
                    # await bot.send_message(chat_id, str(last_req[0]))
                    # await bot.send_message(chat_id, ', '.join(map(str, prepare_cats)))
                    delete_request_categories(user_id)
                    # await bot.send_message(chat_id, "ыыыыыы11")
                    for cat in prepare_cats:
                        add_request_category(user_id, last_req[0], cat)

                    # await bot.send_message(chat_id, "ыыыыыы22")
            case '👨‍💼 Информация':
                k = types.InlineKeyboardMarkup()
                psycho_categories_temp = []
                psycho_categories = get_psycho_categories(user_id)
                for category in psycho_categories:
                    if category[0] not in psycho_categories_temp:
                        cat_arr = get_category_by_id(category[0])
                        category_name = "✅ " + cat_arr[2]
                        k.add(types.InlineKeyboardButton(category_name, callback_data="void"))
                        psycho_categories_temp.append(category[0])

                await msg.delete()
                await msg.answer("Ваши категории:", reply_markup=k)
                await msg.answer("Меню", reply_markup=psycho_menu)
            case '📖 Рабочие категории':
                k = types.InlineKeyboardMarkup()

                for categories in get_categories_lev0():
                    k.add(types.InlineKeyboardButton(categories[2], callback_data=f"psyCatChoose={categories[0]}"))
                await msg.delete()
                await msg.answer("Укажите с какими категориями Вы работаете:", reply_markup=k)
                if get_psychos(msg.from_user.id):
                    await msg.answer("Основные Категории", reply_markup=psycho_cat_menu_level1)
                else:
                    await msg.answer("Основные Категории", reply_markup=aplicant_cat_menu_level1)

            case '✅ Сохранить Категории':
                await bot.delete_message(chat_id, message_id=message_id - 2)
                await bot.delete_message(chat_id, message_id=message_id - 1)
                await msg.delete()
                psycho_id = msg.from_user.id
                delete_psycho_category(psycho_id)
                psycho_cats = get_user_cats(psycho_id)
                for psycho_cat in psycho_cats:
                    set_psycho_category(psycho_id, psycho_cat)

                await msg.answer("Категории Сохранены", reply_markup=psycho_menu)
            case '❎ Отмена':
                await bot.delete_message(chat_id, message_id=message_id - 2)
                await bot.delete_message(chat_id, message_id=message_id - 1)
                await msg.delete()
                await msg.answer("Меню психолога", reply_markup=psycho_menu)
            case '⬅️ Назад':
                k = types.InlineKeyboardMarkup()

                for categories in get_categories_lev0():
                    k.add(types.InlineKeyboardButton(categories[2], callback_data=f"psyCatChoose={categories[0]}"))
                await bot.delete_message(chat_id, message_id=message_id - 2)
                await bot.delete_message(chat_id, message_id=message_id - 1)
                await msg.delete()
                await msg.answer("Укажите с какими категориями Вы работаете:", reply_markup=k)
                if get_psychos(msg.from_user.id):
                    await msg.answer("Основные Категории", reply_markup=psycho_cat_menu_level1)
                else:
                    await msg.answer("Основные Категории", reply_markup=aplicant_cat_menu_level1)
            case _:
                if not (usr[3]):
                    if usr[1] == None:
                        add_user(msg.from_user.id, name=msg.text.strip())
                        await msg.answer("Сколько Вам лет?")
                    elif usr[2] == None:
                        age = msg.text
                        if age.isdigit():
                            age = int(age)
                        else:
                            age = 18

                        add_user(msg.from_user.id, age=age)
                        k = types.InlineKeyboardMarkup()

                        for categories in get_categories_lev0():
                            k.add(types.InlineKeyboardButton(categories[2],
                                                             callback_data=f"=categoryChoose={categories[0]}"))
                        await msg.delete()
                        # k.add(types.InlineKeyboardButton("Отмена", callback_data="cancelRequest"))
                        # await bot.delete_message(chat_id=msg.chat.id, message_id=msg.message_id - 1)
                        await msg.answer("Что бы Вы хотели обсудить в первую очередь? (выберите до 5 категорий)",
                                         reply_markup=k)
                    elif usr[6]:
                        await msg.answer("Добро пожаловать!\nГлавное меню", reply_markup=main_menu)
                    else:
                        session = get_sessions(member=msg.from_user.id)
                        if session:
                            session = list(session)
                            # Здесь надо еще будет добавление в лог чата
                            session.pop(session.index(msg.from_user.id))
                            to = session[1]
                            await bot.copy_message(to, msg.from_user.id, msg.message_id)
                        elif is_applicant(msg.from_user.id):
                            app = is_applicant(msg.from_user.id)
                            if app[1] == None:
                                add_psycho(msg.from_user.id, name=msg.text.strip())
                                await msg.answer("Укажите ссылки на ваши ресурсы(соц. сети, сайт и т.д.)")
                            elif app[2] == None:
                                add_psycho(msg.from_user.id, links=msg.text.strip())
                                await msg.answer("Укажите желаемую оплату одной сессии")
                            elif app[3] == None:
                                add_psycho(msg.from_user.id, price=msg.text.strip())
                                await msg.answer("Расскажите о себе")
                            elif app[4] == None:
                                add_psycho(msg.from_user.id, info=msg.text.strip())
                                await msg.answer("Напишите подходы в которых вы работаете")
                            # elif app[5] == None:
                            #     add_psycho(msg.from_user.id, withWho=msg.text.strip())
                            #     await msg.answer("С какими клиентами Вы неготоВы работать?")
                            elif app[6] == None:
                                add_psycho(msg.from_user.id, withoutWho=msg.text.strip())
                                await msg.answer("Пришлите ваши фотографии, когда пришлете все фото отправте /done")
                            # elif app[5] == None:
                            #     add_psycho(msg.from_user.id, withWho=msg.text.strip())
                            #     await msg.answer("С какими клиентами Вы неготоВы работать?")
                        else:
                            match msg.text:
                                case '👨‍💼 Пригласить психолога':
                                    req = get_requests(msg.from_user.id)
                                    if req:
                                        k = types.InlineKeyboardMarkup()
                                        k.add(types.InlineKeyboardButton("Отмена", callback_data="cancelRequest"))
                                        await msg.answer("Вы уже подали заявку!", reply_markup=k)
                                    else:
                                        add_request(msg.from_user.id)
                                        k = types.InlineKeyboardMarkup()

                                        for categories in get_categories_lev0():
                                            k.add(types.InlineKeyboardButton(categories[2],
                                                                             callback_data=f"=categoryChoose={categories[0]}"))

                                        k.add(types.InlineKeyboardButton("Отмена", callback_data="cancelRequest"))
                                        await msg.delete()
                                        await msg.answer(
                                            "Что бы Вы хотели обсудить в первую очередь? (выберите до 5 категорий)",
                                            reply_markup=k)
                                case '👨‍🔧 Техподдержка':
                                    add_techRequest(user=msg.from_user.id)
                                    k = types.InlineKeyboardMarkup()
                                    k.add(types.InlineKeyboardButton("Отмена", callback_data="cancelTechRequest"))
                                    await msg.answer(
                                        "Если у вас произошла ошибка, или есть вопросы по работе нашего сервиса, напишите нам",
                                        reply_markup=k)
                                case '🕘 История сессий':
                                    sessions = get_sessions(user=msg.from_user.id)
                                    if len(sessions) > 0:
                                        for session in sessions:
                                            psycho = get_psychos(session[2])
                                            # k = types.InlineKeyboardMarkup()
                                            # k.add(types.InlineKeyboardButton("⭐️", callback_data=f"@{session[2]}"))
                                            await msg.answer(
                                                f"Сессия #{session[0]}\nДата: {datetime.fromtimestamp(session[5]).strftime('%d/%m/%Y %H:%M')}\nПсихолог: {psycho[1]}\nВаша оценка: {session[4] * '⭐️'}",
                                                reply_markup=main_menu)
                                    else:
                                        await msg.answer(
                                            f"Пусто",
                                            reply_markup=main_menu)
                                case _:
                                    req = get_requests(msg.from_user.id)
                                    if req:
                                        if req[2] == None:
                                            add_request(user_id, msg.text.strip())
                                            user_cats = get_user_cats(user_id)
                                            user_cats_len = len(user_cats)

                                            user_cats_str = ' '.join(map(str, user_cats))

                                            psychos_by_categories = get_psychos_by_categories_ids(user_cats_str)
                                            prepare_psychos_arr = []

                                            for psycho in psychos_by_categories:
                                                if psycho[1] == user_cats_len:
                                                    prepare_psychos_arr.append(psycho[0])
                                            prepare_psychos_str = ' '.join(map(str, prepare_psychos_arr))
                                            add_psychos_to_request(req[0], prepare_psychos_str)
                                            await msg.answer(
                                                "Ваша заявка принята в обработку!\n\nСначала ее проверит администратор, и, после успешной проверки, с Вами свяжется психолог!")

                                            for adm in get_admins():
                                                try:
                                                    await bot.send_message(chat_id=adm, text="Новая заявка!\nПосмтортеть непроверенные заявки - /NewRequests")
                                                except exceptions.BotBlocked:
                                                    pass
                                                except exceptions.ChatNotFound:
                                                    pass
                                                except exceptions.RetryAfter as e:
                                                    pass
                                                except exceptions.UserDeactivated:
                                                    pass
                                                except exceptions.TelegramAPIError:
                                                    pass

                                    techReq = get_techRequests(msg.from_user.id)
                                    if techReq:
                                        if techReq[3] == None:
                                            add_techRequest(user=msg.from_user.id, problem=msg.text.strip(),
                                                            user_nickname=msg.from_user.mention)
                                            await msg.answer(
                                                "Ваша заявка принята! Если потребуется, с Вами свяжется один из наших администраторов!")
                                            for adm in get_admins():
                                                try:
                                                    await bot.send_message(adm,
                                                                           "Новое обращение в техподдержку! Посмотреть обращения - /techRequests")
                                                except exceptions.BotBlocked:
                                                    pass
                                                except exceptions.ChatNotFound:
                                                    pass
                                                except exceptions.RetryAfter as e:
                                                    pass
                                                except exceptions.UserDeactivated:
                                                    pass
                                                except exceptions.TelegramAPIError:
                                                    pass

    else:
        # REGISTRATION
        match msg.text:
            case _:
                add_user(msg.from_user.id)
                await msg.answer(
                    f"Здесь есть психолог, который вас услышит💚\n\n"
                    f"Заполните простую анкету и мы подберем психолога, специализирующегося на вашем запросе.\n\n"
                    f"Мы понимаем, найти подходящего психолога – это сложно. Не каждый специалист работает с вашей конкретной проблемой, и, даже если работает, результаты могут быть не всегда эффективными.\n\n"
                    f"Для этого мы создали сервис PsyTetrica✨\n\n"
                    f"Мы предложим вам профессионала с опытом работы, который специализируется именно на вашем запросе.\n\n"
                    f"1️⃣Заполните простую анкету и мгновенно получите психолога с опытом работы в вашей области.\n\n"
                    f"Заполните информацию о себе, напишите запрос и выберите от 2 до 5 категории запросов.\n\n"
                    f"Более 1,500 человек уже воспользовались услугами PsyTetrica за последний месяц!\n\n"
                    f"2️⃣Прямо в чате вы можете познакомится с психологом и задать вопросы о терапии.\n\n"
                    f"Все наши специалисты посещают обязательные интервизии от ведущего психолога сервиса. У нас есть более 100 проверенных психологов.\n\n"
                    f"3️⃣Запишитесь на онлайн-сессию с психологом прямо в боте, в дальнейшем вы можете связаться со специалистом в удобном для вас мессенджере\n\n"
                    f"PsyTetrica делает процесс психотерапии удобным. Мы берем на себя все организационные вопросы, чтобы вы могли сосредоточиться на самом главном – на себе и своих эмоциях💙"
                    f"Не забудьте подписаться на наш канал: https://t.me/chat_psytetrica")

                chat_id = msg.chat.id
                for file_path in register_docx_files:
                    with open(file_path, "rb") as docx_file:
                        await bot.send_document(chat_id=chat_id, document=docx_file)

                await msg.answer("Как к Вам обращаться?")

    # PSYCHO TEXT
    psycho = get_psychos(msg.from_user.id)
    sessions = get_sessions(member=msg.from_user.id)
    if psycho:
        if sessions:
            match msg.text:
                case '❎ Остановить Сессию':
                    session = get_sessions(member=msg.from_user.id)
                    if session:
                        if get_psychos(msg.from_user.id):
                            end_session(msg.from_user.id)
                            k = types.InlineKeyboardMarkup()
                            for i in range(5):
                                k.add(types.InlineKeyboardButton(f"{(5 - i) * '⭐️'}",
                                                                 callback_data=f"&{session[0]}&{5 - i}"))
                            #                             await bot.delete_message(session[1], message_id=message_id - 1)
                            #                             await bot.delete_message(session[1], message_id=message_id)
                            try:
                                try:
                                    await bot.delete_message(session[1], message_id=msg.message_id)
                                except Exception:
                                    pass
                                await msg.delete()
                                await bot.send_message(session[1],
                                                       "Психолог завершил сессию! Укажите Вашу оценку данной сессии:",
                                                       reply_markup=k)
                            except exceptions.BotBlocked:
                                pass
                            except exceptions.ChatNotFound:
                                pass
                            except exceptions.RetryAfter as e:
                                pass
                            except exceptions.UserDeactivated:
                                pass
                            except exceptions.TelegramAPIError:
                                pass
                            await msg.answer("Сессия завершена!\nМеню психолога", reply_markup=psycho_menu)
        else:
            match msg.text:
                case 'Активные заявки':
                    reqs = get_not_occupied_requests()
                    n = 0
                    for req in reqs:
                        request_psychos = req[4]
                        if request_psychos:
                            request_psychos = request_psychos.split(" ")
                            if len(request_psychos) > 0:
                                request_psychos = list(map(int, request_psychos))
                                if psycho[0] in request_psychos:
                                    if not req[5]:
                                        n += 1
                                        user = get_user(req[1])
                                        user_name = user[1]
                                        if user_name:
                                            user_name = user_name
                                        else:
                                            user_name = ""

                                        user_age = user[2]
                                        if user_age:
                                            user_age = str(user_age)
                                        else:
                                            user_age = ""
                                        request_cats = get_request_categories_by_req_id(req[0])
                                        prepared_request_cats = []

                                        for request_cat_id in request_cats:
                                            category_by_id = get_category_by_id(request_cat_id[3])
                                            prepared_request_cats.append(category_by_id[0])

                                        if len(prepared_request_cats) > 0:
                                            prepared_request_cats = ', '.join(prepared_request_cats)
                                        else:
                                            prepared_request_cats = 'Без категорий'

                                        req_cats = get_request_categories_by_req_id(req[0])
                                        req_cats_len = len(req_cats)
                                        psy_car_count = 0
                                        for cat in req_cats:
                                            psychos_category_count = 0
                                            category_exist = check_if_psychos_category_exist(msg.from_user.id, cat[3])
                                            if category_exist:
                                                psychos_category_count = len(category_exist)
                                            psy_car_count = psy_car_count + psychos_category_count

                                        if req_cats_len == psy_car_count:
                                            k = types.InlineKeyboardMarkup()
                                            k.add(types.InlineKeyboardButton("Принять", callback_data=f"?{req[0]}"))
                                            await msg.answer(f"Заявка #{req[0]}\nИмя: {user_name}\nВозраст: {user_age}\nКатегории: {prepared_request_cats}\nПроблема: {req[2]}", reply_markup=k)
                    if n == 0:
                        await msg.answer("Активных заявок нет!", reply_markup=psycho_menu)
                    else:
                        await msg.answer("Меню психолога", reply_markup=psycho_menu)
                case '👨‍💼 Информация':
                    k = types.InlineKeyboardMarkup()

                    psycho_categories_temp = []
                    psycho_categories = get_psycho_categories(msg.from_user.id)
                    for category in psycho_categories:
                        if category[0] not in psycho_categories_temp:
                            cat_arr = get_category_by_id(category[0])
                            category_name = "✅ " + cat_arr[2]
                            k.add(types.InlineKeyboardButton(category_name, callback_data="void"))
                            psycho_categories_temp.append(category[0])

                    await msg.delete()
                    await msg.answer("Ваши категории:", reply_markup=k)
                    await msg.answer("Категории Сохранены", reply_markup=psycho_menu)
                case '📖 Рабочие категории':
                    k = types.InlineKeyboardMarkup()

                    for categories in get_categories_lev0():
                        k.add(types.InlineKeyboardButton(categories[2], callback_data=f"psyCatChoose={categories[0]}"))
                    await msg.delete()
                    await msg.answer("Укажите с какими категориями Вы работаете:", reply_markup=k)
                    if get_psychos(msg.from_user.id):
                        await msg.answer("Основные Категории", reply_markup=psycho_cat_menu_level1)
                    else:
                        await msg.answer("Основные Категории", reply_markup=aplicant_cat_menu_level1)

                case '✅ Сохранить Категории':
                    await msg.delete()
                    await msg.answer("Категории Сохранены", reply_markup=psycho_menu)
                case '❎ Отмена':
                    await msg.delete()
                    await msg.answer("Меню психолога", reply_markup=psycho_menu)
                case '⬅️ Назад':
                    k = types.InlineKeyboardMarkup()

                    for categories in get_categories_lev0():
                        k.add(types.InlineKeyboardButton(categories[2], callback_data=f"psyCatChoose={categories[0]}"))
                    await msg.delete()
                    await msg.answer("Укажите с какими категориями Вы работаете:", reply_markup=k)

                    if get_psychos(msg.from_user.id):
                        await msg.answer("Основные Категории", reply_markup=psycho_cat_menu_level1)
                    else:
                        await msg.answer("Основные Категории", reply_markup=aplicant_cat_menu_level1)
                case '❎ Остановить Сессию':
                    session = get_sessions(member=msg.from_user.id)
                    if session:
                        if get_psychos(msg.from_user.id):
                            end_session(msg.from_user.id)
                            k = types.InlineKeyboardMarkup()
                            for i in range(5):
                                k.add(types.InlineKeyboardButton(f"{(5 - i) * '⭐️'}",
                                                                 callback_data=f"&{session[0]}&{5 - i}"))
                            #                             await bot.delete_message(session[1], message_id=message_id - 1)
                            #                             await bot.delete_message(session[1], message_id=message_id)

                            try:
                                try:
                                    await bot.delete_message(session[1], message_id=msg.message_id)
                                except Exception:
                                    pass
                                await msg.delete()
                                await bot.send_message(session[1],
                                                       "Психолог завершил сессию! Укажите Вашу оценку данной сессии:",
                                                       reply_markup=k)
                            except exceptions.BotBlocked:
                                pass
                            except exceptions.ChatNotFound:
                                pass
                            except exceptions.RetryAfter as e:
                                pass
                            except exceptions.UserDeactivated:
                                pass
                            except exceptions.TelegramAPIError:
                                pass
                            await msg.answer("Сессия завершена!\nМеню психолога", reply_markup=psycho_menu)

    # ADMINS TEXT
    if msg.from_user.id in get_admins():
        match msg.text:
            case 'Обращения':
                reqs = get_requests()
                n = 0
                for req in reqs:
                    if not (req[3]):
                        n += 1
                        k = types.InlineKeyboardMarkup(row_width=2)
                        k.add(types.InlineKeyboardButton("✅", callback_data=f"+{req[0]}"))
                        k.add(types.InlineKeyboardButton("⛔️", callback_data=f"-{req[0]}"))
                        await msg.answer(f"Заявка #{req[0]}\nПроблема: {req[2]}", reply_markup=k)
                if n == 0:
                    await msg.answer("Нет необработанных заявок!")
            case 'Рассылка':
                pass
            case 'Баны':
                banned = get_banned()
                if len(banned) == 0:
                    await msg.answer(
                        "Нет забанненых пользователей!\nЧтобы забанить пользователя, введите команду /ban <id пользователя>")
                else:
                    for ban in banned:
                        k = types.InlineKeyboardMarkup()
                        k.add(types.InlineKeyboardButton("Разбанить", callback_data=f">{ban[0]}"))
                        await msg.answer(f"{ban[0]} - {datetime.fromtimestamp(ban[4]).strftime('%d/%m/%Y %H:%M')}",
                                         reply_markup=k)
                    await msg.answer(
                        f"Всего {len(banned)} забанненых пользователей!\nЧтобы забанить пользователя, введите команду /ban <id пользователя>")
            case '📝 Статистика':
                stats = get_stat()
                k = types.InlineKeyboardMarkup()
                try:
                    prepare_psycho_google_sheet()
                except Exception:
                    pass

                google_sheets_url = spreadsheet.url
                if google_sheets_url:
                    k.add(types.InlineKeyboardButton('Google Таблица', url=google_sheets_url))
                k.add(types.InlineKeyboardButton("Вся статистика", callback_data="stats"))

                await msg.answer(
                    f"Статистикa\nКол-во пользователей: {stats[0]}\nКол-во психологов: {stats[1]}\nКол-во сессий сегодня: {stats[2]}\nКол-во сессий за месяц: {stats[3]}",
                    reply_markup=k)


# CALLBACK HANDLER
@dp.callback_query_handler()
async def callback(call: types.CallbackQuery):
    chat_id = call.message.chat.id
    user_id = call.from_user.id
    message_id = call.message.message_id

    if call.data.startswith("psyCatChoose="):
        cat_id = int(call.data.replace("psyCatChoose=", ""))
        set_user_main_cat(user_id, cat_id)
        apended_arr = get_user_cats(user_id)

        k = types.InlineKeyboardMarkup()
        for categories in get_subcategories_by_parent(cat_id):
            category_name = "⬜️ " + categories[2]
            if categories[0] in apended_arr:
                category_name = "✅ " + categories[2]
            k.add(types.InlineKeyboardButton(category_name, callback_data=f"subPsyCatChoose={categories[0]}"))

        await call.message.delete()

        try:
            await bot.send_message(chat_id, "Подкатегории:", reply_markup=k)
            await bot.send_message(chat_id, "\nМеню ", reply_markup=psycho_cat_menu_level2)
        except exceptions.BotBlocked:
            pass
        except exceptions.ChatNotFound:
            pass
        except exceptions.RetryAfter as e:
            pass
        except exceptions.UserDeactivated:
            pass
        except exceptions.TelegramAPIError:
            pass
        await call.answer()
    elif call.data.startswith("subPsyCatChoose="):
        cat_id = int(call.data.replace("subPsyCatChoose=", ""))

        apended_arr = get_user_cats(user_id)

        if cat_id in apended_arr:
            apended_arr.remove(cat_id)
        else:
            apended_arr.append(cat_id)

        set_user_cats(user_id, apended_arr)

        main_cat = get_user_main_cat(user_id)

        k = types.InlineKeyboardMarkup()
        await call.message.delete()
        for category in get_subcategories_by_parent(main_cat):
            category_name = "⬜️ " + category[2]
            if category[0] in apended_arr:
                category_name = "✅ " + category[2]
            k.add(types.InlineKeyboardButton(category_name, callback_data=f"subPsyCatChoose={category[0]}"))

        try:
            await bot.send_message(chat_id, "Подкатегории:", reply_markup=k)
            await bot.send_message(chat_id, "Основные категории", reply_markup=psycho_cat_menu_level2)
        except exceptions.BotBlocked:
            pass
        except exceptions.ChatNotFound:
            pass
        except exceptions.RetryAfter as e:
            pass
        except exceptions.UserDeactivated:
            pass
        except exceptions.TelegramAPIError:
            pass
        await call.answer()
    elif call.data.startswith("=categoryChoose="):
        cat_id = int(call.data.replace("=categoryChoose=", ""))
        set_user_main_cat(user_id, cat_id)
        apended_arr = get_user_cats(user_id)
        k = types.InlineKeyboardMarkup()
        for categories in get_subcategories_by_parent(cat_id):
            category_name = "⬜️ " + categories[2]
            if categories[0] in apended_arr:
                category_name = "✅ " + categories[2]
            k.add(types.InlineKeyboardButton(category_name, callback_data=f"=subCategoryChoose={categories[0]}"))

        await call.message.delete()
        try:
            await bot.send_message(chat_id, "Что бы Вы хотели обсудить в первую очередь (выберите до 5 категорий)?",
                                   reply_markup=k)
            await bot.send_message(chat_id, "\nМеню", reply_markup=user_presession_menu)
        except exceptions.BotBlocked:
            pass
        except exceptions.ChatNotFound:
            pass
        except exceptions.RetryAfter as e:
            pass
        except exceptions.UserDeactivated:
            pass
        except exceptions.TelegramAPIError:
            pass
        await call.answer()
    elif call.data.startswith("=subCategoryChoose="):

        cat_id = int(call.data.replace("=subCategoryChoose=", ""))
        apended_arr = get_user_cats(user_id)

        if cat_id in apended_arr:
            apended_arr.remove(cat_id)
        else:
            apended_arr.append(cat_id)

        set_user_cats(user_id, apended_arr)
        main_cat = get_user_main_cat(user_id)

        k = types.InlineKeyboardMarkup()

        if len(apended_arr) == 5:
            for category in get_user_cats(user_id):
                cat_arr = get_category_by_id(category)
                category_name = "✅ " + cat_arr[2]
                k.add(types.InlineKeyboardButton(category_name, callback_data="void"))

            # try:
            #     await bot.delete_message(chat_id, message_id=message_id - 2)
            # except exceptions.MessageToDeleteNotFound:
            #     await bot.send_message(user_id, srt(message_id - 2) + " MessageToDeleteNotFound")
            #     pass
            # except exceptions.MessageCantBeDeleted:
            #     await bot.send_message(user_id, srt(message_id - 2) + " MessageCantBeDeleted")
            #     pass
            # except exceptions.RetryAfter as e:
            #     await bot.send_message(user_id, srt(message_id - 2) + " RetryAfter")
            #     pass
            # except exceptions.TelegramAPIError:
            #     await bot.send_message(user_id, srt(message_id - 2) + " TelegramAPIError")
            #     pass
            #
            # try:
            #     await bot.delete_message(chat_id, message_id=message_id - 1)
            # except exceptions.MessageToDeleteNotFound:
            #     await bot.send_message(user_id, srt(message_id - 2) + " 2MessageToDeleteNotFound")
            #     pass
            # except exceptions.MessageCantBeDeleted:
            #     await bot.send_message(user_id, srt(message_id - 2) + " 2MessageCantBeDeleted")
            #     pass
            # except exceptions.RetryAfter as e:
            #     await bot.send_message(user_id, srt(message_id - 2) + " 2RetryAfter")
            #     pass
            # except exceptions.TelegramAPIError:
            #     await bot.send_message(user_id, srt(message_id - 2) + " 2TelegramAPIError")
            #     pass

            await call.message.delete()
            # await call.answer()

            try:
                await bot.send_message(chat_id, "Выбранные темы:", reply_markup=k)
                await bot.send_message(chat_id, "Опишите Вашу проблему:", reply_markup=types.ReplyKeyboardRemove())
            except exceptions.BotBlocked:
                pass
            except exceptions.ChatNotFound:
                pass
            except exceptions.RetryAfter as e:
                pass
            except exceptions.UserDeactivated:
                pass
            except exceptions.TelegramAPIError:
                pass
            # add_request(user_id)
            last_req = get_last_request_by_user_id(user_id)

            # await bot.send_message(chat_id, "fffff")
            # await bot.send_message(chat_id, len(last_req))
            # await bot.send_message(chat_id, str(last_req[0]))
            # await bot.send_message(chat_id, type(last_req[0]))
            delete_request_categories(user_id)
            for cat in get_user_cats(user_id):
                add_request_category(user_id, last_req[0], cat)
        else:
            for category in get_subcategories_by_parent(main_cat):
                category_name = "⬜️ " + category[2]
                if category[0] in apended_arr:
                    category_name = "✅ " + category[2]
                k.add(types.InlineKeyboardButton(category_name, callback_data=f"=subCategoryChoose={category[0]}"))


            # try:
            #     await bot.delete_message(chat_id, message_id=message_id - 2)
            # except exceptions.MessageToDeleteNotFound:
            #     await bot.send_message(user_id, srt(message_id - 2) + " MessageToDeleteNotFound")
            #     pass
            # except exceptions.MessageCantBeDeleted:
            #     await bot.send_message(user_id, srt(message_id - 2) + " MessageCantBeDeleted")
            #     pass
            # except exceptions.RetryAfter as e:
            #     await bot.send_message(user_id, srt(message_id - 2) + " RetryAfter")
            #     pass
            # except exceptions.TelegramAPIError:
            #     await bot.send_message(user_id, srt(message_id - 2) + " TelegramAPIError")
            #     pass
            #
            # try:
            #     await bot.delete_message(chat_id, message_id=message_id - 1)
            # except exceptions.MessageToDeleteNotFound:
            #     await bot.send_message(user_id, srt(message_id - 2) + " 2MessageToDeleteNotFound")
            #     pass
            # except exceptions.MessageCantBeDeleted:
            #     await bot.send_message(user_id, srt(message_id - 2) + " 2MessageCantBeDeleted")
            #     pass
            # except exceptions.RetryAfter as e:
            #     await bot.send_message(user_id, srt(message_id - 2) + " 2RetryAfter")
            #     pass
            # except exceptions.TelegramAPIError:
            #     await bot.send_message(user_id, srt(message_id - 2) + " 2TelegramAPIError")
            #     pass

            await call.message.delete()
            # await call.answer()

            try:
                await bot.send_message(user_id, "Что бы Вы хотели обсудить в первую очередь? (выберите до 5 категорий)",
                                       reply_markup=k)
                await bot.send_message(user_id, "\nМеню", reply_markup=user_presession_menu)
            except exceptions.BotBlocked:
                pass
            except exceptions.ChatNotFound:
                pass
            except exceptions.RetryAfter as e:
                pass
            except exceptions.UserDeactivated:
                pass
            except exceptions.TelegramAPIError:
                pass
        await call.answer()
    elif call.data == 'cancelRequest':
        remove_request(user_id)
        await call.answer("Ваша заявка отменена!")
        try:
            await bot.send_message(user_id, "Главное меню", reply_markup=main_menu)
        except exceptions.BotBlocked:
            pass
        except exceptions.ChatNotFound:
            pass
        except exceptions.RetryAfter as e:
            pass
        except exceptions.UserDeactivated:
            pass
        except exceptions.TelegramAPIError:
            pass
    elif call.data == 'cancelTechRequest':
        remove_techRequest(user_id)
        await call.answer("Главное меню")

        try:
            await bot.send_message(user_id, "Главное меню", reply_markup=main_menu)
        except exceptions.BotBlocked:
            pass
        except exceptions.ChatNotFound:
            pass
        except exceptions.RetryAfter as e:
            pass
        except exceptions.UserDeactivated:
            pass
        except exceptions.TelegramAPIError:
            pass
    elif call.data == 'stats':
        with open(DB_PATH, 'rb') as file:
            await bot.send_document(user_id, file, caption="Вся статистика")
    elif ((call.data.startswith('+')) or (call.data.startswith('-'))):
        if call.data.startswith('+'):
            request_id = int(call.data[1:])
            accept_request(request_id)
            request = get_request_by_id(request_id)
            user = get_user(request[1])
            user_name = user[1]
            if user_name:
                user_name = user_name
            else:
                user_name = ""
            user_age = user[2]
            if user_age:
                user_age = str(user_age)
            else:
                user_age = ""
            request_cats = get_request_categories_by_req_id(request[0])
            prepared_request_cats = []
            for request_cat in request_cats:
                category_by_id = get_category_by_id(request_cat[3])
                prepared_request_cats.append(category_by_id[2])
            if len(prepared_request_cats) > 0:
                prepared_request_cats = ', '.join(prepared_request_cats)
            else:
                prepared_request_cats = 'Без категорий'
            request_psychos = request[4]
            if request_psychos is None:
                try:
                    await bot.send_message(user_id, "Нет подходящих психологов для заявки", reply_markup=admin_menu)
                except exceptions.BotBlocked:
                    pass
                except exceptions.ChatNotFound:
                    pass
                except exceptions.RetryAfter as e:
                    pass
                except exceptions.UserDeactivated:
                    pass
                except exceptions.TelegramAPIError:
                    pass
            else:
                if request_psychos:
                    request_psychos = request_psychos.split(" ")
                    if len(request_psychos) > 0:
                        request_psychos = list(map(int, request_psychos))
                        for psy_id in request_psychos:
                            k = types.InlineKeyboardMarkup()
                            k.add(types.InlineKeyboardButton("Принять", callback_data=f"?{request[0]}"))

                            try:
                                await bot.send_message(psy_id,
                                                       f"Новая заявка!\n\nЗаявка #{request[0]}\nИмя: {user_name}\nВозраст: {user_age}\nКатегории: {prepared_request_cats}\nПроблема: {request[2]}\n✅ Заявка открыта",
                                                       reply_markup=k)
                            except exceptions.BotBlocked:
                                pass
                            except exceptions.ChatNotFound:
                                pass
                            except exceptions.RetryAfter as e:
                                pass
                            except exceptions.UserDeactivated:
                                pass
                            except exceptions.TelegramAPIError:
                                pass
                        await call.answer("Заявка проверена и отправлена психологам!")
                    else:
                        try:
                            await bot.send_message(user_id, "Нет подходящих психологов для заявки", reply_markup=admin_menu)
                        except exceptions.BotBlocked:
                            pass
                        except exceptions.ChatNotFound:
                            pass
                        except exceptions.RetryAfter as e:
                            pass
                        except exceptions.UserDeactivated:
                            pass
                        except exceptions.TelegramAPIError:
                            pass
        else:
            remove_request(request_id=int(call.data[1:]))
            await call.answer("Заявка удалена!")
        await call.message.delete()
        await call.answer()
    elif call.data.startswith("!"):
        remove_techRequest(int(call.data[1:]))
        await call.answer("Заявка обработана!")
        await call.message.edit_reply_markup()
    elif call.data.startswith("?"):
        request = add_session(int(call.data[1:]), user_id)
        if request[5]:
            await call.answer("Заявка занята другим специалистом.")
            try:
                await bot.send_message(user_id, "Меню психолога", reply_markup=psycho_menu)
            except exceptions.BotBlocked:
                pass
            except exceptions.ChatNotFound:
                pass
            except exceptions.RetryAfter as e:
                pass
            except exceptions.UserDeactivated:
                pass
            except exceptions.TelegramAPIError:
                pass
        else:
            psycho = get_psychos(user_id)
            applicant = get_applicant(user_id)
            user = get_user(request[1])
            group = types.MediaGroup()
            photo_exist = False

            request_cats = get_request_categories_by_req_id(request[0])
            prepared_request_cats = []

            for request_cat_id in request_cats:
                category_by_id = get_category_by_id(request_cat_id[3])
                prepared_request_cats.append(category_by_id[2])

            if len(prepared_request_cats) > 0:
                prepared_request_cats = ', '.join(prepared_request_cats)
            else:
                prepared_request_cats = 'Без категорий'

            psycho_rate = psycho[3]
            if psycho_rate:
                psycho_rate = str(round(psycho[3], 2))
            else:
                psycho_rate = "0"

            psycho_desc = psycho[2]
            if psycho_desc:
                psycho_desc = psycho_desc
            else:
                psycho_desc = ""

            psycho_name = psycho[1]
            if psycho_name:
                psycho_name = psycho_name
            else:
                psycho_name = ""

            user_name = user[1]
            if user_name:
                user_name = user_name
            else:
                user_name = ""

            user_age = user[2]
            if user_age:
                user_age = str(user_age)
            else:
                user_age = ""

            applicant_links = "-"
            applicant_price = "-"

            if applicant:
                if applicant[2]:
                    applicant_links = applicant[2]

                if applicant[3]:
                    applicant_price = applicant[3]

            for el in get_photos(user_id):
                photo_exist = True
                group.attach_photo(el,
                                   f"К Вам подключился психолог!\n"
                                   f" Имя: {psycho_name}\n"
                                   f" Сайт/Соц.сети/Канал: {applicant_links}\n"
                                   f" Цена: {applicant_price}\n"
                                   f" Метод работы: {psycho_desc}\n"
                                   f" Рейтинг: {psycho_rate}")

            if photo_exist:
                try:
                    await bot.send_media_group(request[1], media=group)
                except Exception:
                    await bot.send_message(request[1],
                               f"К Вам подключился психолог!\n"
                               f" Имя: {psycho_name}\n"
                               f" Сайт/Соц.сети/Канал: {applicant_links}\n"
                               f" Цена: {applicant_price}\n"
                               f" Метод работы: {psycho_desc}\n"
                               f" Рейтинг: {psycho_rate}")
            else:
                try:
                    await bot.send_message(request[1],
                       f"К Вам подключился психолог!\n"
                       f" Имя: {psycho_name}\n"
                       f" Сайт/Соц.сети/Канал: {applicant_links}\n"
                       f" Цена: {applicant_price}\n"
                       f" Метод работы: {psycho_desc}\n"
                       f" Рейтинг: {psycho_rate}")
                except exceptions.BotBlocked:
                    pass
                except exceptions.ChatNotFound:
                    pass
                except exceptions.RetryAfter as e:
                    pass
                except exceptions.UserDeactivated:
                    pass
                except exceptions.TelegramAPIError:
                    pass
            try:
                await bot.send_message(user_id,
                                       f"Ваш диалог начался!\nИнформация о пользователе:\n Имя: {user_name}\n Возраст: {user_age}\n Категории: {prepared_request_cats}\n Проблема: {request[2]}")
                await bot.send_message(user_id, "Меню Сессии", reply_markup=psycho_active_session_menu)
                await call.answer("Диалог начался!")
            except exceptions.BotBlocked:
                pass
            except exceptions.ChatNotFound:
                pass
            except exceptions.RetryAfter as e:
                pass
            except exceptions.UserDeactivated:
                pass
            except exceptions.TelegramAPIError:
                pass

            set_request_occupied(request[0])
            request_psychos = request[4]
            if request_psychos:
                request_psychos = request_psychos.split(" ")
                if len(request_psychos) > 0:
                    request_psychos = list(map(int, request_psychos))
                    request_psychos.remove(user_id)
                for psy_id in request_psychos:
                    try:
                        await bot.send_message(psy_id,
                                               f"Заявка #{request[0]}\nИмя: {user_name}\nВозраст: {user_age}\n❌ Заявка занята другим психологом")
                    except exceptions.BotBlocked:
                        pass
                    except exceptions.ChatNotFound:
                        pass
                    except exceptions.RetryAfter as e:
                        pass
                    except exceptions.UserDeactivated:
                        pass
                    except exceptions.TelegramAPIError:
                        pass
    elif call.data.startswith("&"):
        session, rating = call.data.split("&")[1:]
        set_rating(session, rating)
        await call.answer("Спасибо за оцеку!")
        await call.message.delete()
        try:
            await bot.send_message(user_id, "Главное меню", reply_markup=main_menu)
        except exceptions.BotBlocked:
            pass
        except exceptions.ChatNotFound:
            pass
        except exceptions.RetryAfter as e:
            pass
        except exceptions.UserDeactivated:
            pass
        except exceptions.TelegramAPIError:
            pass
    elif call.data.startswith(">"):
        unban(int(call.data[1:]))
        await call.message.delete()
        await call.answer("Пользователь разбанен!")
    elif call.data.startswith("accept"):
        psycho_id = int(call.data.replace('accept', ''))
        add_psycho(psycho_id, requisites="1")

        try:
            await bot.send_message(psycho_id,
                                   "Ваша заявка принята!\nТеперь вам нужно оплатить доступ к сервису PsyTetrica по ссылке https://app.leadpay.ru/3365/ \nПосле оплаты, пришлите сюда скрин платежа, чтобы мы подтвердили оплату(либо пришлите существующий скрин платежа, если уже оплатили)")
        except exceptions.BotBlocked:
            pass
        except exceptions.ChatNotFound:
            pass
        except exceptions.RetryAfter as e:
            pass
        except exceptions.UserDeactivated:
            pass
        except exceptions.TelegramAPIError:
            pass
        delete_psycho_category(psycho_id)
        psycho_cats = get_user_cats(psycho_id)
        for psycho_cat in psycho_cats:
            set_psycho_category(psycho_id, psycho_cat)

        await call.answer("Заявка одобрена!")
        await call.message.delete()
    elif call.data.startswith("deny"):
        remove_applicant(int(call.data.replace('deny', '')))
        await call.answer("Заявка удалена!")
        await call.message.delete()
    elif call.data.startswith("approve"):
        psycho_id = call.data.replace("approve", "")
        add_psycho(psycho_id, verified=True)
        try:
            await bot.send_message(int(call.data.replace('approve', '')),
                                   "Ваш платеж подтвержден! Теперь Вы можете принимать запросы пользователей, чтобы посмотреть активные запросы введите /work")
        except exceptions.BotBlocked:
            pass
        except exceptions.ChatNotFound:
            pass
        except exceptions.RetryAfter as e:
            pass
        except exceptions.UserDeactivated:
            pass
        except exceptions.TelegramAPIError:
            pass

        await call.answer("Заявка подтверждена!")

        try:
            await bot.send_message(user_id, "Вы подтвердили платеж!")
        except exceptions.BotBlocked:
            pass
        except exceptions.ChatNotFound:
            pass
        except exceptions.RetryAfter as e:
            pass
        except exceptions.UserDeactivated:
            pass
        except exceptions.TelegramAPIError:
            pass
    elif call.data == 'void':
        await call.answer()

if __name__ == "__main__":
    executor.start_polling(dp)
