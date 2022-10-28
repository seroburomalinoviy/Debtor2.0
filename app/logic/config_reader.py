import configparser
from dataclasses import dataclass

@dataclass(frozen=True)
class TGBot:
    token: str
    admin_ids: list

@dataclass(frozen=True)
class Dbase:
    hostname: str
    username: str
    password: str
    name: str

@dataclass
class Config:
    tg_bot: TGBot
    db: Dbase

def load_config(path: str):
    config = configparser.ConfigParser()
    config.read(path)

    tg_bot = config["tg_config"]
    db = config["db_config"]

    return Config(
        tg_bot = TGBot(
            token=tg_bot["token"],
            admin_ids = [int(tg_bot["admin1_id"]),int(tg_bot["admin2_id"]),int(tg_bot["admin3_id"])]
        ),
        db = Dbase(
            hostname=db["DB_HOSTNAME"],
            username=db["DB_USERNAME"],
            password=db["DB_PASSWORD"],
            name=db["DB_NAME"]

        )
    )

