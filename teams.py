import random


def random_teamer(players, num_teams: int, consider_rating: bool = False) -> str:
    """
    Данная функция предлагает разбиение игроков по командам.
    :param players: словарь, где ключ это обозначение игрока: @player_name; значение: имя игрока
    :param num_teams: количество команд
    :param consider_rating: учитывать рейтинг при составлении команд
    :return: строка с составом команд
    """
    division = []
    s = ""
    if not consider_rating:
        avg_players_per_team = len(players) // num_teams
        remainder = len(players) % num_teams

        # Добавляем команды с средним количеством людей
        for i in range(num_teams - remainder):
            division.append(avg_players_per_team)

        # Добавляем команды со средним количеством людей + 1
        for i in range(remainder):
            division.append(avg_players_per_team + 1)

        for idx, d in enumerate(division):
            s += "Команда " + str(idx + 1) + ":\n"
            for player in range(d):
                random_player = random.choice(list(players.keys()))
                s += "\t- " + players[random_player] + "\n"
                del players[random_player]
    return s[:-1]
