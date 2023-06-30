import datetime
import schedule
import threading
import time
from telebot import types
import src.choose_players  # Используется callback 'choose_players_btn'
from src.poll import handle_last_poll_participants_btn  # Используется callback 'last_poll_participants_btn'
from src.access import check_white_list_decorator, check_admin_list_decorator
from src.bot import get_bot_instance
from src.parse_config import get_players
from src.storage import MemoryStorage

bot = get_bot_instance()
lock = threading.Lock()


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
                                                            callback_data='last_poll_participants_btn')
    keyboard.add(choose_players_btn, last_poll_participants_btn)

    bot.send_message(chat_id=message.chat.id, text='Кто будет в командах?', reply_markup=keyboard)


@bot.message_handler(commands=['stop_all_notifications'])
@check_admin_list_decorator(bot_instance=bot)
def stop_all_notifications_handler(message):
    if MemoryStorage.get_instance(message.chat.id).notification_thread \
            and MemoryStorage.get_instance(message.chat.id).notification_thread.is_alive():
        stop_thread(message)

        with lock:
            MemoryStorage.get_instance(message.chat.id).subscribed_players = {}
            MemoryStorage.get_instance(message.chat.id).not_polled_players = {}
            MemoryStorage.get_instance(message.chat.id).ready_to_play_players = {}

        bot.reply_to(message, f'🔕 Рассылка уведомлений игрокам остановлена.'
                              f'\n❗️Поток рассылки уведомлений для данного чата остановлен:'
                              f'\n\t- Активных задач schedule всего: {len(schedule.jobs)}'
                              f'\n\t- Активных потоков threads всего: {threading.active_count()}')
    else:
        bot.reply_to(message, '❗️Поток рассылки уведомлений не запущен.')


@bot.callback_query_handler(func=lambda call: call.data == 'unsubscribe_btn')
def handle_unsubscribe_btn(call):
    unsubscribe_player(call)


def start_tag_players(call, chosen_players):
    with lock:
        MemoryStorage.get_instance(call.message.chat.id).subscribed_players = chosen_players

    # Удалить задачу в schedule
    if 'tag_players_job' in MemoryStorage.get_instance(call.message.chat.id).jobs_id.keys():
        schedule.cancel_job(MemoryStorage.get_instance(call.message.chat.id).jobs_id.pop('tag_players_job'))
    # Создать задачу в schedule
    with lock:
        MemoryStorage.get_instance(call.message.chat.id).jobs_id['tag_players_job'] = \
            schedule.every(20).seconds.do(send_notification,
                                          call,
                                          header='🔔 Собираемся в Discord! Вы где?',
                                          show_unsubscribe_btn=True,
                                          players_to_notify=MemoryStorage.get_instance(
                                              call.message.chat.id).subscribed_players
                                          ).until("23:59")
    # Если поток ещё не создавался
    if not MemoryStorage.get_instance(call.message.chat.id).notification_thread \
            or not MemoryStorage.get_instance(call.message.chat.id).notification_thread.is_alive():
        MemoryStorage.get_instance(call.message.chat.id).stop_event = threading.Event()
        MemoryStorage.get_instance(call.message.chat.id).notification_thread = threading.Thread(target=worker,
                                                                                                args=(call.message,),
                                                                                                name='tag-players-thr',
                                                                                                daemon=True)
        MemoryStorage.get_instance(call.message.chat.id).notification_thread.start()

    bot.send_message(chat_id=call.message.chat.id,
                     text=create_prompt(MemoryStorage.get_instance(call.message.chat.id).subscribed_players,
                                        f'\n❕@{call.from_user.username} инициирует автоматическое оповещение '
                                        f'выбранных игроков каждые 60 секунд.\n'
                                        f'\nСледующие игроки добавлены в список уведомлений:')
                     )


def send_notification(call, players_to_notify, header, show_unsubscribe_btn=False):
    with lock:
        if show_unsubscribe_btn:
            keyboard = types.InlineKeyboardMarkup()
            unsubscribe_btn = types.InlineKeyboardButton(text='Отписаться', callback_data='unsubscribe_btn')
            keyboard.add(unsubscribe_btn)

            bot.send_message(chat_id=call.message.chat.id,
                             text=create_prompt(players_to_notify, header),
                             reply_markup=keyboard)
        else:
            bot.send_message(chat_id=call.message.chat.id,
                             text=create_prompt(players_to_notify, header))


def create_prompt(players_to_notify, header):
    players = get_players()
    s = header
    for player_id in players_to_notify:
        if players_to_notify[player_id]:
            s += f'\n\t- {players[int(player_id)][0]}'
    return s


def worker(message):
    while not MemoryStorage.get_instance(message.chat.id).stop_event.is_set():
        # Если список рассылки subscribed_players пуст
        with lock:
            subscribed_players_values_sum = sum(MemoryStorage.get_instance(message.chat.id).subscribed_players.values())
        if not subscribed_players_values_sum:
            if 'tag_players_job' in MemoryStorage.get_instance(message.chat.id).jobs_id.keys():
                schedule.cancel_job(MemoryStorage.get_instance(message.chat.id).jobs_id.pop('tag_players_job'))
                bot.send_message(chat_id=message.chat.id,
                                 text='🔕 Задача рассылки уведомлений выбранным игрокам для данного чата завершена.\n'
                                      '\nТекущий список рассылки пуст.')
        # Если более нет активных задач
        if not MemoryStorage.get_instance(message.chat.id).jobs_id:
            MemoryStorage.get_instance(message.chat.id).stop_event.set()
            bot.send_message(chat_id=message.chat.id,
                             text=f'❗Поток рассылки уведомлений для данного чата остановлен.\n'
                                  f'\nКоличество активных задач рассылки уведомлений для данного чата: '
                                  f'*{len(MemoryStorage.get_instance(message.chat.id).jobs_id)}*',
                             parse_mode='Markdown')
        schedule.run_pending()
        time.sleep(1)


def unsubscribe_player(call):
    with lock:
        if str(call.from_user.id) in MemoryStorage.get_instance(call.message.chat.id).subscribed_players.keys() and \
                MemoryStorage.get_instance(call.message.chat.id).subscribed_players[str(call.from_user.id)]:
            with threading.Lock():
                MemoryStorage.get_instance(call.message.chat.id).subscribed_players[str(call.from_user.id)] = False
            bot.send_message(chat_id=call.message.chat.id,
                             text=f'❕Игрок @{call.from_user.username} отписался от уведомлений.')
        else:
            bot.send_message(chat_id=call.message.chat.id,
                             text=f'❕Игрок @{call.from_user.username} не находится в текущем списке рассылки уведомлений.')


def stop_thread(message):
    MemoryStorage.get_instance(message.chat.id).stop_event.set()
    # Удалить задачи в schedule
    for job_name in list(MemoryStorage.get_instance(message.chat.id).jobs_id.keys()):
        schedule.cancel_job(MemoryStorage.get_instance(message.chat.id).jobs_id.pop(job_name))
    MemoryStorage.get_instance(message.chat.id).notification_thread.join()  # Дождаться завершения потока
    MemoryStorage.get_instance(message.chat.id).notification_thread = None
    MemoryStorage.get_instance(message.chat.id).stop_event = None