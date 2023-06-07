import telebot
from access import check_white_list
from parse_config import get_token
from telebot.types import BotCommand


bot = telebot.TeleBot(get_token())

last_cmd = None

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
    BotCommand(description='Выбрать игроков для рассылки уведомлений об игре;', command='/tag_players'),
    BotCommand(description='Завершить рассылку уведомлений об игре игрокам;', command='/stop_tag_players'),
    BotCommand(description='Начало работы с ботом, обновление команд бота;', command='/start'),
    BotCommand(description='Список всех команд, доступных боту;', command='/help')
]

cmds = ''.join([f'{cmd.command} - {cmd.description}\n' for cmd in cmds_list])


# ----------------------------------------------------------------------------------------------------------------------
# Common commands
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


def get_last_cmd():
    return last_cmd


def set_last_cmd(cmd: str):
    global last_cmd
    last_cmd = cmd
