import copy
import math
import random
from telebot import types
import src.choose_players  # Используется callback 'choose_players_btn'
from src.access import check_white_list
from src.bot import get_bot
from src.parse_config import get_players
from src.rating import load_df
from src.storage import MemoryStorage

bot = get_bot()


@bot.message_handler(commands=['propose_teams'])
def propose_teams_handler(message):
    if check_white_list(message.from_user.id):
        MemoryStorage.get_instance(message.chat.id).callback_func_ref = choose_team_num

        keyboard = types.InlineKeyboardMarkup()
        choose_players_btn = types.InlineKeyboardButton(text='Выбрать игроков', callback_data='choose_players_btn')
        last_poll_participants_btn = types.InlineKeyboardButton(text='Участники последнего опроса',
                                                                callback_data='last_poll_participants_btn')
        keyboard.add(choose_players_btn, last_poll_participants_btn)

        bot.send_message(chat_id=message.chat.id, text='Кто будет в командах?', reply_markup=keyboard)


@bot.callback_query_handler(func=lambda call: call.data in ['teams_2_btn', 'teams_3_btn', 'teams_4_btn'])
def handle_teams_x_btn(call):
    if call.data == 'teams_2_btn':
        MemoryStorage.get_instance(call.message.chat.id).teams_count = 2

    elif call.data == 'teams_3_btn':
        MemoryStorage.get_instance(call.message.chat.id).teams_count = 3

    elif call.data == 'teams_4_btn':
        MemoryStorage.get_instance(call.message.chat.id).teams_count = 4

    if MemoryStorage.get_instance(call.message.chat.id).teams_count and \
            MemoryStorage.get_instance(call.message.chat.id).teams_count > \
            sum(MemoryStorage.get_instance(call.message.chat.id).players_to_play.values()):
        bot.send_message(chat_id=call.message.chat.id,
                         text='Выбранное количество команд превышает количество игроков.')
    else:
        keyboard = types.InlineKeyboardMarkup()
        ignore_rating_btn = types.InlineKeyboardButton(text='Без учёта рейтинга', callback_data='ignore_rating_btn')
        consider_rating_btn = types.InlineKeyboardButton(text='С учётом рейтинга', callback_data='consider_rating_btn')
        keyboard.add(ignore_rating_btn, consider_rating_btn)

        bot.send_message(chat_id=call.message.chat.id,
                         text='Учитывать рейтинг игроков при составлении команд?',
                         reply_markup=keyboard)


@bot.callback_query_handler(func=lambda call: call.data in ['consider_rating_btn', 'ignore_rating_btn'])
def handle_consider_players_rating(call):
    if MemoryStorage.get_instance(call.message.chat.id).teams_count and \
            MemoryStorage.get_instance(call.message.chat.id).players_to_play:

        keyboard = types.InlineKeyboardMarkup()
        regen_teams_btn = types.InlineKeyboardButton(text='Пересоздать команды', callback_data='regen_teams_btn')
        keyboard.add(regen_teams_btn)

        if call.data == 'consider_rating_btn':
            MemoryStorage.get_instance(call.message.chat.id).consider_rating = True
            bot.send_message(chat_id=call.message.chat.id,
                             text=create_random_teams(
                                 MemoryStorage.get_instance(call.message.chat.id).players_to_play.copy(),
                                 MemoryStorage.get_instance(call.message.chat.id).teams_count,
                                 True),
                             reply_markup=keyboard,
                             parse_mode='Markdown')

        elif call.data == 'ignore_rating_btn':
            MemoryStorage.get_instance(call.message.chat.id).consider_rating = False
            bot.send_message(chat_id=call.message.chat.id,
                             text=create_random_teams(
                                 MemoryStorage.get_instance(call.message.chat.id).players_to_play.copy(),
                                 MemoryStorage.get_instance(call.message.chat.id).teams_count,
                                 False),
                             reply_markup=keyboard,
                             parse_mode='Markdown')
    else:
        bot.send_message(chat_id=call.message.chat.id,
                         text='Сначала необходимо выбрать игроков и количество команд')


@bot.callback_query_handler(func=lambda call: call.data == 'regen_teams_btn')
def handle_regen_teams_btn(call):
    if not MemoryStorage.get_instance(call.message.chat.id).teams_count or not sum(MemoryStorage.get_instance(
            call.message.chat.id).players_to_play.values()):
        bot.send_message(chat_id=call.message.chat.id,
                         text='Сначала необходимо выбрать игроков и количество команд')
    else:
        keyboard = types.InlineKeyboardMarkup()
        regen_teams_btn = types.InlineKeyboardButton(text='Пересоздать команды', callback_data='regen_teams_btn')
        keyboard.add(regen_teams_btn)
        bot.send_message(chat_id=call.message.chat.id,
                         text=create_random_teams(
                             MemoryStorage.get_instance(call.message.chat.id).players_to_play.copy(),
                             MemoryStorage.get_instance(call.message.chat.id).teams_count,
                             MemoryStorage.get_instance(call.message.chat.id).consider_rating),
                         reply_markup=keyboard,
                         parse_mode='Markdown')


def choose_team_num(message, chosen_players):
    MemoryStorage.get_instance(message.chat.id).teams_count = None
    MemoryStorage.get_instance(message.chat.id).players_to_play = chosen_players

    players_count = sum(chosen_players.values())

    if players_count < 2:
        bot.send_message(chat_id=message.chat.id,
                         text=f'Недостаточно игроков. '
                              f'Текущее количество выбранных игроков: *{players_count}* (необходимо 2 и более).',
                         parse_mode='Markdown')
    else:
        keyboard = types.InlineKeyboardMarkup()
        teams_2_btn = types.InlineKeyboardButton(text='2', callback_data='teams_2_btn')
        teams_3_btn = types.InlineKeyboardButton(text='3', callback_data='teams_3_btn')
        teams_4_btn = types.InlineKeyboardButton(text='4', callback_data='teams_4_btn')
        keyboard.add(teams_2_btn, teams_3_btn, teams_4_btn)

        bot.send_message(chat_id=message.chat.id,
                         text='Количество игроков: {0}. Сколько будет команд?'.format(players_count),
                         reply_markup=keyboard)


def create_random_teams(players_to_play, num_teams: int, consider_rating: bool = False) -> str:
    """
    Данная функция предлагает разбиение игроков по командам.
    :param players_to_play: Словарь, где ключ это обозначение игрока: player_id, а значение: True / False
    :param num_teams: Количество команд.
    :param consider_rating: Учитывать рейтинг при составлении команд.
    :return: Строка с составом команд.
    """

    def get_team_division():
        """
        Данная функция выполняет разделение количества игроков по командам.
        :return: Список с количеством игроков в командах.
        """
        num_players_per_team = []
        avg_players_per_team = sum(players_to_play.values()) // num_teams
        remainder = sum(players_to_play.values()) % num_teams
        # Добавляем команды со средним количеством людей
        for i in range(num_teams - remainder):
            num_players_per_team.append(avg_players_per_team)
        # Добавляем команды со средним количеством людей + 1
        for i in range(remainder):
            num_players_per_team.append(avg_players_per_team + 1)
        return num_players_per_team

    def get_random_teams(num_players_per_team):
        """
        Данная функция составляет список с вложенными списками из игроков в количестве, равном количеству команд.
        :return: Список, внутри которого лежат вложенные списки по количеству команд, содержащие player_id игроков.
        """
        random_teams = []
        for idx, players_count in enumerate(num_players_per_team):
            temp_team = []
            current_players_count = 0
            while current_players_count < players_count:
                random_player_id = random.choice(list(players_to_play.keys()))
                if players_to_play[random_player_id]:
                    temp_team.append(int(random_player_id))
                    del players_to_play[random_player_id]
                    current_players_count += 1
                else:
                    del players_to_play[random_player_id]
            random_teams.append(temp_team)
        return random_teams

    def get_players_power():
        """
        Данная функция составляет словарь, где ключ это player_id, а значение - количество его побед.
        :return: Словарь с количеством побед каждого игрока на текущий момент.
        """
        players_power = {}
        df = load_df('statistics_data/statistics.csv')
        for i in range(3, df.shape[1]):
            players_power[int(df.columns[i])] = df.iloc[-1, i]
        return players_power

    def print_result_rating_ignored(random_teams):
        """
        Данная функция составляет строку с итоговым разбиением по командам.
        Строка оформлена для случая, когда пользователь выбирает опцию "без учета рейтинга игроков".
        :return: Готовая строка для вывода в выбранном сообщении.
        """
        s = ""
        for idx, team in enumerate(random_teams):
            s += "Команда " + str(idx + 1) + ":\n"
            temp_team = []
            for player_id in team:
                temp_team.append(players[player_id][1])
            temp_team.sort()
            s += ''.join([f'\t- {player_name}\n' for player_name in temp_team])
        return s[:-1]

    def print_result_rating_considered(balanced_teams):
        """
        Данная функция составляет строку с итоговым разбиением по командам.
        Строка оформлена для случая, когда пользователь выбирает опцию "учитывать рейтинг игроков".
        :return: Готовая строка для вывода в выбранном сообщении.
        """
        teams_power = get_teams_power(balanced_teams)
        s = ""
        for idx, team in enumerate(balanced_teams):
            s += "Команда {0}: 🦾 *{1}*\n".format(str(idx + 1), teams_power[idx])
            temp_team = []
            for player_id in team:
                temp_team.append((players[player_id][1], players_power[player_id]))
            temp_team.sort()
            s += ''.join(
                ['\t- {0} 🏆 {1}\n'.format(player[0], player[1]) for player in temp_team])
        return s[:-1]

    def get_teams_power(current_teams):
        """
        Данная функция расчет силы каждой команды.
        :return: Список, содержащий значение силы каждой команды.
        """
        teams_power = []
        for team in current_teams:
            temp_team_power = 0
            for player_id in team:
                temp_team_power += players_power[player_id]
            teams_power.append(temp_team_power)
        return teams_power

    def simulated_annealing(random_teams):
        """
        Данная функция реализует алгоритм имитации отжига для формирования сбалансированных команд.
        :param random_teams: Случайное разбиение по командам с которых начинается работа алгоритма.
        :return: Список, внутри которого лежат вложенные списки по количеству команд, содержащие player_id игроков.
        """
        # Параметры алгоритма
        T = 1000  # Начальная температура
        T_min = 1  # Минимальная температура
        alpha = 0.9  # Коэффициент охлаждения
        max_iter = 1000  # Максимальное число итераций

        def get_teams_power_diff(current_teams_powers):
            """
            Данная функция вычисляет сумму модуля разниц в силе каждой команды между друг другом.
            :return: Сумма разниц в силе каждой команды между друг другом.
            """
            power_diff = 0
            for i in range(len(current_teams_powers)):
                for j in range(i + 1, len(current_teams_powers)):
                    power_diff += abs(current_teams_powers[i] - current_teams_powers[j])
            return power_diff

        # Вычисляем начальную разницу между силами команд
        teams_powers = get_teams_power(random_teams)
        teams_power_diff = get_teams_power_diff(teams_powers)

        # Генерируем новое решение (1 случайный игрок каждой команды переходит в другую команду)
        for i in range(max_iter):
            new_teams = copy.deepcopy(random_teams)
            # Из каждой команды вынимаем по случайному игроку
            players_for_transfer = []
            for team in new_teams:
                players_for_transfer.append(team.pop(random.randint(0, len(team) - 1)))
            # Перемещаем игроков в соседние команды, если 3 команды: 1->2, 2->3, 3->1
            N = len(new_teams)
            for j in range(N):
                new_teams[(j + 1) % N].append(players_for_transfer[j])

            new_teams_powers = get_teams_power(new_teams)
            new_teams_power_diff = get_teams_power_diff(new_teams_powers)

            # Если новое решение лучше, то принимаем его
            if new_teams_power_diff < teams_power_diff:
                random_teams = new_teams
                teams_power_diff = new_teams_power_diff
            # Если новое решение хуже, то может быть принято с некоторой вероятностью
            else:
                p = math.exp(-1 * (new_teams_power_diff - teams_power_diff) / T)
                cp = random.uniform(0, 1)
                if cp < p:
                    random_teams = new_teams
                    teams_power_diff = new_teams_power_diff

            # Понижаем температуру
            T = alpha * T
            # Выход из цикла, если температура достигла минимального значения
            if T < T_min:
                break

        return random_teams

    players = get_players()
    players_power = get_players_power()
    division = get_team_division()
    teams = get_random_teams(division)

    if consider_rating:
        teams = simulated_annealing(teams)
        result = print_result_rating_considered(teams)
    else:
        result = print_result_rating_ignored(teams)
    return result
