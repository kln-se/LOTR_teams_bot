import random
from telebot import types

# My imports
from access import check_white_list
from bot import bot, set_last_cmd
from parse_config import get_players


teams_count = None
chosen_players_names = {}


@bot.message_handler(commands=['propose_teams'])
def propose_teams_handler(message):
    if check_white_list(message.from_user.id):

        set_last_cmd('propose_teams')

        keyboard = types.InlineKeyboardMarkup()
        choose_players_btn = types.InlineKeyboardButton(text='Выбрать игроков', callback_data='choose_players_btn')
        last_poll_participants_btn = types.InlineKeyboardButton(text='Участники последнего опроса',
                                                                callback_data='last_poll_participants_btn')
        keyboard.add(choose_players_btn, last_poll_participants_btn)

        bot.send_message(chat_id=message.chat.id, text='Кто будет в командах?', reply_markup=keyboard)


@bot.callback_query_handler(func=lambda call: call.data in ['teams_2_btn', 'teams_3_btn', 'teams_4_btn'])
def handle_teams_x_btn(call):
    global chosen_players_names
    global teams_count

    if call.data == 'teams_2_btn':
        teams_count = 2
        keyboard = types.InlineKeyboardMarkup()
        regen_teams_btn = types.InlineKeyboardButton(text='Пересоздать команды', callback_data='regen_teams_btn')
        keyboard.add(regen_teams_btn)
        bot.send_message(chat_id=call.message.chat.id,
                         text=create_random_teams(chosen_players_names.copy(), teams_count),
                         reply_markup=keyboard)
    elif call.data == 'teams_3_btn':
        teams_count = 3
        keyboard = types.InlineKeyboardMarkup()
        regen_teams_btn = types.InlineKeyboardButton(text='Пересоздать команды', callback_data='regen_teams_btn')
        keyboard.add(regen_teams_btn)
        bot.send_message(chat_id=call.message.chat.id,
                         text=create_random_teams(chosen_players_names.copy(), teams_count),
                         reply_markup=keyboard)

    elif call.data == 'teams_4_btn':
        teams_count = 4
        keyboard = types.InlineKeyboardMarkup()
        regen_teams_btn = types.InlineKeyboardButton(text='Пересоздать команды', callback_data='regen_teams_btn')
        keyboard.add(regen_teams_btn)
        bot.send_message(chat_id=call.message.chat.id,
                         text=create_random_teams(chosen_players_names.copy(), teams_count),
                         reply_markup=keyboard)


@bot.callback_query_handler(func=lambda call: call.data == 'regen_teams_btn')
def handle_regen_teams_btn(call):
    global chosen_players_names
    global teams_count

    if not teams_count or not chosen_players_names:
        bot.send_message(chat_id=call.message.chat.id,
                         text='Сначала необходимо выбрать игроков и количество команд.')
    else:
        keyboard = types.InlineKeyboardMarkup()
        regen_teams_btn = types.InlineKeyboardButton(text='Пересоздать команды', callback_data='regen_teams_btn')
        keyboard.add(regen_teams_btn)
        bot.send_message(chat_id=call.message.chat.id,
                         text=create_random_teams(chosen_players_names.copy(), teams_count),
                         reply_markup=keyboard)


def choose_team_num(message, players_to_play):
    global teams_count
    global chosen_players_names

    chosen_players_names = {}
    teams_count = None

    players = get_players()
    for player_id in players_to_play:
        if players_to_play[player_id]:
            chosen_players_names[int(player_id)] = players[int(player_id)][1]

    keyboard = types.InlineKeyboardMarkup()
    teams_2_btn = types.InlineKeyboardButton(text='2', callback_data='teams_2_btn')
    teams_3_btn = types.InlineKeyboardButton(text='3', callback_data='teams_3_btn')
    teams_4_btn = types.InlineKeyboardButton(text='4', callback_data='teams_4_btn')
    keyboard.add(teams_2_btn, teams_3_btn, teams_4_btn)

    bot.send_message(chat_id=message.chat.id,
                     text=f'Количество игроков: {len(chosen_players_names)}. Сколько будет команд?:',
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
