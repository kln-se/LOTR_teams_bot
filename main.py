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

players = {}
players_to_play = {}
teams_count = None
last_poll_results = {}
choose_players_btn_callback_names = {}
choose_winners_btn_callback_names = {}
for p in config.options('PLAYERS'):
    players[int(p)] = [str(x) for x in config.get('PLAYERS', p).split(';')]
white_list = [int(x) for x in config.get('SECURITY', 'white_list').split(';')]
admin_list = [int(x) for x in config.get('SECURITY', 'admin_list').split(';')]
contributor = None

start_prompt = '''Этот бот создан для участников чата «Властелін Котец👑» и выполняет следующие функции:
✔ Старт опроса о следующей игре;
✔ Предложение по составу команд;
✔ Информация по рейтингу игроков.
'''

cmds_list = [
    BotCommand(description='Старт опроса о следующей игре;', command='/start_poll'),
    BotCommand(description='Предложение по разбиению по командам;', command='/propose_teams'),
    BotCommand(description='Инфорграфика с текущим рейтингом игроков;', command='/rating'),
    BotCommand(description='Добавить запись об игре и её результатах в статистику;', command='/add_record'),
    BotCommand(description='Начало работы с ботом, обновление команд бота;', command='/start'),
    BotCommand(description='Cписок всех команд, доступных боту;', command='/help')
]

cmds = "/start - начало работы с ботом;\n" \
       "/help - список всех доступных команд;\n" \
       "/start_poll - старт опроса о следующей игре;\n" \
       "/propose_teams - предложение по разбиению по командам;\n" \
       "/rating - инфорграфика с текущим рейтингом игроков;\n" \
       "/add_record - Добавить запись об игре в статистику;\n" \
       "/discord - ссылка на канал в Discord."


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
        poll_sent = bot.send_poll(
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
    if check_white_list(message.from_user.id):
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
def add_record(message):
    global contributor
    if check_white_list(message.from_user.id):
        contributor = message.from_user.id
        keyboard = types.InlineKeyboardMarkup()
        for p_id in players:
            temp_btn = types.InlineKeyboardButton(text="☐ " + players[p_id][1],
                                                  callback_data='choose_winner=' + str(p_id))
            keyboard.add(temp_btn)
            choose_winners_btn_callback_names['choose_winner=' + str(p_id)] = False
        finish_winners_choice_btn = types.InlineKeyboardButton(text="«Готово»",
                                                               callback_data='finish_winners_choice_btn')
        keyboard.add(finish_winners_choice_btn)
        bot.send_message(chat_id=message.chat.id,
                         text='Выберите победителей:',
                         reply_markup=keyboard)
    else:
        bot.reply_to(message, 'Добавление новых записей возможно только администрированными участниками.')


@bot.poll_answer_handler()
def handle_poll_answer(poll_answer):
    global last_poll_results
    poll_id = poll_answer.poll_id
    user_id = poll_answer.user.id
    option_ids = poll_answer.option_ids
    last_poll_results[user_id] = option_ids


@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    global players
    global last_poll_results
    global players_to_play
    global teams_count
    global choose_players_btn_callback_names
    global choose_winners_btn_callback_names
    global contributor

    if call.data == 'choose_players_btn':
        players_to_play = {}
        choose_players_btn_callback_names = {}
        teams_count = None
        keyboard = types.InlineKeyboardMarkup()
        for p_id in players:
            temp_btn = types.InlineKeyboardButton(text="☐ " + players[p_id][1],
                                                  callback_data='choose_player=' + str(p_id))
            keyboard.add(temp_btn)
            choose_players_btn_callback_names['choose_player=' + str(p_id)] = False
        finish_players_choice_btn = types.InlineKeyboardButton(text="«Готово»",
                                                               callback_data='finish_players_choice_btn')
        keyboard.add(finish_players_choice_btn)
        bot.send_message(chat_id=call.message.chat.id,
                         text='Выберите игроков:',
                         reply_markup=keyboard)
    elif call.data in choose_players_btn_callback_names:  # Обработка нажатия на имя игрока при выборе игроков для игры
        choose_players_btn_callback_names[call.data] = True
        updated_keyboard = types.InlineKeyboardMarkup()
        for player_btn_callback_name in choose_players_btn_callback_names:
            if choose_players_btn_callback_names[player_btn_callback_name]:
                temp_btn = types.InlineKeyboardButton(
                    text="☑ " + players[int(player_btn_callback_name.split('=')[1])][1],
                    callback_data=player_btn_callback_name)
            else:
                temp_btn = types.InlineKeyboardButton(
                    text="☐ " + players[int(player_btn_callback_name.split('=')[1])][1],
                    callback_data=player_btn_callback_name)
            updated_keyboard.add(temp_btn)
        finish_players_choice_btn = types.InlineKeyboardButton(text="«Готово»",
                                                               callback_data='finish_players_choice_btn')
        updated_keyboard.add(finish_players_choice_btn)
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=updated_keyboard)
    elif call.data in choose_winners_btn_callback_names:  # Обработка нажатия на имя игрока при выборе игроков-победителей
        choose_winners_btn_callback_names[call.data] = True
        updated_keyboard = types.InlineKeyboardMarkup()
        for winner_btn_callback_name in choose_winners_btn_callback_names:
            if choose_winners_btn_callback_names[winner_btn_callback_name]:
                temp_btn = types.InlineKeyboardButton(
                    text="☑ " + players[int(winner_btn_callback_name.split('=')[1])][1],
                    callback_data=winner_btn_callback_name)
            else:
                temp_btn = types.InlineKeyboardButton(
                    text="☐ " + players[int(winner_btn_callback_name.split('=')[1])][1],
                    callback_data=winner_btn_callback_name)
            updated_keyboard.add(temp_btn)
        finish_players_choice_btn = types.InlineKeyboardButton(text="«Готово»",
                                                               callback_data='finish_winners_choice_btn')
        updated_keyboard.add(finish_players_choice_btn)
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=updated_keyboard)
    elif call.data == 'finish_players_choice_btn':
        for player_btn_callback_name in choose_players_btn_callback_names:
            if choose_players_btn_callback_names[player_btn_callback_name]:
                players_to_play[int(player_btn_callback_name.split('=')[1])] = \
                    players[int(player_btn_callback_name.split('=')[1])][1]
        keyboard = types.InlineKeyboardMarkup()
        teams_2_btn = types.InlineKeyboardButton(text='2', callback_data='teams_2_btn')
        teams_3_btn = types.InlineKeyboardButton(text='3', callback_data='teams_3_btn')
        teams_4_btn = types.InlineKeyboardButton(text='4', callback_data='teams_4_btn')
        keyboard.add(teams_2_btn, teams_3_btn, teams_4_btn)
        bot.send_message(chat_id=call.message.chat.id,
                         text=f'Количество игроков: {len(players_to_play)}. Сколько будет команд?',
                         reply_markup=keyboard)
    elif call.data == 'last_poll_participants_btn':
        if last_poll_results:
            players_to_play = {}
            teams_count = None
            for t_id in last_poll_results:
                if 0 in last_poll_results[t_id] or 1 in last_poll_results[t_id]:
                    players_to_play[t_id] = players[t_id][1]
            keyboard = types.InlineKeyboardMarkup()
            teams_2_btn = types.InlineKeyboardButton(text='2', callback_data='teams_2_btn')
            teams_3_btn = types.InlineKeyboardButton(text='3', callback_data='teams_3_btn')
            teams_4_btn = types.InlineKeyboardButton(text='4', callback_data='teams_4_btn')
            keyboard.add(teams_2_btn, teams_3_btn, teams_4_btn)
            bot.send_message(chat_id=call.message.chat.id,
                             text=f'Судя по опросу игроков будет: {len(players_to_play)}. Сколько будет команд?',
                             reply_markup=keyboard)
        else:
            bot.send_message(chat_id=call.message.chat.id, text='Опросный лист пуст. Создайте новый опрос.')
    elif call.data == 'teams_2_btn':
        teams_count = 2
        keyboard = types.InlineKeyboardMarkup()
        regen_teams_btn = types.InlineKeyboardButton(text='Пересоздать команды', callback_data='regen_teams_btn')
        keyboard.add(regen_teams_btn)
        bot.send_message(chat_id=call.message.chat.id, text=teams.random_teamer(players_to_play.copy(), teams_count),
                         reply_markup=keyboard)
    elif call.data == 'teams_3_btn':
        teams_count = 3
        keyboard = types.InlineKeyboardMarkup()
        regen_teams_btn = types.InlineKeyboardButton(text='Пересоздать команды', callback_data='regen_teams_btn')
        keyboard.add(regen_teams_btn)
        bot.send_message(chat_id=call.message.chat.id, text=teams.random_teamer(players_to_play.copy(), teams_count),
                         reply_markup=keyboard)
    elif call.data == 'teams_4_btn':
        teams_count = 4
        keyboard = types.InlineKeyboardMarkup()
        regen_teams_btn = types.InlineKeyboardButton(text='Пересоздать команды', callback_data='regen_teams_btn')
        keyboard.add(regen_teams_btn)
        bot.send_message(chat_id=call.message.chat.id, text=teams.random_teamer(players_to_play.copy(), teams_count),
                         reply_markup=keyboard)
    elif call.data == 'regen_teams_btn':
        if teams_count == None or len(players_to_play) == 0:
            bot.send_message(chat_id=call.message.chat.id,
                             text='Сначала необходимо выбрать игроков и количество команд.')
        else:
            keyboard = types.InlineKeyboardMarkup()
            regen_teams_btn = types.InlineKeyboardButton(text='Пересоздать команды', callback_data='regen_teams_btn')
            keyboard.add(regen_teams_btn)
            bot.send_message(chat_id=call.message.chat.id,
                             text=teams.random_teamer(players_to_play.copy(), teams_count),
                             reply_markup=keyboard)
    elif call.data == 'finish_winners_choice_btn':
        winners = {}
        for winner_btn_callback_name in choose_winners_btn_callback_names:
            if choose_winners_btn_callback_names[winner_btn_callback_name]:
                winners[int(winner_btn_callback_name.split('=')[1])] = True
            else:
                winners[int(winner_btn_callback_name.split('=')[1])] = False
        if choose_winners_btn_callback_names:
            df = rating.load_df('statistics_data/statistics.csv')
            rating.add_record(df, dt.datetime.now(), contributor, winners)
            rating.save_df(df, 'statistics_data/statistics.csv')
            contributor = None
            choose_winners_btn_callback_names = {}
            bot.send_message(chat_id=call.message.chat.id, text='Запись добавлена.')
        else:
            bot.send_message(chat_id=call.message.chat.id, text='Выберите победителей, текущий список пуст.')


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

