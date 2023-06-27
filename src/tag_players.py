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
    schedule.clear()
    if MemoryStorage.get_instance(message.chat.id).stop_event:
        MemoryStorage.get_instance(message.chat.id).stop_event.set()
        MemoryStorage.get_instance(message.chat.id).notification_thread.join()  # Дождаться завершения потока
        MemoryStorage.get_instance(message.chat.id).notification_thread = None
        MemoryStorage.get_instance(message.chat.id).stop_event = None
        bot.reply_to(message, f'\nРассылка уведомлений игрокам остановлена:'
                              f'\n - Активных задач schedule: {len(schedule.jobs)}'
                              f'\n - Активных потоков threads: {threading.active_count()}')
    else:
        bot.reply_to(message, 'Поток рассылки уведомлений не запущен')


@bot.callback_query_handler(func=lambda call: call.data == 'unsubscribe_btn')
def handle_unsubscribe_btn(call):
    unsubscribe_player(call)


def start_tag_players(call, chosen_players):
    MemoryStorage.get_instance(call.message.chat.id).subscribed_players = chosen_players

    # Удалить задачу в schedule
    if 'tag_players_job' in MemoryStorage.get_instance(call.message.chat.id).jobs_id.keys():
        schedule.cancel_job(MemoryStorage.get_instance(call.message.chat.id).jobs_id.pop('tag_players_job'))
    # Создать задачу в schedule
    MemoryStorage.get_instance(call.message.chat.id).jobs_id['tag_players_job'] = \
        schedule.every(60).seconds.do(send_notification,
                                      call,
                                      header='Собираемся в Discord! Вы где?',
                                      show_unsubscribe_btn=True,
                                      players_to_notify=MemoryStorage.get_instance(
                                          call.message.chat.id).subscribed_players
                                      ).until("23:59")
    # Остановить поток если он существует
    if MemoryStorage.get_instance(call.message.chat.id).stop_event:
        MemoryStorage.get_instance(call.message.chat.id).stop_event.set()
        MemoryStorage.get_instance(call.message.chat.id).notification_thread.join()  # Дождаться завершения потока
        MemoryStorage.get_instance(call.message.chat.id).notification_thread = None
    else:
        MemoryStorage.get_instance(call.message.chat.id).stop_event = threading.Event()
    # Запустить поток
    MemoryStorage.get_instance(call.message.chat.id).stop_event.clear()
    MemoryStorage.get_instance(call.message.chat.id).notification_thread = threading.Thread(target=worker,
                                                                                            args=(call.message,),
                                                                                            name='tag-players-thr',
                                                                                            daemon=True)
    MemoryStorage.get_instance(call.message.chat.id).notification_thread.start()

    bot.send_message(chat_id=call.message.chat.id,
                     text=create_prompt(MemoryStorage.get_instance(call.message.chat.id).subscribed_players,
                                        f'\n@{call.from_user.username} инициирует автоматическое оповещение '
                                        f'выбранных игроков каждые 60 секунд.'
                                        f'\nСледующие игроки добавлены в список уведомлений:')
                     )


def send_notification(call, players_to_notify, header, show_unsubscribe_btn=False):
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
    with threading.Lock():
        for player_id in players_to_notify:
            if players_to_notify[player_id]:
                s += f'\n{players[int(player_id)][0]}'
    return s


def worker(message):
    while not MemoryStorage.get_instance(message.chat.id).stop_event.is_set():
        # Если список рассылки subscribed_players пуст
        if not sum(MemoryStorage.get_instance(message.chat.id).subscribed_players.values()):
            if 'tag_players_job' in MemoryStorage.get_instance(message.chat.id).jobs_id.keys():
                schedule.cancel_job(MemoryStorage.get_instance(message.chat.id).jobs_id.pop('tag_players_job'))
                bot.send_message(chat_id=message.chat.id,
                                 text='Текущий список рассылки пуст. '
                                      'Задача рассылки уведомлений выбранным игрокам завершена')
        # Если более нет активных задач
        if not schedule.jobs:
            MemoryStorage.get_instance(message.chat.id).stop_event.set()
            bot.send_message(chat_id=message.chat.id,
                             text=f'Количество активных задач рассылки уведомлений: *{len(schedule.jobs)}*. '
                                  f'Поток рассылки уведомлений остановлен',
                             parse_mode='Markdown')
        schedule.run_pending()
        time.sleep(1)


def unsubscribe_player(call):
    if str(call.from_user.id) in MemoryStorage.get_instance(call.message.chat.id).subscribed_players.keys() and \
            MemoryStorage.get_instance(call.message.chat.id).subscribed_players[str(call.from_user.id)]:
        with threading.Lock():
            MemoryStorage.get_instance(call.message.chat.id).subscribed_players[str(call.from_user.id)] = False
        bot.send_message(chat_id=call.message.chat.id,
                         text=f'Игрок @{call.from_user.username} отписался от уведомлений.')
    else:
        bot.send_message(chat_id=call.message.chat.id,
                         text=f'Игрок @{call.from_user.username} не находится в текущем списке рассылки уведомлений')
