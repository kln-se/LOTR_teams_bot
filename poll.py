from access import check_white_list
from bot import bot
from datetime import datetime
from teams import choose_team_num

last_poll_results = {}


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


@bot.poll_answer_handler()
def handle_poll_answer(poll_answer):
    global last_poll_results

    poll_id = poll_answer.poll_id
    player_id = poll_answer.user.id
    option_ids = poll_answer.option_ids
    last_poll_results[player_id] = option_ids
