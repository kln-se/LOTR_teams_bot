import time
import logging
from datetime import datetime
import src.poll
import src.rating
import src.teams
from src.bot import get_bot


if __name__ == "__main__":
    logging.basicConfig(filename='errors.log', level=logging.ERROR)
    while True:
        time.sleep(5)
        try:
            bot = get_bot()
            print(datetime.now(), "\tbot started...")
            bot.polling(none_stop=True, interval=1)
        except Exception as e:
            print(datetime.now(), "\tbot has terminated with an error...")
            logging.exception(e)
