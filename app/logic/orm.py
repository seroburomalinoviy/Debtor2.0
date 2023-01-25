import psycopg2
import psycopg2.extras
import logging
from datetime import date
import uuid
import asyncpg
from time import perf_counter

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
    
    def __init__(self, tg_id, tg_name='',name='', join_date=date.today().strftime("%d.%m.%y"), current_room=None):
        self.tg_id = tg_id
        self.tg_name = tg_name
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
                ( %(id)s, %(telegram_id)s, %(name)s, %(join_date)s, %(current_group)s, %(tg_name)s )
                """

                curs.execute(query, {'id':uuid.uuid4(), 'telegram_id': self.tg_id, 'name': self.name,
                                     'join_date':self.join_date,'current_group': self.current_room, 'tg_name': self.tg_name})
                conn.commit()
                logger.info('Query completed')

    def get_user(self):
        conn = self.connection
        with conn:
            with conn.cursor() as curs:
                logger.info(f'Database query: get data for user {self.tg_id}')

                curs.execute("SELECT name, join_date, current_group, tg_name FROM users WHERE telegram_id=%(tg_id)s",
                             {"tg_id": self.tg_id})
                query_result = curs.fetchone()

                logger.info('Query completed')
                if query_result:
                    self.name = query_result[0]
                    self.join_date = query_result[1]
                    self.current_room = query_result[2]
                    self.tg_name = query_result[3]
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
                SELECT DISTINCT telegram_id, tg_name, name FROM public.users inner join public.users_groups on 
                public.users_groups.user_id=public.users.id WHERE group_id=%(room_id)s
                """
                curs.execute(query, {'room_id': room_id[0]})
                query_result = curs.fetchall()
                logger.info('Query completed')

                userlist = {i[0].split(' ')[0]: [i[1], i[2]] for i in query_result}
                return userlist



class Package:
    """representation of purchases"""

    config = load_config('config/bot.ini')
    connection = psycopg2.connect(host=config.db.hostname, user=config.db.username,
                                  password=config.db.password,
                                  dbname=config.db.name,
                                  port=config.db.port)

    def __init__(self, tg_id='', room_name='', cost=0, description='', date=date.today().strftime("%d.%m.%y"),
                 transaction_id=0, paid=False):
        self.payer = tg_id
        self.room_name = room_name
        self.cost = cost
        self.description = description
        self.date = date
        self.sum_debt = 0
        self.paid = paid
        self.transaction_id = transaction_id

    def create(self):
        conn = self.connection
        with conn:
            with conn.cursor() as curs:
                logger.info(f'Database query: create package')
                start = perf_counter()
                query = """
                SELECT id FROM users WHERE telegram_id=%(tg_id)s
                """
                curs.execute(query, {'tg_id': self.payer})
                user_id = curs.fetchone()

                query = """
                SELECT id FROM groups WHERE group_name=%(room_name)s
                """
                curs.execute(query, {'room_name': self.room_name})
                room_id = curs.fetchone()

                query = """
                INSERT INTO payments
                VALUES
                ( %(id)s, %(date)s, %(group_id)s, %(cost)s, %(description)s, %(payer_id)s )
                """
                curs.execute(query, {'id': uuid.uuid4(), 'date': self.date, 'payer_id': user_id[0], 'group_id':
                    room_id[0], 'cost': self.cost, 'description': self.description})
                conn.commit()
                logger.info(f'Query completed\n{perf_counter()-start}')

# FIXME: update query to db
    def get_products_list(self):
        conn = self.connection
        with conn:
            with conn.cursor() as curs:
                logger.info(f'[DB query]: Get debts')
                start = perf_counter()
                query = """
                SELECT id FROM users WHERE telegram_id=%(tg_id)s
                """
                curs.execute(query, {'tg_id': self.payer})
                user_id = curs.fetchone()

                query = """
               SELECT id FROM groups WHERE group_name=%(room_name)s
               """
                curs.execute(query, {'room_name': self.room_name})
                room_id = curs.fetchone()

                query = """
                SELECT id, debt, cost, date, paid, group_name, debtor_name, payer_name, description 
                FROM 
                debts_for_users 
                WHERE debtor_id=%(tg_id)s 
                and group_id=%(room)s and paid=%(paid)s
                """
                curs.execute(query, {'tg_id': user_id[0], 'room': room_id[0], 'paid': self.paid})
                query_result = curs.fetchall()
                logger.info(f'Query completed\n{perf_counter()-start}')

                return query_result

    def get_debts_user_payer(self):
        conn = self.connection
        with conn:
            with conn.cursor() as curs:
                logger.info(f'[DB query]: get_debts_user_payer')
                start = perf_counter()

                query = """
                   SELECT id FROM users WHERE telegram_id=%(tg_id)s
                   """
                curs.execute(query, {'tg_id': self.payer})
                user_id = curs.fetchone()

                query = """
                  SELECT id FROM groups WHERE group_name=%(room_name)s
                  """
                curs.execute(query, {'room_name': self.room_name})
                room_id = curs.fetchone()

                query = """
                -- Собрали суммы долгов участникам комнаты, которым должен я.
-- SELECT payer_id, sum(debt) FROM debts_for_users where paid=False and debtor_tg_id='250545783' group by payer_id
-- Найдем сумму долгов моих плательщикам мне.
-- select debtor_tg_id, sum(debt) FROM debts_for_users where paid=False and payer_id ='250545783' group by debtor_tg_id


select payers, my_money, my_debts from 
	(select debtor_tg_id as payers, sum(debt) as my_money FROM debts_for_users where paid=False and payer_id ='250545783' group by debtor_tg_id) as my_first 
	left join 
	(SELECT payer_id, sum(debt)as my_debts FROM debts_for_users where paid=False and debtor_tg_id='250545783' group by payer_id) as my_t 
	on my_first.payers=my_t.payer_id 
                """


                


    def check_debt(self):
        conn = self.connection
        with conn:
            with conn.cursor() as curs:
                logger.info(f'[DB query]: check debt')
                start = perf_counter()

                query = """
                UPDATE debts_for_users SET
                paid=%(paid)s
                WHERE id=%(trans_id)s
                """

                curs.execute(query, {'trans_id': self.transaction_id, 'paid': True})
                conn.commit()
                logger.info(f"Transaction id of the debt {self.transaction_id}")
                logger.info(f'Query completed\n{perf_counter()-start}')

    def get_product(self):
        conn = self.connection
        with conn:
            with conn.cursor() as curs:
                logger.info(f'[DB query]: get product')
                start = perf_counter()

                query = """
                SELECT date, description, debt, payer_id, debtor_name, debtor_tg_id, paid FROM 
                debts_for_users 
                WHERE id=%(trans_id)s
                """

                curs.execute(query, {'trans_id': self.transaction_id})
                query_result = curs.fetchone()
                logger.info(f'Query completed\n{perf_counter()-start}')
                return query_result

    def accept_payment(self):
        conn = self.connection
        with conn:
            with conn.cursor() as curs:
                logger.info(f'[DB query]: accept payment')
                start = perf_counter()

                query = """
                UPDATE debts_for_users SET
                payment_accept=%(payment)s
                WHERE id=%(trans_id)s
                """

                curs.execute(query, {'trans_id': self.transaction_id, 'payment': True})
                conn.commit()
                logger.info(f"Transaction id of the debt {self.transaction_id}")
                logger.info(f'Query completed\n{perf_counter()-start}')







