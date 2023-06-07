from bot import bot, get_last_cmd
from parse_config import get_players
from rating import add_record
from teams import choose_team_num
from telebot import types

chosen_players = {}


@bot.callback_query_handler(func=lambda call: call.data == 'choose_players_btn')
def handle_choose_players_btn(call):
    choose_players(call.message)


def choose_players(message):
    global chosen_players

    players = get_players()
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

    players = get_players()
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
    global chosen_players

    last_cmd = get_last_cmd()
    if last_cmd == 'propose_teams':
        choose_team_num(call.message, chosen_players)
        chosen_players = {}
    elif last_cmd == 'add_record':
        add_record(call.message, chosen_players)
        chosen_players = {}
