import psycopg2
from parameters import password


conn = psycopg2.connect(
    database='vk_users',
    user='postgres',
    password=password,
    host='127.0.0.1'
)

conn.autocommit = True


def create_db():
    with conn.cursor() as cursor:
        cursor.execute(
            """CREATE TABLE IF NOT EXISTS users(
                id serial,
                id_user varchar(20) NOT NULL,
                id_candidate varchar(20) NOT NULL);"""
        )


def add_users(user_id, candidate_id):
    with conn.cursor() as cursor:
        cursor.execute(
            f"""INSERT INTO users (id_user, id_candidate)
            VALUES ('{user_id}', '{candidate_id}');"""
        )


def select_viewed_id(out_id):
    with conn.cursor() as cursor:
        cursor.execute(
            f"""SELECT id_candidate FROM users WHERE id_user='{out_id}';
            """
        )
        viewed_ids = cursor.fetchall()
        list_of_ids = []
        for item in viewed_ids:
            list_of_ids.append(item[0])
        return list_of_ids
