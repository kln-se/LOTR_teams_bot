import telebot
from telebot.types import BotCommand
from src.access import check_white_list_decorator
from src.parse_config import get_token

bot = telebot.TeleBot(get_token())

start_prompt = '''Этот бот создан для участников чата «Властелин Котец👑» и выполняет следующие основные функции:
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
    BotCommand(description='Завершить рассылку уведомлений об игре игрокам;', command='/stop_all_notifications'),
    BotCommand(description='Начало работы с ботом, обновление команд бота;', command='/start'),
    BotCommand(description='Список открытых команд, доступных боту;', command='/help'),
    BotCommand(description='Ссылка на канал в Discord;', command='/discord'),
    BotCommand(description='Ссылка на модификацию Ennorath mod 1.9.6.6;', command='/ennorathmod'),
]

cmds = ''.join([f'{cmd.command} - {cmd.description}\n' for cmd in cmds_list])


# ----------------------------------------------------------------------------------------------------------------------
# Common commands
# ----------------------------------------------------------------------------------------------------------------------

@bot.message_handler(commands=['start'])
@check_white_list_decorator(bot_instance=bot)
def start_handler(message):
    bot.set_my_commands(cmds_list)
    bot.reply_to(message, start_prompt)


@bot.message_handler(commands=['help'])
@check_white_list_decorator(bot_instance=bot)
def help_handler(message):
    bot.reply_to(message, cmds)


@bot.message_handler(commands=['discord'])
@check_white_list_decorator(bot_instance=bot)
def discord_handler(message):
    bot.reply_to(message, 'https://discord.gg/BsQrgxPZ')


@bot.message_handler(commands=['ennorathmod'])
@check_white_list_decorator(bot_instance=bot)
def discord_handler(message):
    bot.reply_to(message, 'https://ennorathmod.ru/forum/topic/1092/')


def get_bot_instance():
    global bot
    return bot
