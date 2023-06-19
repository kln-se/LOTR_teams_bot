import datetime as dt
import pandas as pd
from src.access import check_white_list, check_admin_list
from src.bot import get_bot
from src.choose_players import choose_players
from src.parse_config import get_players
from src.plots import plot_statistics
from src.storage import MemoryStorage

bot = get_bot()


@bot.message_handler(commands=['rating'])
def rating_handler(message):
    if check_white_list(message.from_user.id):
        plot_statistics(load_df('statistics_data/statistics.csv'), get_players())
        with open('statistics_data/statistics.png', 'rb') as photo:
            bot.send_photo(message.chat.id, photo)


@bot.message_handler(commands=['add_record'])
def add_record_handler(message):
    if check_white_list(message.from_user.id):
        MemoryStorage.get_instance(message.chat.id).callback_func_ref = add_record
        choose_players(message)


@bot.message_handler(commands=['delete_record'])
def delete_last_record_handler(message):
    if check_admin_list(message.from_user.id):
        delete_last_record(message)


def create_df(players):
    """Создает pandas dataframe"""
    # Заголовки df
    headers = ["datetime", "contributor_id", "map"]
    for tg_id in players:
        headers.append(str(tg_id))

    return pd.DataFrame(columns=headers)


def save_df(df, path):
    """Сохраняет df в файл *.csv"""
    df.to_csv(path_or_buf=path, index=False)


def load_df(path):
    """Загружает df из файла *.csv"""
    df = pd.read_csv(filepath_or_buffer=path)
    df['datetime'] = pd.to_datetime(df['datetime'], dayfirst=True, format='%Y-%m-%d %H:%M:%S.%f')
    int_cols = df.columns[3:]
    df[int_cols] = df[int_cols].astype(int)
    return df


def add_record(message, chosen_players):
    if chosen_players:
        df = load_df('statistics_data/statistics.csv')
        create_record(df, dt.datetime.now(), message.from_user.id, chosen_players)
        save_df(df, 'statistics_data/statistics.csv')
        MemoryStorage.get_instance(message.chat.id).chosen_players = {}
        bot.send_message(chat_id=message.chat.id, text='Запись добавлена, список выбранных игроков очищен.')
    else:
        bot.send_message(chat_id=message.chat.id, text='Выберите победителей, текущий список пуст.')


def delete_last_record(message):
    df = load_df('statistics_data/statistics.csv')
    if len(df):
        series_to_delete = df.iloc[-1]
        df = df.drop(index=df.index[-1])
        save_df(df, 'statistics_data/statistics.csv')
        if message.from_user.username:
            bot.send_message(chat_id=message.chat.id,
                             text='@{0} удалил запись добавленную пользователем с id={1} в {2}.'.format(
                                 message.from_user.username, series_to_delete[1], series_to_delete[0]))
        else:
            bot.send_message(chat_id=message.chat.id,
                             text='{0} удалил запись добавленную пользователем с id={1} в {2}.'.format(
                                 message.from_user.id, series_to_delete[1], series_to_delete[0]))
    else:
        bot.send_message(chat_id=message.chat.id, text='Статистика не содержит записей.')


def create_record(df, datetime, contributor_id, winners, game_map='-'):
    """Добавить запись в df"""
    temp_record = {
        "datetime": datetime,
        "contributor_id": contributor_id,
        "map": game_map
    }
    # Самая первая запись в df
    if len(df) == 0:
        for t_id in winners:
            if winners[t_id]:
                temp_record[str(t_id)] = 1
            else:
                temp_record[str(t_id)] = 0
    # Новая запись в df
    else:
        for t_id in winners:
            if winners[t_id]:
                temp_record[str(t_id)] = df.iloc[-1][str(t_id)] + 1
            else:
                temp_record[str(t_id)] = df.iloc[-1][str(t_id)]

    df.loc[len(df)] = temp_record
