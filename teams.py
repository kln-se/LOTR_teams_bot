import random


def create_random_teams(players, num_teams: int, consider_rating: bool = False) -> str:
    """
    Данная функция предлагает разбиение игроков по командам.
    :param players: Словарь, где ключ это обозначение игрока: @player_name; значение: имя игрока
    :param num_teams: Количество команд.
    :param consider_rating: Учитывать рейтинг при составлении команд.
    :return: Строка с составом команд.
    """
    division = []
    s = ""
    if not consider_rating:
        avg_players_per_team = len(players) // num_teams
        remainder = len(players) % num_teams

        # Добавляем команды со средним количеством людей
        for i in range(num_teams - remainder):
            division.append(avg_players_per_team)

        # Добавляем команды со средним количеством людей + 1
        for i in range(remainder):
            division.append(avg_players_per_team + 1)

        for idx, d in enumerate(division):
            s += "Команда " + str(idx + 1) + ":\n"
            temp_team = []
            for player in range(d):
                random_player_id = random.choice(list(players.keys()))
                temp_team.append(players[random_player_id])
                del players[random_player_id]
            temp_team.sort()
            s += ''.join([f'\t- {player_name}\n' for player_name in temp_team])
    return s[:-1]
