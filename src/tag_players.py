import datetime
import schedule
import threading
import time
from telebot import types
from telebot.apihelper import ApiTelegramException
import src.choose_players  # Используется callback 'choose_players_btn', callback 'choose_last_poll_participants_btn'
from src.access import check_white_list_decorator, check_admin_list_decorator
from src.bot import get_bot_instance
from src.parse_config import get_players
from src.storage import MemoryStorage

bot = get_bot_instance()
schedule_lock = threading.Lock()


@bot.message_handler(commands=['active_threads'])
@check_admin_list_decorator(bot_instance=bot)
def active_threads_handler(message):
    bot.send_message(chat_id=message.chat.id,
                     text='\n'.join([f'{idx + 1} {str(t)}' for idx, t in enumerate(threading.enumerate())]))


@bot.message_handler(commands=['active_jobs'])
@check_admin_list_decorator(bot_instance=bot)
def active_jobs_handler(message):
    if schedule.jobs:
        bot.send_message(chat_id=message.chat.id,
                         text='\n'.join([f'{idx + 1} {str(j)}' for idx, j in enumerate(schedule.jobs)]))
    else:
        bot.send_message(chat_id=message.chat.id,
                         text=len(schedule.jobs))


@bot.message_handler(commands=['tag_players'])
@check_white_list_decorator(bot_instance=bot)
def tag_players_handler(message):
    MemoryStorage.get_instance(message.chat.id).callback_func_ref = start_tag_players

    keyboard = types.InlineKeyboardMarkup()
    choose_players_btn = types.InlineKeyboardButton(text='Выбрать игроков', callback_data='choose_players_btn')
    last_poll_participants_btn = types.InlineKeyboardButton(text='Участники последнего опроса',
                                                            callback_data='choose_last_poll_participants_btn')
    keyboard.add(choose_players_btn, last_poll_participants_btn)

    bot.send_message(chat_id=message.chat.id, text='Кого добавить в список рассылки уведомлений?',
                     reply_markup=keyboard)


@bot.message_handler(commands=['stop_all_notifications'])
@check_admin_list_decorator(bot_instance=bot)
def stop_all_notifications_handler(message):
    chat_inst = MemoryStorage.get_instance(message.chat.id)
    if chat_inst.notification_thread and chat_inst.notification_thread.is_alive():
        stop_thread(message)

        with chat_inst.lock:
            chat_inst.subscribed_players = {}
            chat_inst.not_polled_players = {}

        bot.reply_to(message, f'🔕 Рассылка уведомлений игрокам остановлена.'
                              f'\n❗️Поток рассылки уведомлений для данного чата остановлен.\n'
                              f'\nТекущее состояние:'
                              f'\n\t- Активных задач schedule всего: {len(schedule.jobs)}'
                              f'\n\t- Активных потоков threads всего: {threading.active_count()}')
    else:
        bot.reply_to(message, '❗️Поток рассылки уведомлений не запущен.')


@bot.callback_query_handler(func=lambda call: call.data == 'unsubscribe_btn')
def handle_unsubscribe_btn(call):
    unsubscribe_player(call)


def start_tag_players(call, chosen_players):
    chat_inst = MemoryStorage.get_instance(call.message.chat.id)
    if chosen_players:
        with chat_inst.lock:
            chat_inst.subscribed_players = chosen_players

            # Удалить задачу в schedule
            if 'tag_players_job' in chat_inst.started_jobs:
                schedule.cancel_job(chat_inst.started_jobs.pop('tag_players_job'))

            # Создать задачу в schedule
            if datetime.datetime.now().time() < datetime.time(23, 59, 59):
                chat_inst.started_jobs['tag_players_job'] = \
                    schedule.every(60).seconds.do(send_notification,
                                                  call.message,
                                                  players_to_notify=chat_inst.subscribed_players,
                                                  header='🔔 Собираемся в Discord! Вы где?\n\nСписок рассылки:',
                                                  last_notification_msg_id=[chat_inst.tag_players_msg_id],
                                                  show_unsubscribe_btn=True).until("23:59:59")

        # Если поток ещё не создавался или завершён
        if not chat_inst.notification_thread or not chat_inst.notification_thread.is_alive():
            chat_inst.stop_event = threading.Event()
            chat_inst.notification_thread = threading.Thread(target=worker,
                                                             args=(call.message,),
                                                             name=f'PlayersNotificationThread:{call.message.chat.id}',
                                                             daemon=True)
            chat_inst.notification_thread.start()

        bot.send_message(chat_id=call.message.chat.id,
                         text=create_prompt(chat_inst.subscribed_players,
                                            f'\n❕@{call.from_user.username} инициирует автоматическое оповещение '
                                            f'выбранных игроков каждые 60 секунд.\n'
                                            f'\nСледующие игроки добавлены в список уведомлений:')
                         )
    else:
        bot.send_message(chat_id=call.message.chat.id, text='❗Выберите игроков, текущий список пуст.')


def start_tag_not_polled_players(message, not_polled_players):
    chat_inst = MemoryStorage.get_instance(message.chat.id)
    with chat_inst.lock:
        chat_inst.not_polled_players = not_polled_players

        # Удалить задачу в schedule
        if 'tag_not_polled_players_job' in chat_inst.started_jobs:
            schedule.cancel_job(chat_inst.started_jobs.pop('tag_not_polled_players_job'))

        # Создать задачу в schedule
        # Бот инициирует автоматическое оповещение не проголосовавших игроков каждые 15 минут
        if datetime.datetime.now().time() < datetime.time(22, 30, 00):
            chat_inst.started_jobs['tag_not_polled_players_job'] = \
                schedule.every(15).minutes.do(send_notification,
                                              message,
                                              players_to_notify=chat_inst.not_polled_players,
                                              header='🔔 Проголосуйте в закреплённом опросе!\n\nСписок рассылки:',
                                              last_notification_msg_id=[chat_inst.not_polled_players_msg_id],
                                              show_unsubscribe_btn=False).until("22:30:00")

    # Если поток ещё не создавался или завершён
    if not chat_inst.notification_thread or not chat_inst.notification_thread.is_alive():
        chat_inst.stop_event = threading.Event()
        chat_inst.notification_thread = threading.Thread(target=worker,
                                                         args=(message,),
                                                         name=f'PlayersNotificationThread:{message.chat.id}',
                                                         daemon=True)
        chat_inst.notification_thread.start()


def send_notification(message, players_to_notify, header, last_notification_msg_id, show_unsubscribe_btn=False):
    # Если уведомление было отправлено, то необходимо удалить из чата старое сообщение и отправить новое
    if last_notification_msg_id[0]:
        try:
            bot.delete_message(chat_id=message.chat.id, message_id=last_notification_msg_id)
        except ApiTelegramException:
            pass

    if show_unsubscribe_btn:
        keyboard = types.InlineKeyboardMarkup()
        unsubscribe_btn = types.InlineKeyboardButton(text='Отписаться', callback_data='unsubscribe_btn')
        keyboard.add(unsubscribe_btn)
        t_info = threading.current_thread()
        notification_msg = bot.send_message(chat_id=message.chat.id,
                                            text=create_prompt(players_to_notify, header),
                                            reply_markup=keyboard)
    else:
        notification_msg = bot.send_message(chat_id=message.chat.id,
                                            text=create_prompt(players_to_notify, header))
    # Эмуляция указателя на переменную через изменяемый объект list
    last_notification_msg_id[0] = notification_msg.message_id


def create_prompt(players_to_notify, header):
    players = get_players()
    s = header
    for player_id in players_to_notify:
        if players_to_notify[player_id]:
            s += f'\n\t- {players[int(player_id)][0]}'
    return s


def worker(message):
    chat_inst = MemoryStorage.get_instance(message.chat.id)
    while not chat_inst.stop_event.is_set():
        with chat_inst.lock:
            # Если список рассылки subscribed_players пуст, а задача в started_jobs есть
            if not sum(chat_inst.subscribed_players.values()) and 'tag_players_job' in chat_inst.started_jobs:

                schedule.cancel_job(chat_inst.started_jobs.pop('tag_players_job'))
                bot.send_message(chat_id=message.chat.id,
                                 text='🔕 Задача рассылки уведомлений выбранным игрокам завершена.')

            # Если задача завершилась по timeout (условие .until()) и в schedule.jobs её нет
            elif 'tag_players_job' in chat_inst.started_jobs and \
                    chat_inst.started_jobs['tag_players_job'] not in schedule.jobs:

                chat_inst.subscribed_players = {}
                del chat_inst.started_jobs['tag_players_job']

                bot.send_message(chat_id=message.chat.id,
                                 text='🔕 Задача рассылки уведомлений выбранным игрокам завершена (timeout).')

            # Если список рассылки not_polled_players пуст, а задача в started_jobs есть
            if not sum(chat_inst.not_polled_players.values()) and \
                    'tag_not_polled_players_job' in chat_inst.started_jobs:

                schedule.cancel_job(chat_inst.started_jobs.pop('tag_not_polled_players_job'))
                bot.send_message(chat_id=message.chat.id,
                                 text='🔕 Задача рассылки уведомлений не проголосовавшим игрокам завершена.')

            # Если задача завершилась по timeout (условие .until()) и в schedule.jobs её нет
            elif 'tag_not_polled_players_job' in chat_inst.started_jobs and \
                    chat_inst.started_jobs['tag_not_polled_players_job'] not in schedule.jobs:

                chat_inst.not_polled_players = {}
                del chat_inst.started_jobs['tag_not_polled_players_job']

                bot.send_message(chat_id=message.chat.id,
                                 text='🔕 Задача рассылки уведомлений не проголосовавшим игрокам завершена (timeout).')

            # Если более нет активных задач
            if not chat_inst.started_jobs:
                chat_inst.stop_event.set()

        with schedule_lock:
            schedule.run_pending()
        time.sleep(1)


def unsubscribe_player(call):
    chat_inst = MemoryStorage.get_instance(call.message.chat.id)
    with chat_inst.lock:
        if 'tag_players_job' not in chat_inst.started_jobs:
            bot.send_message(chat_id=call.message.chat.id,
                             text=f'❗@{call.from_user.username}, список рассылки пуст. Задача рассылки уведомлений '
                                  f'выбранным игрокам завершена или не создана.')
        elif str(call.from_user.id) in chat_inst.subscribed_players and \
                chat_inst.subscribed_players[str(call.from_user.id)]:
            chat_inst.subscribed_players[str(call.from_user.id)] = False
            bot.send_message(chat_id=call.message.chat.id,
                             text=f'❕Игрок @{call.from_user.username} отписался от уведомлений.')

        else:
            bot.send_message(chat_id=call.message.chat.id,
                             text=f'❕Игрок @{call.from_user.username} не находится в текущем списке '
                                  f'рассылки уведомлений.')


def unsubscribe_polled_player(chat_id, user):
    chat_inst = MemoryStorage.get_instance(chat_id)
    with chat_inst.lock:
        if 'tag_not_polled_players_job' not in chat_inst.started_jobs:
            pass
        elif not chat_inst.not_polled_players[str(user.id)]:
            bot.send_message(chat_id=chat_id,
                             text=f'❕Игрок {get_players()[user.id][0]} изменил своё решение в опросе.')
        else:
            chat_inst.not_polled_players[str(user.id)] = False
            bot.send_message(chat_id=chat_id,
                             text=f'❕Игрок {get_players()[user.id][0]} проголосовал в опросе.')


# Если игрок отозвал голос
def subscribe_retracted_player(chat_id, user):
    chat_inst = MemoryStorage.get_instance(chat_id)
    with chat_inst.lock:
        if 'tag_not_polled_players_job' in chat_inst.started_jobs:
            chat_inst.not_polled_players[str(user.id)] = True
            bot.send_message(chat_id=chat_id,
                             text=f'❕Игрок {get_players()[user.id][0]} отозвал голос.')


def stop_thread(message):
    chat_inst = MemoryStorage.get_instance(message.chat.id)
    chat_inst.stop_event.set()
    with chat_inst.lock:
        # Удалить задачи в schedule
        for job_name in list(chat_inst.started_jobs.keys()):
            schedule.cancel_job(chat_inst.started_jobs.pop(job_name))

    chat_inst.notification_thread.join()  # Дождаться завершения потока
    chat_inst.notification_thread = None
    chat_inst.stop_event = None
