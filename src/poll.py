from datetime import datetime
from src.access import check_white_list
from src.bot import get_bot
from src.teams import choose_team_num
from src.storage import MemoryStorage

bot = get_bot()


@bot.message_handler(commands=['start_poll'])
def poll_handler(message):
    if check_white_list(message.from_user.id):
        poll = bot.send_poll(
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
        MemoryStorage.polls_locations[poll.poll.id] = message.chat.id
        MemoryStorage.get_instance(message.chat.id).last_poll_results = {}


@bot.message_handler(commands=['no_clowns_poll'])
def poll_handler(message):
    if check_white_list(message.from_user.id):
        bot.send_poll(
            chat_id=message.chat.id,
            question='Сегодня клоунов не будет))) Кто будет сегодня играть в ВК? Голосуют все!!!',
            options=['👍 Буду, если наберётся хотя бы 5 человек',
                     '👎 Не буду, но ниже напишу причину того, почему я пропускаю такие важные катки в ВК)'],
            is_anonymous=False,
            allows_multiple_answers=False,
            close_date=datetime.combine(datetime.today().date(), datetime.min.time()),
            reply_to_message_id=message.id
        )


@bot.callback_query_handler(func=lambda call: call.data == 'last_poll_participants_btn')
def handle_last_poll_participants_btn(call):
    if MemoryStorage.get_instance(call.message.chat.id).last_poll_results:
        polled_players = {}
        for player_id in MemoryStorage.get_instance(call.message.chat.id).last_poll_results:
            if 0 in MemoryStorage.get_instance(call.message.chat.id).last_poll_results[player_id] or 1 in \
                    MemoryStorage.get_instance(call.message.chat.id).last_poll_results[player_id]:
                polled_players[player_id] = True

        bot.send_message(chat_id=call.message.chat.id,
                         text=f'Судя по опросу игроков будет: *{len(polled_players)}*',
                         parse_mode='Markdown')
        choose_team_num(call.message, polled_players)
    else:
        bot.send_message(chat_id=call.message.chat.id, text='Опросный лист пуст или никто не проголосвал "Буду...". Создайте новый опрос.')


@bot.poll_answer_handler()
def handle_poll_answer(poll_answer):
    poll_id = poll_answer.poll_id
    player_id = poll_answer.user.id
    option_ids = poll_answer.option_ids
    chat_id = MemoryStorage.get_poll_location(poll_id)
    MemoryStorage.get_instance(chat_id).last_poll_results[player_id] = option_ids
