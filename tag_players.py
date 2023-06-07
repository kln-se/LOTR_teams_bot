from access import check_white_list, check_admin_list
from bot import bot


@bot.message_handler(commands=['tag_players'])
def tag_players_handler(message):
    if check_white_list(message.from_user.id):
        None


@bot.message_handler(commands=['stop_tag_players'])
def stop_tag_players_handler(message):
    if check_admin_list(message.from_user.id):
        None
    else:
        bot.reply_to(message, 'Остановить отправку уведомления сразу всем игрокам вам недоступно.')