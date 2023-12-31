BEGIN TRANSACTION;
--DROP TABLE IF EXISTS "Sessions";
--DROP TABLE IF EXISTS "Requests";
--DROP TABLE IF EXISTS "Categories";
--DROP TABLE IF EXISTS "Psycho";
--DROP TABLE IF EXISTS "RequestsCategories";
--CREATE TABLE IF NOT EXISTS "Users"
--(
--    "id"        integer,
--    "nickname"  text,
--    "age"       integer,
--    "banned"    boolean,
--    "ban_time"  float,
--    "reg_date"  float,
--    "not_first" boolean,
--    "temp_main_cat"  integer,
--    "temp_cats"  text
--);
--CREATE TABLE IF NOT EXISTS "Psycho"
--(
--    "id"       integer,
--    "nickname" text,
--    "desc"     text,
--    "rating"   float
--);
--CREATE TABLE IF NOT EXISTS "Sessions"
--(
--    "id"       integer,
--    "user"     integer,
--    "psycho"   integer,
--    "finished" boolean,
--    "rating"   int,
--    "date"     float,
--    PRIMARY KEY ("id" AUTOINCREMENT)
--);
--CREATE TABLE IF NOT EXISTS "Requests"
--(
--    "id"        integer,
--    "user"      integer,
--    "problem"   text,
--    "confirmed" boolean,
--    "psychos"   text,
--    "occupied"  boolean,
--    PRIMARY KEY ("id" AUTOINCREMENT)
--);
----
--CREATE TABLE IF NOT EXISTS "RequestsCategories"
--(
--    "id"        integer,
--    "user"      integer,
--    "requests_id"   integer,
--    "category_id"   integer,
--    PRIMARY KEY ("id" AUTOINCREMENT)
--);
--CREATE TABLE IF NOT EXISTS "Admins"
--(
--    "id" integer
--);
--CREATE TABLE IF NOT EXISTS "TechRequests"
--(
--    "id"            integer,
--    "user"          integer,
--    "user_nickname" text,
--    "problem"       text,
--    PRIMARY KEY ("id" AUTOINCREMENT)
--);
--CREATE TABLE IF NOT EXISTS "Photos"
--(
--    "id"     text,
--    "psycho" id
--);
--CREATE TABLE IF NOT EXISTS "Applicants"
--(
--    "id"         integer,
--    "name"       text,
--    "links"      text,
--    "price"      text,
--    "info"       text,
--    "withWho"    text,
--    "withoutWho" text,
--    "username"   text,
--    "requisites" text
--);
--CREATE TABLE IF NOT EXISTS "Categories"
--(
--    "id"     integer,
--    "parent" integer,
--    "name"   text,
--    "sort"   integer,
--    PRIMARY KEY ("id" AUTOINCREMENT)
--);
--CREATE TABLE IF NOT EXISTS "PsychoCategories"
--(
--    "id"       integer,
--    "psycho"   integer,
--    "category" integer,
--    PRIMARY KEY ("id" AUTOINCREMENT)
--);
--INSERT INTO "Admins" ("id")
--VALUES (657805132);
--INSERT INTO "Categories" ("id", "parent", "name", "sort")
--VALUES (1, 0, 'Мое состояние', 0);
--INSERT INTO "Categories" ("id", "parent", "name", "sort")
--VALUES (2, 0, 'Отношения', 0);
--INSERT INTO "Categories" ("id", "parent", "name", "sort")
--VALUES (3, 0, 'События в жизни', 0);
--INSERT INTO "Categories" ("id", "parent", "name", "sort")
--VALUES (4, 1, 'Стресс', 0);
--INSERT INTO "Categories" ("id", "parent", "name", "sort")
--VALUES (5, 1, 'Упадок сил', 0);
--INSERT INTO "Categories" ("id", "parent", "name", "sort")
--VALUES (6, 1, 'Нестабильная самооценка', 0);
--INSERT INTO "Categories" ("id", "parent", "name", "sort")
--VALUES (7, 1, 'Приступы страха и тревоги', 0);
--INSERT INTO "Categories" ("id", "parent", "name", "sort")
--VALUES (8, 1, 'Перепады настроения', 0);
--INSERT INTO "Categories" ("id", "parent", "name", "sort")
--VALUES (9, 1, 'Раздражительность', 0);
--INSERT INTO "Categories" ("id", "parent", "name", "sort")
--VALUES (10, 1, 'Ощущение одиночества', 0);
--INSERT INTO "Categories" ("id", "parent", "name", "sort")
--VALUES (11, 1, 'Проблемы с концентрацией', 0);
--INSERT INTO "Categories" ("id", "parent", "name", "sort")
--VALUES (12, 1, 'Эмоциональная зависимость', 0);
--INSERT INTO "Categories" ("id", "parent", "name", "sort")
--VALUES (13, 1, 'Проблемы со сном', 0);
--INSERT INTO "Categories" ("id", "parent", "name", "sort")
--VALUES (14, 1, 'Расстройство пищевого поведения', 0);
--INSERT INTO "Categories" ("id", "parent", "name", "sort")
--VALUES (15, 1, 'Депрессивные состояния', 0);
--INSERT INTO "Categories" ("id", "parent", "name", "sort")
--VALUES (16, 1, 'Панические атаки', 0);
--INSERT INTO "Categories" ("id", "parent", "name", "sort")
--VALUES (17, 1, 'Навязчивые мысли о здоровье', 0);
--INSERT INTO "Categories" ("id", "parent", "name", "sort")
--VALUES (18, 1, 'Сложности с алкоголем / наркотиками', 0);
--INSERT INTO "Categories" ("id", "parent", "name", "sort")
--VALUES (19, 2, 'С партнёром', 0);
--INSERT INTO "Categories" ("id", "parent", "name", "sort")
--VALUES (20, 2, 'В целом, с окружающими', 0);
--INSERT INTO "Categories" ("id", "parent", "name", "sort")
--VALUES (21, 2, 'С родителями', 0);
--INSERT INTO "Categories" ("id", "parent", "name", "sort")
--VALUES (22, 2, 'С детьми', 0);
--INSERT INTO "Categories" ("id", "parent", "name", "sort")
--VALUES (23, 2, 'Сексуальные', 0);
--INSERT INTO "Categories" ("id", "parent", "name", "sort")
--VALUES (24, 2, 'Сложности с ориентацией, её поиск', 0);
--INSERT INTO "Categories" ("id", "parent", "name", "sort")
--VALUES (25, 0, 'Работа, учёба', 0);
--INSERT INTO "Categories" ("id", "parent", "name", "sort")
--VALUES (26, 25, 'Недостаток мотивации', 0);
--INSERT INTO "Categories" ("id", "parent", "name", "sort")
--VALUES (27, 25, 'Выгорание', 0);
--INSERT INTO "Categories" ("id", "parent", "name", "sort")
--VALUES (28, 25, '«Не знаю, чем хочу заниматься»', 0);
--INSERT INTO "Categories" ("id", "parent", "name", "sort")
--VALUES (29, 25, 'Прокрастинация', 0);
--INSERT INTO "Categories" ("id", "parent", "name", "sort")
--VALUES (30, 25, 'Отсутствие цели', 0);
--INSERT INTO "Categories" ("id", "parent", "name", "sort")
--VALUES (31, 25, 'Смена, потеря работы', 0);
--INSERT INTO "Categories" ("id", "parent", "name", "sort")
--VALUES (32, 3, 'Переезд, эмиграция', 0);
--INSERT INTO "Categories" ("id", "parent", "name", "sort")
--VALUES (33, 3, 'Беременность, рождение ребёнка', 0);
--INSERT INTO "Categories" ("id", "parent", "name", "sort")
--VALUES (34, 3, 'Разрыв отношений, развод', 0);
--INSERT INTO "Categories" ("id", "parent", "name", "sort")
--VALUES (35, 3, 'Финансовые изменения', 0);
--INSERT INTO "Categories" ("id", "parent", "name", "sort")
--VALUES (36, 3, 'Утрата близкого человека', 0);
--INSERT INTO "Categories" ("id", "parent", "name", "sort")
--VALUES (37, 3, 'Болезнь, своя или близких', 0);
--INSERT INTO "Categories" ("id", "parent", "name", "sort")
--VALUES (38, 3, 'Насилие', 0);
COMMIT;