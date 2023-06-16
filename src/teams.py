import random
from telebot import types
import src.choose_players
from src.access import check_white_list
from src.bot import get_bot
from src.parse_config import get_players
from src.storage import MemoryStorage

bot = get_bot()


@bot.message_handler(commands=['propose_teams'])
def propose_teams_handler(message):
    if check_white_list(message.from_user.id):
        MemoryStorage.get_instance(message.chat.id).callback_func_ref = choose_team_num

        keyboard = types.InlineKeyboardMarkup()
        choose_players_btn = types.InlineKeyboardButton(text='Выбрать игроков', callback_data='choose_players_btn')
        last_poll_participants_btn = types.InlineKeyboardButton(text='Участники последнего опроса',
                                                                callback_data='last_poll_participants_btn')
        keyboard.add(choose_players_btn, last_poll_participants_btn)

        bot.send_message(chat_id=message.chat.id, text='Кто будет в командах?', reply_markup=keyboard)


@bot.callback_query_handler(func=lambda call: call.data in ['teams_2_btn', 'teams_3_btn', 'teams_4_btn'])
def handle_teams_x_btn(call):
    if call.data == 'teams_2_btn':
        MemoryStorage.get_instance(call.message.chat.id).teams_count = 2
        keyboard = types.InlineKeyboardMarkup()
        regen_teams_btn = types.InlineKeyboardButton(text='Пересоздать команды', callback_data='regen_teams_btn')
        keyboard.add(regen_teams_btn)
        bot.send_message(chat_id=call.message.chat.id,
                         text=create_random_teams(
                             MemoryStorage.get_instance(call.message.chat.id).chosen_players_names.copy(),
                             MemoryStorage.get_instance(call.message.chat.id).teams_count),
                         reply_markup=keyboard)
    elif call.data == 'teams_3_btn':
        MemoryStorage.get_instance(call.message.chat.id).teams_count = 3
        keyboard = types.InlineKeyboardMarkup()
        regen_teams_btn = types.InlineKeyboardButton(text='Пересоздать команды', callback_data='regen_teams_btn')
        keyboard.add(regen_teams_btn)
        bot.send_message(chat_id=call.message.chat.id,
                         text=create_random_teams(
                             MemoryStorage.get_instance(call.message.chat.id).chosen_players_names.copy(),
                             MemoryStorage.get_instance(call.message.chat.id).teams_count),
                         reply_markup=keyboard)

    elif call.data == 'teams_4_btn':
        MemoryStorage.get_instance(call.message.chat.id).teams_count = 4
        keyboard = types.InlineKeyboardMarkup()
        regen_teams_btn = types.InlineKeyboardButton(text='Пересоздать команды', callback_data='regen_teams_btn')
        keyboard.add(regen_teams_btn)
        bot.send_message(chat_id=call.message.chat.id,
                         text=create_random_teams(
                             MemoryStorage.get_instance(call.message.chat.id).chosen_players_names.copy(),
                             MemoryStorage.get_instance(call.message.chat.id).teams_count),
                         reply_markup=keyboard)


@bot.callback_query_handler(func=lambda call: call.data == 'regen_teams_btn')
def handle_regen_teams_btn(call):
    if not MemoryStorage.get_instance(call.message.chat.id).teams_count or not MemoryStorage.get_instance(
            call.message.chat.id).chosen_players_names:
        bot.send_message(chat_id=call.message.chat.id,
                         text='Сначала необходимо выбрать игроков и количество команд.')
    else:
        keyboard = types.InlineKeyboardMarkup()
        regen_teams_btn = types.InlineKeyboardButton(text='Пересоздать команды', callback_data='regen_teams_btn')
        keyboard.add(regen_teams_btn)
        bot.send_message(chat_id=call.message.chat.id,
                         text=create_random_teams(
                             MemoryStorage.get_instance(call.message.chat.id).chosen_players_names.copy(),
                             MemoryStorage.get_instance(call.message.chat.id).teams_count),
                         reply_markup=keyboard)


def choose_team_num(message, players_to_play):
    MemoryStorage.get_instance(message.chat.id).chosen_players_names = {}
    MemoryStorage.get_instance(message.chat.id).teams_count = None

    players = get_players()
    for player_id in players_to_play:
        if players_to_play[player_id]:
            MemoryStorage.get_instance(message.chat.id).chosen_players_names[int(player_id)] = players[int(player_id)][
                1]

    keyboard = types.InlineKeyboardMarkup()
    teams_2_btn = types.InlineKeyboardButton(text='2', callback_data='teams_2_btn')
    teams_3_btn = types.InlineKeyboardButton(text='3', callback_data='teams_3_btn')
    teams_4_btn = types.InlineKeyboardButton(text='4', callback_data='teams_4_btn')
    keyboard.add(teams_2_btn, teams_3_btn, teams_4_btn)

    bot.send_message(chat_id=message.chat.id,
                     text='Количество игроков: {0}. Сколько будет команд?'.format(
                         len(MemoryStorage.get_instance(message.chat.id).chosen_players_names)),
                     reply_markup=keyboard)


def create_random_teams(players, num_teams: int, consider_rating: bool = False) -> str:
    """
    Данная функция предлагает разбиение игроков по командам.
    :param players: Словарь, где ключ это обозначение игрока: @player_name; значение: имя игрока
    :param num_teams: Количество команд.
    :param consider_rating: Учитывать рейтинг при составлении команд.
    :return: Строка с составом команд.
    """
    division = []
    s = ""
    if not consider_rating:
        avg_players_per_team = len(players) // num_teams
        remainder = len(players) % num_teams

        # Добавляем команды со средним количеством людей
        for i in range(num_teams - remainder):
            division.append(avg_players_per_team)

        # Добавляем команды со средним количеством людей + 1
        for i in range(remainder):
            division.append(avg_players_per_team + 1)

        for idx, d in enumerate(division):
            s += "Команда " + str(idx + 1) + ":\n"
            temp_team = []
            for player in range(d):
                random_player_id = random.choice(list(players.keys()))
                temp_team.append(players[random_player_id])
                del players[random_player_id]
            temp_team.sort()
            s += ''.join([f'\t- {player_name}\n' for player_name in temp_team])
    return s[:-1]
