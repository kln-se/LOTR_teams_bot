from telebot import types
from src.bot import get_bot_instance
from src.parse_config import get_players
from src.storage import MemoryStorage

bot = get_bot_instance()


@bot.callback_query_handler(func=lambda call: call.data == 'choose_players_btn')
def handle_choose_players_btn(call):
    bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.id)
    choose_players(call.message)


def choose_players(message):
    players = get_players()
    MemoryStorage.get_instance(message.chat.id).chosen_players = {}

    keyboard = types.InlineKeyboardMarkup()
    for player_id in players:
        temp_btn = types.InlineKeyboardButton(text="☐ " + players[player_id][1], callback_data=str(player_id))
        keyboard.add(temp_btn)
        MemoryStorage.get_instance(message.chat.id).chosen_players[str(player_id)] = False
    choose_all_btn = types.InlineKeyboardButton(text="«Выбрать всех»", callback_data='choose_all_btn')
    finish_players_choice_btn = types.InlineKeyboardButton(text="«Готово»", callback_data='finish_players_choice_btn')
    keyboard.add(choose_all_btn, finish_players_choice_btn)

    bot.send_message(chat_id=message.chat.id,
                     text='Выберите игроков:',
                     reply_markup=keyboard)


@bot.callback_query_handler(
    func=lambda call: call.data in MemoryStorage.get_instance(call.message.chat.id).chosen_players)
def handle_player_choice(call):
    players = get_players()
    if MemoryStorage.get_instance(call.message.chat.id).chosen_players[call.data]:
        MemoryStorage.get_instance(call.message.chat.id).chosen_players[call.data] = False
    else:
        MemoryStorage.get_instance(call.message.chat.id).chosen_players[call.data] = True

    updated_keyboard = types.InlineKeyboardMarkup()
    for player_id in MemoryStorage.get_instance(call.message.chat.id).chosen_players:
        if MemoryStorage.get_instance(call.message.chat.id).chosen_players[player_id]:
            temp_btn = types.InlineKeyboardButton(
                text="☑ " + players[int(player_id)][1],
                callback_data=player_id)
        else:
            temp_btn = types.InlineKeyboardButton(
                text="☐ " + players[int(player_id)][1],
                callback_data=player_id)
        updated_keyboard.add(temp_btn)
    choose_all_btn = types.InlineKeyboardButton(text="«Выбрать всех»", callback_data='choose_all_btn')
    finish_players_choice_btn = types.InlineKeyboardButton(text="«Готово»", callback_data='finish_players_choice_btn')
    updated_keyboard.add(choose_all_btn, finish_players_choice_btn)

    bot.edit_message_reply_markup(call.message.chat.id,
                                  call.message.message_id,
                                  reply_markup=updated_keyboard)


@bot.callback_query_handler(func=lambda call: call.data == 'finish_players_choice_btn')
def handle_finish_players_choice_btn(call):
    callback_func = MemoryStorage.get_instance(call.message.chat.id).callback_func_ref
    if callback_func:
        callback_func(call, MemoryStorage.get_instance(call.message.chat.id).chosen_players)
    else:
        bot.reply_to(call.message, '❗️Начальная команда не определена. Выберите команду из списка /help.')


@bot.callback_query_handler(func=lambda call: call.data == 'choose_all_btn')
def handle_choose_all_btn(call):
    players = get_players()

    updated_keyboard = types.InlineKeyboardMarkup()
    for player_id in MemoryStorage.get_instance(call.message.chat.id).chosen_players.keys():
        temp_btn = types.InlineKeyboardButton(
            text="☑ " + players[int(player_id)][1],
            callback_data=player_id)
        updated_keyboard.add(temp_btn)

        MemoryStorage.get_instance(call.message.chat.id).chosen_players[player_id] = True

    choose_all_btn = types.InlineKeyboardButton(text="«Выбрать всех»", callback_data='choose_all_btn')
    finish_players_choice_btn = types.InlineKeyboardButton(text="«Готово»", callback_data='finish_players_choice_btn')
    updated_keyboard.add(choose_all_btn, finish_players_choice_btn)

    bot.edit_message_reply_markup(call.message.chat.id,
                                  call.message.message_id,
                                  reply_markup=updated_keyboard)


@bot.callback_query_handler(func=lambda call: call.data == 'choose_last_poll_participants_btn')
def handle_last_poll_participants_btn(call):
    if MemoryStorage.get_instance(call.message.chat.id).last_poll_results:
        polled_players = {}
        for player_id in MemoryStorage.get_instance(call.message.chat.id).last_poll_results:
            if 0 in MemoryStorage.get_instance(call.message.chat.id).last_poll_results[player_id] or 1 in \
                    MemoryStorage.get_instance(call.message.chat.id).last_poll_results[player_id]:
                polled_players[str(player_id)] = True
            else:
                polled_players[str(player_id)] = False

        callback_func = MemoryStorage.get_instance(call.message.chat.id).callback_func_ref
        if callback_func:
            callback_func(call, polled_players)
    else:
        bot.send_message(chat_id=call.message.chat.id,
                         text='❗️Опросный лист пуст.'
                              '\nНеобходимо создать новый опрос.')


def choose_winners(message):
    players = get_players()
    MemoryStorage.get_instance(message.chat.id).chosen_players = {}

    keyboard = types.InlineKeyboardMarkup()
    for player_id in players:
        temp_win_btn = types.InlineKeyboardButton(text="☐ " + players[player_id][1],
                                                  callback_data=str(player_id) + '1')  # player_id + '1', если winner
        temp_lose_btn = types.InlineKeyboardButton(text="☐ " + players[player_id][1],
                                                   callback_data=str(player_id) + '0')  # player_id + '0', если loser
        keyboard.add(temp_win_btn, temp_lose_btn)
        MemoryStorage.get_instance(message.chat.id).chosen_players[str(player_id)] = None
    finish_players_choice_btn = types.InlineKeyboardButton(text="«Готово»", callback_data='finish_players_choice_btn')
    keyboard.add(finish_players_choice_btn)

    bot.send_message(chat_id=message.chat.id,
                     text='Выберите победителей и проигравших:',
                     reply_markup=keyboard)


@bot.callback_query_handler(
    func=lambda call: call.data[:-1] in MemoryStorage.get_instance(call.message.chat.id).chosen_players)
def handle_winner_choice(call):
    players = get_players()
    # Если нажата win_btn
    if int(call.data[-1]):
        # Игрок уже отнесён к winner
        if MemoryStorage.get_instance(call.message.chat.id).chosen_players[call.data[:-1]]:
            MemoryStorage.get_instance(call.message.chat.id).chosen_players[call.data[:-1]] = None
        # Игрок не отнесён ни к winner, ни к loser или является loser
        else:
            MemoryStorage.get_instance(call.message.chat.id).chosen_players[call.data[:-1]] = True
    # Если нажата lose_btn
    else:
        # Игрок уже отнесён к loser
        if MemoryStorage.get_instance(call.message.chat.id).chosen_players[call.data[:-1]] is False:
            MemoryStorage.get_instance(call.message.chat.id).chosen_players[call.data[:-1]] = None
        # Игрок не отнесён ни к winner, ни к loser или является loser
        else:
            MemoryStorage.get_instance(call.message.chat.id).chosen_players[call.data[:-1]] = False

    updated_keyboard = types.InlineKeyboardMarkup()
    for player_id in MemoryStorage.get_instance(call.message.chat.id).chosen_players:
        if MemoryStorage.get_instance(call.message.chat.id).chosen_players[player_id] is None:
            temp_win_btn = types.InlineKeyboardButton(text="☐ " + players[int(player_id)][1],
                                                      callback_data=player_id + '1')
            temp_lose_btn = types.InlineKeyboardButton(text="☐ " + players[int(player_id)][1],
                                                       callback_data=player_id + '0')
        elif MemoryStorage.get_instance(call.message.chat.id).chosen_players[player_id]:
            temp_win_btn = types.InlineKeyboardButton(text="🏆 " + players[int(player_id)][1],
                                                      callback_data=player_id + '1')
            temp_lose_btn = types.InlineKeyboardButton(text="☐ " + players[int(player_id)][1],
                                                       callback_data=player_id + '0')
        else:
            temp_win_btn = types.InlineKeyboardButton(text="☐ " + players[int(player_id)][1],
                                                      callback_data=player_id + '1')
            temp_lose_btn = types.InlineKeyboardButton(text="💀 " + players[int(player_id)][1],
                                                       callback_data=player_id + '0')
        updated_keyboard.add(temp_win_btn, temp_lose_btn)
    finish_players_choice_btn = types.InlineKeyboardButton(text="«Готово»", callback_data='finish_players_choice_btn')
    updated_keyboard.add(finish_players_choice_btn)

    bot.edit_message_reply_markup(call.message.chat.id,
                                  call.message.message_id,
                                  reply_markup=updated_keyboard)
