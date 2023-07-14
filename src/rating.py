import datetime as dt
import pandas as pd
from src.access import check_white_list_decorator, check_admin_list_decorator
from src.bot import get_bot_instance
from src.choose_players import choose_winners
from src.parse_config import get_players
from src.plots import plot_statistics
from src.storage import MemoryStorage

bot = get_bot_instance()


@bot.message_handler(commands=['rating'])
@check_white_list_decorator(bot_instance=bot)
def rating_handler(message):
    plot_statistics(load_df('statistics_data/statistics.csv'), get_players())
    with open('statistics_data/statistics.png', 'rb') as photo:
        bot.send_photo(message.chat.id, photo)


@bot.message_handler(commands=['add_record'])
@check_white_list_decorator(bot_instance=bot)
def add_record_handler(message):
    MemoryStorage.get_instance(message.chat.id).callback_func_ref = add_record
    choose_winners(message)


@bot.message_handler(commands=['delete_record'])
@check_admin_list_decorator(bot_instance=bot)
def delete_last_record_handler(message):
    delete_last_record(message)


def create_df(players):
    """Создает pandas dataframe"""
    # Заголовки df
    headers = ["datetime", "contributor_id"]
    for player_id in players:
        headers.append(str(player_id))

    return pd.DataFrame(columns=headers)


def save_df(df, path):
    """Сохраняет df в файл *.csv"""
    df.to_csv(path_or_buf=path, index=False)


def load_df(path):
    """Загружает df из файла *.csv"""
    df = pd.read_csv(filepath_or_buffer=path)
    df['datetime'] = pd.to_datetime(df['datetime'], dayfirst=True, format='%Y-%m-%d %H:%M:%S.%f')
    complex_cols = df.columns[2:]
    df[complex_cols] = df[complex_cols].astype(complex)
    return df


def add_record(call, chosen_players):
    if chosen_players and sum([True for players_id in chosen_players if chosen_players[players_id] is not None]):
        bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.id)
        df = load_df('statistics_data/statistics.csv')
        create_record(df, dt.datetime.now(), call.from_user.id, chosen_players)
        save_df(df, 'statistics_data/statistics.csv')
        MemoryStorage.get_instance(call.message.chat.id).chosen_players = {}
        bot.send_message(chat_id=call.message.chat.id, text='❕Запись добавлена, список выбранных игроков очищен.')
    else:
        bot.send_message(chat_id=call.message.chat.id,
                         text='❗Выберите победителей и проигравших, текущий список пуст.')


def delete_last_record(message):
    df = load_df('statistics_data/statistics.csv')
    if len(df):
        series_to_delete = df.iloc[-1]
        df = df.drop(index=df.index[-1])
        save_df(df, 'statistics_data/statistics.csv')
        if message.from_user.username:
            bot.send_message(chat_id=message.chat.id,
                             text='❕@{0} удалил запись добавленную пользователем с id={1} в {2}.'.format(
                                 message.from_user.username, series_to_delete[1], series_to_delete[0]))
        else:
            bot.send_message(chat_id=message.chat.id,
                             text='❕{0} удалил запись добавленную пользователем с id={1} в {2}.'.format(
                                 message.from_user.id, series_to_delete[1], series_to_delete[0]))
    else:
        bot.send_message(chat_id=message.chat.id, text='❗Статистика не содержит записей.')


def create_record(df, datetime, contributor_id, winners):
    """
    Добавить запись в df. Результат игры для игрока представлен в виде комплексного числа w + l * j,
    где w - выиграл, а l - проиграл. Если игрок победил, то 1+0j, если проиграл - 0+1j, если не участвовал в
    текущей игре - 0+0j
    :param df: Объект pandas dataframe, содержащий таблицу со статистикой игр.
    :param datetime: Дата и время добавления новой записи в статистику.
    :param contributor_id: Telegram id пользователя, добавляющего новую запись в статистику.
    :param winners: Словарь, где ключи это Telegram id игроков, а значения: True - выиграл в игре, False - проиграл,
    None - не участвовал в текущей игре.
    """
    temp_record = {
        "datetime": datetime,
        "contributor_id": contributor_id
    }
    for player_id in winners:
        if winners[player_id] is None:
            temp_record[str(player_id)] = 0 + 0j
        elif winners[player_id]:
            temp_record[str(player_id)] = 1 + 0j
        else:
            temp_record[str(player_id)] = 0 + 1j

    df.loc[len(df)] = temp_record
