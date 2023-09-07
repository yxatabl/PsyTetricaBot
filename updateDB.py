from aiogram import Bot, executor, types, Dispatcher
from aiogram.utils import exceptions
import sqlite3 as sql
import logging
import time
from datetime import datetime
from dotenv import load_dotenv
import os

load_dotenv()

TKN = os.getenv('TOKEN')
DB_PATH = 'root/PsyTet/db.db'
DB_CONFIG_PATH = 'root/PsyTet/db_config.sql'
PHOTOS_PATH = 'photos'

#LOGGING
logging.basicConfig(level=logging.INFO, filename='root/PsyTet/log.log', filemode='w', format="%(asctime)s %(levelname)s %(message)s")

#BOT INIT
bot = Bot(TKN)
dp = Dispatcher(bot)

#DB INIT
conn = sql.connect(DB_PATH)
cur = conn.cursor()
with open(DB_CONFIG_PATH, 'r') as file:
    cur.executescript(file.read())

#DB METHODS
def get_user(id: int):
    cur.execute(''' SELECT * FROM Users WHERE id=?''', [id])
    return cur.fetchone()
def get_users():
    cur.execute(''' SELECT * FROM Users ''')
    return cur.fetchall()
def add_user(id, name = None, age = None):
    if name:
        cur.execute(''' UPDATE Users SET nickname=? WHERE id=?''', [name, id])
    elif age:
        cur.execute(''' UPDATE Users SET age=? WHERE id=? ''', [age, id])
    else:
        cur.execute(''' INSERT INTO Users(id, banned, reg_date, ban_time) VALUES (?, ?, ?, ?) ''', [id, False, time.time(), 0.0])
    conn.commit()
def get_psychos(id = None):
    if id:
        cur.execute(''' SELECT * FROM Psycho WHERE id=?''', [id])
        return cur.fetchone()
    else:
        cur.execute(''' SELECT * FROM Psycho''')
        return cur.fetchall()
def update_rating(psycho_id: int):
    cur.execute(''' SELECT rating FROM Sessions WHERE psycho=? AND finished=1 ''', [psycho_id])
    ratings = cur.fetchall()
    s = 0
    k = 0
    for rat in ratings:
        s+=rat[0]
        k+=1
    if k == 0:
        cur.execute(''' UPDATE Psycho SET rating=? WHERE id=? ''', [0, psycho_id])
    else:
        cur.execute(''' UPDATE Psycho SET rating=? WHERE id=? ''', [round(s/k, 2), psycho_id])
    conn.commit()
def add_request(user, problem = None):
    if problem:
        cur.execute(''' UPDATE Requests SET problem=? WHERE user=? ''', [problem, user])
    else:
        cur.execute(''' INSERT INTO Requests(user, confirmed) VALUES (?, ?) ''', [user, False])
    conn.commit()
def remove_request(id = None, request_id = None):
    if request_id:
       cur.execute(''' DELETE FROM Requests WHERE id=? ''', [request_id]) 
    else:
        cur.execute(''' DELETE FROM Requests WHERE user=? ''', [id])
    conn.commit()
def accept_request(id: int):
    cur.execute(''' UPDATE Requests SET confirmed=? WHERE id=? ''', [True, id])
    conn.commit()
def get_requests(user = None):
    if user:
        cur.execute(''' SELECT * FROM Requests WHERE user=? ''', [user])
        return cur.fetchone()
    else:
        cur.execute(''' SELECT * FROM Requests ''')
        return cur.fetchall()
def add_techRequest(user, problem = None, user_nickname = None):
    if problem:
        cur.execute(''' UPDATE TechRequests SET problem=?, user_nickname=? WHERE user=? ''', [problem, user_nickname, user])
    else:
        cur.execute(''' INSERT INTO TechRequests(user) VALUES (?) ''', [user])
    conn.commit()
def remove_techRequest(id: int):
    cur.execute(''' DELETE FROM TechRequests WHERE id=? ''', [id])
    conn.commit()
def get_techRequests(user = None):
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
def get_sessions(user = None, member = None):
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
def add_psycho(id: int, name = None, links = None, price = None, info = None, withWho = None, withoutWho = None, username = None, requisites = None, verified = None):
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
            cur.execute(''' INSERT INTO Applicants(id, username) VALUES (?, ?)''', [id, username])
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
                month_sessions+=1
                if a.day == b.day:
                    today_sessions+=1
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

#PANELS
global main_menu
main_menu = types.ReplyKeyboardMarkup([['Пригласить психолога'], ['Техподдержка', 'История сессий']], resize_keyboard=True, one_time_keyboard=True)

global psycho_menu
psycho_menu = types.ReplyKeyboardMarkup([['Активные заявки']], resize_keyboard=True, one_time_keyboard=True)

global admin_menu
admin_menu = types.ReplyKeyboardMarkup([['Обращения'], ['Баны'], ['Статистика']], resize_keyboard=True, one_time_keyboard=True)

#CHAT HANDLER
@dp.message_handler(content_types=[types.ContentType.ANIMATION,
                                   types.ContentType.AUDIO,
                                   types.ContentType.VIDEO,
                                   types.ContentType.VIDEO_NOTE,
                                   types.ContentType.STICKER,
                                   types.ContentType.VOICE,
                                   types.ContentType.DOCUMENT
                                   ])
async def files(msg: types.Message):
    session = get_sessions(member = msg.from_user.id)
    if session:
        session = list(session)
        #Здесь надо еще будет добавление в лог чата
        session.pop(session.index(msg.from_user.id))
        to = session[1]
        await bot.copy_message(to, msg.from_user.id, msg.message_id)
@dp.message_handler(content_types=[types.ContentType.PHOTO])
async def photo(msg: types.Message):
    session = get_sessions(member = msg.from_user.id)
    app = is_applicant(msg.from_user.id)
    if session:
        session = list(session)
        #Здесь надо еще будет добавление в лог чата
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
    session = get_sessions(member = msg.from_user.id)
    if session:
        if get_psychos(msg.from_user.id):
            end_session(msg.from_user.id)
            k = types.InlineKeyboardMarkup()
            for i in range(5):
                k.add(types.InlineKeyboardButton(f"{i+1}", callback_data=f"&{session[0]}&{i+1}"))
            await bot.send_message(session[1], "Психолог завершил сессию! Укажите вашу оценку данной сессии", reply_markup=k)
            await msg.answer("Сессия завершена!\nМеню психолога", reply_markup=psycho_menu)

#COMMANDS HANDLER
@dp.message_handler(commands=['start'])
async def start(msg: types.Message):
    if not(get_sessions(member=msg.from_user.id)):
        usr = get_user(msg.from_user.id)
        if usr:
            if not(usr[3]):
                if usr[1] == None:
                    add_user(msg.from_user.id, name=msg.text.strip())
                    await msg.answer("Сколько вам лет?")
                elif usr[2] == None:
                    age = int(msg.text)
                    add_user(msg.from_user.id, age=age)
                    await msg.answer("Добро пожаловать!\nГлавное меню", reply_markup=main_menu)
                else:
                    await msg.answer("Добро пожаловать!\nГлавное меню", reply_markup=main_menu)
        else:
            #REGISTRATION
            add_user(msg.from_user.id)
            await msg.answer("🥺Перед началом регистрации, вы должны понимать: Наши специалисты -  действительные профессионалы своего дела💚 А вы нам очень дороги 🙌\n\nС уважением, команда PsyTetrica 💙")
            await msg.answer("Как к вам обращаться?")
@dp.message_handler(commands=['done'])
async def done(msg: types.Message):
    if is_applicant(msg.from_user.id):
        await msg.answer("Ваша заявка принята на рассмотрение! Ожидайте ответа от администратора")
        for admin in get_admins():
            await bot.send_message(admin, "Новая заявка на добавление психолога! Посмотреть заявки - /adminApplicants")
@dp.message_handler(commands=['work'])
async def work(msg: types.Message):
    if not(get_sessions(member=msg.from_user.id)):
        psycho = get_psychos(msg.from_user.id)
        if psycho:
            await msg.answer("Меню психолога", reply_markup=psycho_menu)
@dp.message_handler(commands=['requests'])
async def requests(msg: types.Message):
    if not(get_sessions(member=msg.from_user.id)):
        psycho = get_psychos(msg.from_user.id)
        if psycho:
            reqs = get_requests()
            n = 0
            for req in reqs:
                if req[3]:
                    n+=1
                    user = get_user(req[1])
                    k = types.InlineKeyboardMarkup()
                    k.add(types.InlineKeyboardButton("Принять", callback_data=f"?{req[0]}"))
                    await msg.answer(f"Заявка #{req[0]}\nПроблема: {req[2]}\nИнформация о пользователе\nИмя - {user[1]}\nВозраст - {user[2]}", reply_markup=k)
            if n == 0:
                await msg.answer("Активных заявок нет!")
@dp.message_handler(commands=['apply'])
async def apply(msg: types.Message):
    if get_user(msg.from_user.id):
        if not(get_sessions(member=msg.from_user.id)):
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
                add_psycho(msg.from_user.id, username = msg.from_user.mention)
                await msg.answer("Сейчас вы должны будете заполнить заявку, после проверки которой, вы сможете начать работать!")
                await msg.answer("Введите ваши фамилию и имя")
@dp.message_handler(commands=['newRequests'])
async def newRequests(msg: types.Message):
    if not(get_sessions(member=msg.from_user.id)):
        if msg.from_user.id in get_admins():
            reqs = get_requests()
            n = 0
            for req in reqs:
                if not(req[3]):
                    user = get_user(req[1])
                    n+=1
                    k = types.InlineKeyboardMarkup(row_width=2)
                    k.row(types.InlineKeyboardButton("✅", callback_data=f"+{req[0]}"), types.InlineKeyboardButton("⛔️", callback_data=f"-{req[0]}"))
                    await msg.answer(f"Заявка #{req[0]}\nПроблема: {req[2]}\nИнформация о пользователе\nИмя - {user[1]}\nВозраст - {user[2]}", reply_markup=k)
            if n == 0:
                await msg.answer("Нет необработанных заявок!")
@dp.message_handler(commands=['admin'])
async def admin(msg: types.Message):
    if not(get_sessions(member=msg.from_user.id)):
        if msg.from_user.id in get_admins():
            await msg.answer("Админпанель", reply_markup=admin_menu)
@dp.message_handler(commands=['addAdmin'])
async def addAdmin(msg: types.Message):
    if not(get_sessions(member=msg.from_user.id)):
        if msg.from_user.id in get_admins():
            admin_id = int(msg.text.replace('/addAdmin', '').strip())
            if admin_id in get_admins():
                await msg.answer("Пользователь уже является модератором!")
            else:
                try:
                    await bot.send_message(admin_id, "Вы теперь модератор сервиса! Для доступа к меню, введите команду - /admin")
                    add_admin(admin_id)
                    await msg.answer("Админ добавлен!")
                except exceptions.ChatNotFound:
                    await msg.answer("Не удалось добавить модератора, возможно вы неправтльно ввели его id!")
@dp.message_handler(commands=['deleteAdmin'])
async def deleteAdmin(msg: types.Message):
    if not(get_sessions(member=msg.from_user.id)):
        if msg.from_user.id in get_admins():
            remove_admin(int(msg.text.replace('/deleteAdmin', '').strip()))
            await msg.answer("Админ удален!")
@dp.message_handler(commands=['adminApplicants'])
async def adminApplicants(msg: types.Message):
    if not(get_sessions(member=msg.from_user.id)):
        if msg.from_user.id in get_admins():
            apps = get_applicants()
            if len(apps) == 0:
                await msg.answer("Нет новых заявлений!")
            else:
                for app in apps:
                    k = types.InlineKeyboardMarkup()
                    k.row(types.InlineKeyboardButton("Одобрить", callback_data=f"accept{app[0]}"), types.InlineKeyboardButton("Отклонить", callback_data=f"deny{app[0]}"))
                    group = types.MediaGroup()
                    if len(get_photos(app[0]))>0:
                        kol = 0
                        for el in get_photos(app[0]):
                            kol+=1
                            group.attach_photo(el)
                            if kol==10:
                                break
                        await bot.send_media_group(msg.from_user.id, group)
                    await msg.answer(f"Заявка {app[7]}\nИмя - {app[1]}\nСсылки: {app[2]}\nЦена сессии: {app[3]}\nОписание:\n{app[4]}\nС кем работаю: {app[5]}\nС кем не работаю: {app[6]}", reply_markup=k)
@dp.message_handler(commands=['techRequests'])
async def techRequests(msg: types.Message):
    if not(get_sessions(member=msg.from_user.id)):
        if msg.from_user.id in get_admins():
            if len(get_techRequests())>0:
                for req in get_techRequests():
                    k = types.InlineKeyboardMarkup()
                    k.add(types.InlineKeyboardButton("Завершено", callback_data=f"!{req[0]}"))
                    await msg.answer(f"Обращение #{req[0]}\nПользователь: {req[2]}({req[1]})\nПроблема: {req[3]}", reply_markup=k)
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
                b+=1
                try:
                    await bot.copy_message(user[0], msg.from_user.id, post)
                    a+=1
                except Exception:
                    pass
            await msg.answer(f"Рассылка завершена!({a}/{b} пользователей получили объявление)")
        except AttributeError:
            await msg.answer("Вы не ссылаетесь ни на кое сообщение!")
        

#TEXT HANDLER
@dp.message_handler(content_types=['text'])
async def text(msg: types.Message):
    #USERS TEXT
    usr = get_user(msg.from_user.id)
    if usr:
        if not(usr[3]):
            if usr[1] == None:
                add_user(msg.from_user.id, name=msg.text.strip())
                await msg.answer("Сколько вам лет?")
            elif usr[2] == None:
                age = int(msg.text)
                add_user(msg.from_user.id, age=age)
                await msg.answer("Добро пожаловать!\nГлавное меню", reply_markup=main_menu)
            else:
                session = get_sessions(member = msg.from_user.id)
                if session:
                    session = list(session)
                    #Здесь надо еще будет добавление в лог чата
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
                        await msg.answer("Опишите ваши методы работы")
                    elif app[4] == None:
                        add_psycho(msg.from_user.id, info=msg.text.strip())
                        await msg.answer("С какими клиентами вы готовы работать?")
                    elif app[5] == None:
                        add_psycho(msg.from_user.id, withWho=msg.text.strip())
                        await msg.answer("С какими клиентами вы неготовы работать?")
                    elif app[6] == None:
                        add_psycho(msg.from_user.id, withoutWho=msg.text.strip())
                        await msg.answer("Пришлите ваши фотографии, когда пришлете все фото отправте /done")
                else:
                    match msg.text:
                        case 'Пригласить психолога':
                            req = get_requests(msg.from_user.id)
                            if req:
                                k = types.InlineKeyboardMarkup()
                                k.add(types.InlineKeyboardButton("Отмена", callback_data="cancelRequest"))
                                await msg.answer("Вы уже подали заявку!", reply_markup=k)
                            else:
                                add_request(msg.from_user.id)
                                k = types.InlineKeyboardMarkup()
                                k.add(types.InlineKeyboardButton("Отмена", callback_data="cancelRequest"))
                                await msg.answer("Опишите вашу проблему (если не сможете, так и напишите)", reply_markup=k)
                        case 'Техподдержка':
                            add_techRequest(user = msg.from_user.id)
                            k = types.InlineKeyboardMarkup()
                            k.add(types.InlineKeyboardButton("Отмена", callback_data="cancelTechRequest"))
                            await msg.answer("Если у вас произошла ошибка, или есть вопросы по работе нашего сервиса, напишите нам", reply_markup=k)
                        case 'История сессий':
                            sessions = get_sessions(user=msg.from_user.id)
                            for session in sessions:
                                psycho = get_psychos(session[2])
                                #k = types.InlineKeyboardMarkup()
                                #k.add(types.InlineKeyboardButton("⭐️", callback_data=f"@{session[2]}"))
                                await msg.answer(f"Сессия #{session[0]}\nДата: {datetime.fromtimestamp(session[5]).strftime('%d/%m/%Y %H:%M')}\nПсихолог: {psycho[1]}\nВаша оценка: {session[4]}")
                        case _:
                            req = get_requests(msg.from_user.id)
                            if req:
                                if req[2] == None:
                                    add_request(msg.from_user.id, msg.text.strip())
                                    await msg.answer("Ваша заявка принята в обработку!\nСначала ее проверит администратор, и, после успешной проверки, с вами свяжется психолог!")
                                    for admin in get_admins():
                                        await bot.send_message(admin, "Новая заявка!\nПосмтортеть непроверенные заявки - /NewRequests")
                            techReq = get_techRequests(msg.from_user.id)
                            if techReq:
                                if techReq[3] == None:
                                    add_techRequest(user=msg.from_user.id, problem=msg.text.strip(), user_nickname=msg.from_user.mention)
                                    await msg.answer("Ваша заявка принята! Если потребуется, с вами свяжется один из наших администраторов!")
                                    for admin in get_admins():
                                        await bot.send_message(admin, "Новое обращение в техподдержку! Посмотреть обращения - /techRequests")

    else:
        #REGISTRATION
        add_user(msg.from_user.id)
        await msg.answer("🥺Перед началом регистрации, вы должны понимать: Наши специалисты -  действительные профессионалы своего дела💚 А вы нам очень дороги 🙌\n\nС уважением, команда PsyTetrica 💙")
        await msg.answer("Как к вам обращаться?")
    
    #PSYCHO TEXT
    psycho = get_psychos(msg.from_user.id)
    sessions = get_sessions(member=msg.from_user.id)
    if psycho:
        if sessions:
            pass
        else:
            match msg.text:
                case 'Активные заявки':
                    reqs = get_requests()
                    if len(reqs) == 0:
                        await msg.answer("Активных заявок нет!")
                    else:
                        for req in reqs:
                            k = types.InlineKeyboardMarkup()
                            k.add(types.InlineKeyboardButton("Принять", callback_data=f"?{req[0]}"))
                            await msg.answer(f"Заявка #{req[0]}\nПроблема: {req[2]}", reply_markup=k)
    
    #ADMINS TEXT
    if msg.from_user.id in get_admins():
        match msg.text:
            case 'Обращения':
                reqs = get_requests()
                n = 0
                for req in reqs:
                    if not(req[3]):
                        n+=1
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
                    await msg.answer("Нет забанненых пользователей!\nЧтобы забанить пользователя, введите команду /ban <id пользователя>")
                else:
                    for ban in banned:
                        k = types.InlineKeyboardMarkup()
                        k.add(types.InlineKeyboardButton("Разбанить", callback_data=f">{ban[0]}"))
                        await msg.answer(f"{ban[0]} - {datetime.fromtimestamp(ban[4]).strftime('%d/%m/%Y %H:%M')}", reply_markup=k)
                    await msg.answer(f"Всего {len(banned)} забанненых пользователей!\nЧтобы забанить пользователя, введите команду /ban <id пользователя>")
            case 'Статистика':
                stats = get_stat()
                k = types.InlineKeyboardMarkup()
                k.add(types.InlineKeyboardButton("Вся статистика", callback_data="stats"))
                await msg.answer(f"Статистика\nКол-во пользователей: {stats[0]}\nКол-во психологов: {stats[1]}\nКол-во сессий сегодня: {stats[2]}\nКол-во сессий за месяц: {stats[3]}", reply_markup=k)

#CALLBACK HANDLER
@dp.callback_query_handler()
async def callback(call: types.CallbackQuery):
    if call.data == 'cancelRequest':
        remove_request(call.from_user.id)
        await call.answer("Ваша заявка отменена!")
        await bot.send_message(call.from_user.id, "Главное меню", reply_markup=main_menu)
    elif call.data == 'cancelTechRequest':
        remove_techRequest(call.from_user.id)
        await call.answer("Главное меню")
        await bot.send_message(call.from_user.id, "Главное меню", reply_markup=main_menu)
    elif call.data == 'stats':
        with open(DB_PATH, 'rb') as file:
            await bot.send_document(call.from_user.id, file, caption="Вся статистика")
    elif ((call.data.startswith('+')) or (call.data.startswith('-'))):
        if call.data.startswith('+'):
            accept_request(int(call.data[1:]))
            for psycho in get_psychos():
                await bot.send_message(psycho[0], "Новая заявка! Посмотреть активные завки - /requests")
            await call.answer("Заявка проверена!")
        else:
            remove_request(request_id=int(call.data[1:]))
            await call.answer("Заявка удалена!")
        await call.message.delete()
    elif call.data.startswith("!"):
        remove_techRequest(int(call.data[1:]))
        await call.answer("Заявка обработана!")
        await call.message.edit_reply_markup()
    elif call.data.startswith("?"):
        request = add_session(int(call.data[1:]), call.from_user.id)
        psycho = get_psychos(call.from_user.id)
        user = get_user(request[1])
        group = types.MediaGroup()
        for el in get_photos(call.from_user.id):
            group.attach_photo(el, f"К вам подключился психолог!\nИнформация о психологе:\nИмя - {psycho[1]}\nОписание - {psycho[2]}\nРейтинг - {round(psycho[3], 2)}")
        await bot.send_media_group(request[1], group)
        if len(get_photos(call.from_user.id))>1:
            await bot.send_message(request[1], f"К вам подключился психолог!\nИнформация о психологе:\nИмя - {psycho[1]}\nОписание - {psycho[2]}\nРейтинг - {round(psycho[3], 2)}")
        await bot.send_message(call.from_user.id, f"Ваш диалог начался!\nИнформация о пользователе:\nИмя - {user[1]}\nВозраст - {user[2]}\nПроблема: {request[2]}")
        await call.answer("Диалог начался!")
    elif call.data.startswith("&"):
        session, rating = call.data.split("&")[1:]
        set_rating(session, rating)
        await call.answer("Спасибо за оцеку!")
        await call.message.delete()
        await bot.send_message(call.from_user.id, "Главное меню", reply_markup=main_menu)
    elif call.data.startswith(">"):
        unban(int(call.data[1:]))
        await call.message.delete()
        await call.answer("Пользователь разбанен!")
    elif call.data.startswith("accept"):
        add_psycho(int(call.data.replace('accept', '')), requisites="1")
        await bot.send_message(int(call.data.replace('accept', '')), "Ваша заявка принята! Теперь вам нужно отправить 2000 рублей на 5536913934097672(номер карты/Тинькофф), пришлите сюда скрин платежа, чтобы подтвердить оплату")
        await call.answer("Заявка одобрена!")
        await call.message.delete()
    elif call.data.startswith("deny"):
        remove_applicant(int(call.data.replace('deny', '')))
        await call.answer("Заявка удалена!")
        await call.message.delete()
    elif call.data.startswith("approve"):
        psycho_id = call.data.replace("approve", "")
        add_psycho(psycho_id, verified=True)
        await bot.send_message(int(call.data.replace('approve', '')), "Ваш платеж подтвержден! Теперь вы можете принимать запросы пользователей, чтобы посмотреть активные запросы введите /work")
        await call.answer("Заявка подтверждена!")
        await bot.send_message(call.from_user.id, "Вы подтвердили платеж!")


if __name__ == "__main__":
    executor.start_polling(dp)
