import time
import logging
from bot import bot

# My modules
import poll
import choose_players

if __name__ == "__main__":
    logging.basicConfig(filename='errors.log', level=logging.ERROR)
    while True:
        time.sleep(5)
        try:
            print("bot started...")
            bot.polling(none_stop=True, interval=1)
        except Exception as e:
            logging.exception(e)
