import psycopg2
import psycopg2.extras
import logging
from datetime import date
import uuid

from app.utils.config_reader import load_config


logger = logging.getLogger(__name__)
psycopg2.extras.register_uuid() # разрешение использовать uuid


class User:
    """Class user"""
    config = load_config('config/bot.ini')
    
    connection = psycopg2.connect(host=config.db.hostname, user=config.db.username,
                                  password=config.db.password,
                                  dbname=config.db.name,
                                  port=config.db.port)
    
    def __init__(self, tg_id, name='', join_date=date.today().strftime("%d.%m.%y"), current_room=None):
        self.tg_id = tg_id
        self.name = name
        self.join_date = join_date
        self.current_room = current_room

    def create(self):
        # conn = self.connection
        conn = self.connection
        with conn:
            with conn.cursor() as curs:
                logger.info('Database query: create -=USER=- data')

                query = """
                INSERT INTO users 
                VALUES 
                ( %(id)s, %(telegram_id)s, %(name)s, %(join_date)s, %(current_group)s )
                """

                curs.execute(query, {'id':uuid.uuid4(), 'telegram_id': self.tg_id, 'name': self.name,
                                     'join_date':self.join_date,'current_group': self.current_room})
                conn.commit()
                logger.info('Query completed')

    def get_user(self):
        conn = self.connection
        with conn:
            with conn.cursor() as curs:
                logger.info(f'Database query: get data for user {self.tg_id}')

                curs.execute("SELECT name, join_date, current_group FROM users WHERE telegram_id=%(tg_id)s",
                             {"tg_id": self.tg_id})
                query_result = curs.fetchone()

                logger.info('Query completed')
                if query_result:
                    self.name = query_result[0]
                    self.join_date = query_result[1]
                    self.current_room = query_result[2]
                    return True
                else:
                    return False

    def update(self):
        conn = self.connection
        with conn:
            with conn.cursor() as curs:
                logger.info(f'Database query: update data for user {self.tg_id}')

                query = """
                UPDATE users 
                SET 
                name=%(name)s, current_group=%(current_room)s
                WHERE telegram_id=%(tg_id)s
                """
                curs.execute(query, {'name': self.name, 'current_room': self.current_room,
                                     'tg_id': self.tg_id})
                conn.commit()
                logger.info('Query completed')


class Room:
    """Representation of room"""

    config = load_config('config/bot.ini')
    connection = psycopg2.connect(host=config.db.hostname, user=config.db.username,
                                  password=config.db.password,
                                  dbname=config.db.name,
                                  port=config.db.port)

    def __init__(self, name, passw='', owner='', new_member=''):
        self.name = name
        self.password = passw
        self.owner = owner
        self.new_member = new_member
        self.db_id = uuid.uuid4()

    def create(self):
        conn = self.connection
        with conn:
            with conn.cursor() as curs:
                logger.info(f'Database query: create new room {self.name}')
                query = """
                INSERT INTO groups 
                VALUES 
                ( %(id)s, %(group_password)s, %(group_name)s)
                """

                curs.execute(query, {'id':uuid.uuid4(),'group_password': self.password, 'group_name': self.name})
                conn.commit()
                logger.info('Query completed')

    def exist_room(self):
        conn = self.connection
        with conn:
            with conn.cursor() as curs:
                logger.info(f'Database query: validate exists room {self.name}')
                curs.execute("SELECT id FROM groups WHERE group_name=%(room_name)s",
                             {"room_name":self.name})
                query_result = curs.fetchone()
                logger.info('Query completed')
                if query_result == None:
                    return False
                else:
                    return True

    def update(self):
        conn = self.connection
        with conn:
            with conn.cursor() as curs:
                logger.info('Database query: update -=ROOM=- data')
                query = """
                SELECT id FROM users WHERE telegram_id=%(tg_id)s
                """
                curs.execute(query, {'tg_id': self.owner})
                user_id = curs.fetchone()
                query = """
                UPDATE groups 
                SET group_password=%(group_pass)s, owner_id=%(owner_id)s
                WHERE group_name=%(group_name)s
                """
                curs.execute(query, {'group_name': self.name, 'group_pass': self.password, 'owner_id': user_id[0]})
                conn.commit()
                logger.info('Query completed')

    def auth(self):
        conn = self.connection
        with conn:
            with conn.cursor() as curs:
                logger.info(f'Database query: auth in {self.name}')
                curs.execute("SELECT id FROM groups WHERE group_name=%(room_name)s AND group_password=%(room_passw)s",
                             {"room_name": self.name, 'room_passw': self.password})
                query_result = curs.fetchone()
                logger.info('Query completed')
                if query_result == None:
                    return False
                else:
                    return True

    def add_user(self):
        conn = self.connection
        with conn:
            with conn.cursor() as curs:
                logger.info(f'Database query: add user at room {self.name}')
                query = """
                SELECT id FROM users WHERE telegram_id=%(tg_id)s
                """
                curs.execute(query, {'tg_id': self.new_member})
                user_id = curs.fetchone()

                query = """
                SELECT id FROM groups WHERE group_name=%(room_name)s
                """
                curs.execute(query, {'room_name': self.name})
                room_id = curs.fetchone()

                query = """
                INSERT INTO users_groups
                VALUES
                ( %(id)s, %(user_id)s, %(group_id)s)
                """
                curs.execute(query, {'id': uuid.uuid4(), 'group_id': room_id[0], 'user_id': user_id[0]})
                conn.commit()
                logger.info('Query completed')

    def get_userlist(self):
        conn = self.connection
        with conn:
            with conn.cursor() as curs:
                logger.info(f'Database query: get users at room  {self.name}')
                query = """
                SELECT id FROM groups WHERE group_name=%(room_name)s
                """
                curs.execute(query, {'room_name': self.name})
                room_id = curs.fetchone()
                query = """
                SELECT DISTINCT telegram_id FROM public.users inner join public.users_groups on 
                public.users_groups.user_id=public.users.id WHERE group_id=%(room_id)s
                """
                curs.execute(query, {'room_id': room_id[0]})
                query_result = curs.fetchall()
                logger.info('Query completed')

                userlist = [i[0].split(' ')[0] for i in query_result]
                return userlist


class Package:
    """representation of purchases"""

    config = load_config('config/bot.ini')
    connection = psycopg2.connect(host=config.db.hostname, user=config.db.username,
                                  password=config.db.password,
                                  dbname=config.db.name,
                                  port=config.db.port)

    def __init__(self, tg_id: str, cost=0,description='', date=date.today().strftime("%d.%m.%y"), *debtors):
        self.payer = tg_id
        self.cost = cost
        self.description = description
        self.date = date
        self.debtors = debtors

    def create(self):
        conn = self.connection
        with conn:
            with conn.cursor() as curs:
                logger.info(f'Database query: create package')






