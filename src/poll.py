from datetime import datetime
from telebot.apihelper import ApiTelegramException
from src.access import check_white_list_decorator
from src.bot import get_bot_instance
from src.parse_config import get_players
from src.tag_players import start_tag_not_polled_players, unsubscribe_polled_player
from src.teams import choose_team_num
from src.storage import MemoryStorage

bot = get_bot_instance()


@bot.message_handler(commands=['start_poll'])
@check_white_list_decorator(bot_instance=bot)
def poll_handler(message):
    poll = bot.send_poll(
        chat_id=message.chat.id,
        question='Кто будет сегодня играть?',
        options=['☑️ Буду, как обычно в 22:00',
                 '🤔 Буду, но точное время пока не могу сказать',
                 '🕑 Предложу другое время (напишу ниже)',
                 '🤡 Пока не знаю, если будет настроение к 22:00',
                 '🙅‍♂️ Сегодня не смогу'],
        is_anonymous=False,
        allows_multiple_answers=False,
        close_date=datetime.combine(datetime.today().date(), datetime.min.time()),
        reply_to_message_id=message.id
    )
    MemoryStorage.polls_locations[poll.poll.id] = message.chat.id
    MemoryStorage.get_instance(message.chat.id).last_poll_results = {}
    MemoryStorage.get_instance(message.chat.id).not_polled_players = {}
    MemoryStorage.get_instance(message.chat.id).last_poll_id = poll.poll.id

    try:
        if MemoryStorage.get_instance(message.chat.id).last_poll_message_id:
            bot.unpin_chat_message(message.chat.id, MemoryStorage.get_instance(message.chat.id).last_poll_message_id)
        else:
            bot.unpin_all_chat_messages(message.chat.id)
        MemoryStorage.get_instance(message.chat.id).last_poll_message_id = poll.message_id
        bot.pin_chat_message(message.chat.id, poll.message_id)
    except ApiTelegramException as e:
        bot.send_message(chat_id=message.chat.id,
                         text='❗Запрос к Telegram API не удался.\n'
                              '\nВероятно, @LOTR_teams_bot не имеет достаточно прав '
                              'для управления закрепленными сообщениями в чате.')

    not_polled_players = {}
    for player_id in get_players():
        not_polled_players[str(player_id)] = True
    start_tag_not_polled_players(message, not_polled_players)


@bot.message_handler(commands=['no_clowns_poll'])
@check_white_list_decorator(bot_instance=bot)
def poll_handler(message):
    poll = bot.send_poll(
        chat_id=message.chat.id,
        question='Сегодня клоунов не будет))) Кто будет сегодня играть в ВК? Голосуют все!!!\n©Дмитро',
        options=['👍 Буду, если наберётся хотя бы 5 человек',
                 '👎 Не буду, но ниже напишу причину того, почему я пропускаю такие важные катки в ВК)'],
        is_anonymous=False,
        allows_multiple_answers=False,
        close_date=datetime.combine(datetime.today().date(), datetime.min.time()),
        reply_to_message_id=message.id
    )

    try:
        if MemoryStorage.get_instance(message.chat.id).last_poll_message_id:
            bot.unpin_chat_message(message.chat.id, MemoryStorage.get_instance(message.chat.id).last_poll_message_id)
        else:
            bot.unpin_all_chat_messages(message.chat.id)
        MemoryStorage.get_instance(message.chat.id).last_poll_message_id = poll.message_id
        bot.pin_chat_message(message.chat.id, poll.message_id)
    except ApiTelegramException as e:
        bot.send_message(chat_id=message.chat.id,
                         text='❗Запрос к Telegram API не удался.\n'
                              '\nВероятно, @LOTR_teams_bot не имеет достаточно прав '
                              'для управления закрепленными сообщениями в чате.')


@bot.poll_answer_handler()
def handle_poll_answer(poll_answer):
    poll_id = poll_answer.poll_id
    user_id = poll_answer.user.id
    option_ids = poll_answer.option_ids
    if option_ids:  # При изменении результата (Retract vote) option_ids = []
        chat_id = MemoryStorage.get_poll_location(poll_id)
        if chat_id:
            if user_id in get_players().keys():
                MemoryStorage.get_instance(chat_id).last_poll_results[user_id] = option_ids
                if poll_id == MemoryStorage.get_instance(chat_id).last_poll_id:
                    unsubscribe_polled_player(chat_id, poll_answer.user)
                else:
                    bot.send_message(chat_id=chat_id,
                                     text=f'❗@{poll_answer.user.username} проголосуйте в последнем опросе, '
                                          f'который закреплён в шапке чата!')
