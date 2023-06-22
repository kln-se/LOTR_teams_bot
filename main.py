import time
import logging
from datetime import datetime
import src.poll
import src.rating
import src.tag_players
import src.teams
from src.bot import get_bot_instance

if __name__ == "__main__":
    logging.basicConfig(filename='errors.log', level=logging.ERROR)
    while True:
        time.sleep(5)
        try:
            bot = get_bot_instance()
            print(datetime.now(), "\tbot started...")
            bot.polling(none_stop=True, interval=1)
        except Exception as e:
            print(datetime.now(), "\tbot has terminated with an error...")
            logging.exception(e)
