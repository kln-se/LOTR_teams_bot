from configparser import ConfigParser

config = ConfigParser()
config.read('config.ini')

token = config.get('CONNECTION', 'token')
white_list = [int(x) for x in config.get('SECURITY', 'white_list').split(';')]
admin_list = [int(x) for x in config.get('SECURITY', 'admin_list').split(';')]

players = {}
for p in config.options('PLAYERS'):
    players[int(p)] = [str(x) for x in config.get('PLAYERS', p).split(';')]


def get_token():
    return token


def get_white_list():
    return white_list


def get_admin_list():
    return admin_list


def get_players():
    return players
