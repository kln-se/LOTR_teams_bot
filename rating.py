import pandas as pd


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


def add_record(df, datetime, contributor_id, winners, game_map='-'):
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
