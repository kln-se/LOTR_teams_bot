from telebot import types
import src.choose_players  # Используется callback 'choose_players_btn'
from src.poll import handle_last_poll_participants_btn  # Используется callback 'last_poll_participants_btn'
from src.access import check_white_list_decorator, check_admin_list_decorator
from src.bot import get_bot_instance
from src.parse_config import get_players
from src.storage import MemoryStorage

bot = get_bot_instance()


@bot.message_handler(commands=['tag_players'])
@check_admin_list_decorator(bot_instance=bot)
def tag_players_handler(message):
    MemoryStorage.get_instance(message.chat.id).callback_func_ref = start_tag_players

    keyboard = types.InlineKeyboardMarkup()
    choose_players_btn = types.InlineKeyboardButton(text='Выбрать игроков', callback_data='choose_players_btn')
    last_poll_participants_btn = types.InlineKeyboardButton(text='Участники последнего опроса',
                                                            callback_data='last_poll_participants_btn')
    keyboard.add(choose_players_btn, last_poll_participants_btn)

    bot.send_message(chat_id=message.chat.id, text='Кто будет в командах?', reply_markup=keyboard)


@bot.message_handler(commands=['stop_tag_players'])
@check_admin_list_decorator(bot_instance=bot)
def stop_tag_players_handler(message):
    bot.reply_to(message, 'Функционал в процессе разработки')


def start_tag_players(message, chosen_players, header='Проголосуйте в опросе!\n'):
    MemoryStorage.get_instance(message.chat.id).subscribers = chosen_players

    prompt = create_prompt(message, header)
    bot.send_message(chat_id=message.chat.id, text=prompt)

def tag_players_over_time():
    None

def create_prompt(message, header: str = ''):
    players = get_players()
    s = header
    for player_id in MemoryStorage.get_instance(message.chat.id).subscribers:
        if players[int(player_id)][0]:
            s += f' {players[int(player_id)][0]}'

    return s
