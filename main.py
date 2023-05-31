import telebot
import datetime as dt
from datetime import datetime
from configparser import ConfigParser
from telebot import types
from telebot.types import BotCommand
import teams
import rating
import plots
import logging
import time

config = ConfigParser()
config.read('config.ini')
bot = telebot.TeleBot(config.get('CONNECTION', 'token'))

# Global variables
players = {}
chosen_players = {}
chosen_players_names = {}
teams_count = None
last_poll_results = {}
contributor = None
last_cmd = None

for p in config.options('PLAYERS'):
    players[int(p)] = [str(x) for x in config.get('PLAYERS', p).split(';')]
white_list = [int(x) for x in config.get('SECURITY', 'white_list').split(';')]
admin_list = [int(x) for x in config.get('SECURITY', 'admin_list').split(';')]

start_prompt = '''Этот бот создан для участников чата «Властелин Котец👑» и выполняет следующие функции:
✔ Старт опроса о следующей игре;
✔ Предложение по составу команд;
✔ Информация по рейтингу игроков.
'''

cmds_list = [
    BotCommand(description='Старт опроса о следующей игре;', command='/start_poll'),
    BotCommand(description='Предложение по разбиению по командам;', command='/propose_teams'),
    BotCommand(description='Инфографика с текущим рейтингом игроков;', command='/rating'),
    BotCommand(description='Добавить запись об игре и её результатах в статистику;', command='/add_record'),
    BotCommand(description='Начало работы с ботом, обновление команд бота;', command='/start'),
    BotCommand(description='Список всех команд, доступных боту;', command='/help')
]

cmds = ''.join([f'{cmd.command} - {cmd.description}\n' for cmd in cmds_list])


# ----------------------------------------------------------------------------------------------------------------------
# Commands handlers
# ----------------------------------------------------------------------------------------------------------------------

@bot.message_handler(commands=['start'])
def start_handler(message):
    if check_white_list(message.from_user.id):
        bot.set_my_commands(cmds_list)
        bot.reply_to(message, start_prompt)


@bot.message_handler(commands=['help'])
def help_handler(message):
    if check_white_list(message.from_user.id):
        bot.reply_to(message, cmds)


@bot.message_handler(commands=['discord'])
def discord_handler(message):
    if check_white_list(message.from_user.id):
        bot.reply_to(message, 'https://discord.gg/BsQrgxPZ')


@bot.message_handler(commands=['start_poll'])
def poll_handler(message):
    global last_poll_results
    if check_white_list(message.from_user.id):
        bot.send_poll(
            chat_id=message.chat.id,
            question='Кто будет сегодня играть?',
            options=['☑️ Буду, как обычно в 22:00',
                     '🤔 Буду, но точное время пока не могу сказать',
                     '🕑 Предложу другое время (напишу ниже)',
                     '🤡 Пока не знаю, если будет настроение к 22:00',
                     '🙅‍♂️ Сегодня не смогу'],
            is_anonymous=False,
            allows_multiple_answers=True,
            close_date=datetime.combine(datetime.today().date(), datetime.min.time()),
            reply_to_message_id=message.id
        )
        last_poll_results = {}


@bot.message_handler(commands=['propose_teams'])
def propose_teams_handler(message):
    global last_cmd

    if check_white_list(message.from_user.id):
        last_cmd = 'propose_teams'

        keyboard = types.InlineKeyboardMarkup()
        choose_players_btn = types.InlineKeyboardButton(text='Выбрать игроков', callback_data='choose_players_btn')
        last_poll_participants_btn = types.InlineKeyboardButton(text='Участники последнего опроса',
                                                                callback_data='last_poll_participants_btn')
        keyboard.add(choose_players_btn, last_poll_participants_btn)

        bot.send_message(chat_id=message.chat.id, text='Кто будет в командах?', reply_markup=keyboard)


@bot.message_handler(commands=['rating'])
def discord_handler(message):
    if check_white_list(message.from_user.id):
        plots.plot_statistics(rating.load_df('statistics_data/statistics.csv'), players)
        with open('statistics_data/statistics.png', 'rb') as photo:
            bot.send_photo(message.chat.id, photo)


@bot.message_handler(commands=['add_record'])
def add_record_handler(message):
    global last_cmd
    global contributor

    if check_white_list(message.from_user.id):
        last_cmd = 'add_record'
        contributor = message.from_user.id
        choose_players(message)


@bot.poll_answer_handler()
def handle_poll_answer(poll_answer):
    global last_poll_results
    poll_id = poll_answer.poll_id
    player_id = poll_answer.user.id
    option_ids = poll_answer.option_ids
    last_poll_results[player_id] = option_ids


# ----------------------------------------------------------------------------------------------------------------------
# Callback queries handlers
# ----------------------------------------------------------------------------------------------------------------------
@bot.callback_query_handler(func=lambda call: call.data == 'last_poll_participants_btn')
def handle_last_poll_participants_btn(call):
    global last_poll_results

    if last_poll_results:
        polled_players = {}
        for player_id in last_poll_results:
            if 0 in last_poll_results[player_id] or 1 in last_poll_results[player_id]:
                polled_players[player_id] = True

        bot.send_message(chat_id=call.message.chat.id,
                         text=f'Судя по опросу игроков будет: *{len(polled_players)}*',
                         parse_mode='Markdown')
        choose_team_num(call.message, polled_players)
    else:
        bot.send_message(chat_id=call.message.chat.id, text='Опросный лист пуст. Создайте новый опрос.')


@bot.callback_query_handler(func=lambda call: call.data == 'choose_players_btn')
def handle_choose_players_btn(call):
    choose_players(call.message)


def choose_players(message):
    global players
    global chosen_players
    global last_cmd

    chosen_players = {}

    keyboard = types.InlineKeyboardMarkup()
    for player_id in players:
        temp_btn = types.InlineKeyboardButton(text="☐ " + players[player_id][1], callback_data=str(player_id))
        keyboard.add(temp_btn)
        chosen_players[str(player_id)] = False
    finish_players_choice_btn = types.InlineKeyboardButton(text="«Готово»", callback_data='finish_players_choice_btn')
    keyboard.add(finish_players_choice_btn)

    bot.send_message(chat_id=message.chat.id,
                     text='Выберите игроков:',
                     reply_markup=keyboard)


@bot.callback_query_handler(func=lambda call: call.data in chosen_players)
def handle_player_choice(call):
    global chosen_players

    chosen_players[call.data] = True

    updated_keyboard = types.InlineKeyboardMarkup()
    for player_id in chosen_players:
        if chosen_players[player_id]:
            temp_btn = types.InlineKeyboardButton(
                text="☑ " + players[int(player_id)][1],
                callback_data=player_id)
        else:
            temp_btn = types.InlineKeyboardButton(
                text="☐ " + players[int(player_id)][1],
                callback_data=player_id)
        updated_keyboard.add(temp_btn)
    finish_players_choice_btn = types.InlineKeyboardButton(text="«Готово»",
                                                           callback_data='finish_players_choice_btn')
    updated_keyboard.add(finish_players_choice_btn)

    bot.edit_message_reply_markup(call.message.chat.id,
                                  call.message.message_id,
                                  reply_markup=updated_keyboard)


@bot.callback_query_handler(func=lambda call: call.data == 'finish_players_choice_btn')
def handle_finish_players_choice_btn(call):
    global last_cmd
    global chosen_players

    if last_cmd == 'propose_teams':
        choose_team_num(call.message, chosen_players)
    elif last_cmd == 'add_record':
        add_record(call.message, chosen_players)


def choose_team_num(message, players_to_play):
    global teams_count
    global chosen_players_names

    chosen_players_names = {}
    teams_count = None

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


def add_record(message, winners):
    global contributor

    if winners:
        df = rating.load_df('statistics_data/statistics.csv')
        rating.add_record(df, dt.datetime.now(), contributor, winners)
        rating.save_df(df, 'statistics_data/statistics.csv')
        contributor = None
        bot.send_message(chat_id=message.chat.id, text='Запись добавлена.')
    else:
        bot.send_message(chat_id=message.chat.id, text='Выберите победителей, текущий список пуст.')


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
                         text=teams.create_random_teams(chosen_players_names.copy(), teams_count),
                         reply_markup=keyboard)
    elif call.data == 'teams_3_btn':
        teams_count = 3
        keyboard = types.InlineKeyboardMarkup()
        regen_teams_btn = types.InlineKeyboardButton(text='Пересоздать команды', callback_data='regen_teams_btn')
        keyboard.add(regen_teams_btn)
        bot.send_message(chat_id=call.message.chat.id,
                         text=teams.create_random_teams(chosen_players_names.copy(), teams_count),
                         reply_markup=keyboard)

    elif call.data == 'teams_4_btn':
        teams_count = 4
        keyboard = types.InlineKeyboardMarkup()
        regen_teams_btn = types.InlineKeyboardButton(text='Пересоздать команды', callback_data='regen_teams_btn')
        keyboard.add(regen_teams_btn)
        bot.send_message(chat_id=call.message.chat.id,
                         text=teams.create_random_teams(chosen_players_names.copy(), teams_count),
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
                         text=teams.create_random_teams(chosen_players_names.copy(), teams_count),
                         reply_markup=keyboard)


def check_white_list(user_id) -> bool:
    if user_id in white_list:
        return True
    else:
        return False


def check_admin_list(user_id) -> bool:
    if user_id in admin_list:
        return True
    else:
        return False


if __name__ == "__main__":
    logging.basicConfig(filename='errors.log', level=logging.ERROR)
    while True:
        time.sleep(5)
        try:
            print("bot started...")
            bot.polling(none_stop=True, interval=1)
        except Exception as e:
            logging.exception(e)
