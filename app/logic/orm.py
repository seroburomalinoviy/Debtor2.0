import psycopg2
import psycopg2.extras
import logging
from datetime import date
import uuid


logger = logging.getLogger(__name__)
psycopg2.extras.register_uuid() # разрешение использовать uuid


class User:
    """Class user"""

    def __init__(self, tg_id, name='', join_date=date.today().strftime("%d.%m.%y"), is_owner=False, room_name=''):
        self.tg_id = tg_id
        self.name = name
        self.join_date = join_date
        self.is_owner = is_owner
        self.room_name = room_name

    def create(self):
        conn = psycopg2.connect(host='localhost', user='postgres', password='pgadmin', dbname='debtor_db', port="5433")
        with conn:
            with conn.cursor() as curs:
                logger.info('Database query: create -=USER=- data')

                query = """
                INSERT INTO users 
                VALUES 
                ( %(id)s, %(telegram_id)s, %(name)s, %(join_date)s, %(is_owner)s, %(group_name)s )
                """

                curs.execute(query, {'id':uuid.uuid4(), 'telegram_id': self.tg_id, 'name': self.name,
                                     'join_date':self.join_date, 'is_owner':
                    self.is_owner, 'group_name': self.room_name})
                conn.commit()

    def get_user(self):
        conn = psycopg2.connect(host='localhost', user='postgres', password='pgadmin', dbname='debtor_db', port="5433")
        with conn:
            with conn.cursor() as curs:
                logger.info('Database query: get -=USER=- data')

                curs.execute("SELECT name, join_date, group_name FROM users WHERE telegram_id=%(tg_id)s",
                             {"tg_id": self.tg_id})
                query_result = curs.fetchone()

                if query_result:
                    self.name = query_result[0]
                    self.join_date = query_result[1]
                    self.room_name = query_result[2]
                    return True
                else:
                    return False

    def update(self):
        conn = psycopg2.connect(host='localhost', user='postgres', password='pgadmin', dbname='debtor_db', port="5433")
        with conn:
            with conn.cursor() as curs:
                logger.info('Database query: update -=USER=- data')

                query = """
                UPDATE users 
                SET 
                name=%(name)s, is_owner=%(owner)s, group_name=%(room_name)s
                WHERE telegram_id=%(tg_id)s
                """
                curs.execute(query, {'name': self.name, 'owner': self.is_owner, 'room_name':self.room_name,
                                     'tg_id': self.tg_id})
                conn.commit()


class Room:
    """Representation of room"""

    def __init__(self, name, passw=''):
        self.name = name
        self.password = passw
        self.db_id = uuid.uuid4()

    def create(self):
        conn = psycopg2.connect(host='localhost', user='postgres', password='pgadmin', dbname='debtor_db', port="5433")
        with conn:
            with conn.cursor() as curs:
                logger.info('Database query: create -=ROOM=- data')

                query = """
                INSERT INTO groups 
                VALUES 
                ( %(id)s, %(group_password)s, %(group_name)s )
                """

                curs.execute(query, {'id':uuid.uuid4(),'group_password': self.password, 'group_name': self.name})
                conn.commit()
                logger.debug('Query completed')

    def exist_room(self):
        conn = psycopg2.connect(host='localhost', user='postgres', password='pgadmin', dbname='debtor_db', port="5433")
        with conn:
            with conn.cursor() as curs:
                logger.info('Database query: validate name -=ROOM=- data')
                curs.execute("SELECT id FROM groups WHERE group_name=%(room_name)s",
                             {"room_name":self.name})
                query_result = curs.fetchone()

                if query_result == None:
                    return False
                else:
                    return True

    def update(self):
        conn = psycopg2.connect(host='localhost', user='postgres', password='pgadmin', dbname='debtor_db', port="5433")
        with conn:
            with conn.cursor() as curs:
                logger.info('Database query: update -=ROOM=- data')

                query = """
                UPDATE groups 
                SET group_password=%(group_pass)s
                WHERE group_name=%(group_name)s
                """
                curs.execute(query, {'group_name': self.name, 'group_pass':self.password})
                conn.commit()


    def auth(self):
        conn = psycopg2.connect(host='localhost', user='postgres', password='pgadmin', dbname='debtor_db', port="5433")
        with conn:
            with conn.cursor() as curs:
                logger.info('Database query: auth name -=ROOM=- data')
                curs.execute("SELECT id FROM groups WHERE group_name=%(room_name)s AND group_password=%(room_passw)s",
                             {"room_name": self.name, 'room_passw': self.password})
                query_result = curs.fetchone()

                if query_result == None:
                    return False
                else:
                    return True


class Package:
    """Class of purchases"""

    def __init__(self, tg_id:str, cost=0,description='', paydate=date.today().strftime("%d.%m.%y"), *debtors):
        self.payer = tg_id
        self.cost = cost
        self.description = description
        self.date = paydate
        self.debtors = debtors



