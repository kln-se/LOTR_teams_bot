from src.parse_config import get_white_list, get_admin_list


def check_white_list(user_id: int) -> bool:
    return user_id in get_white_list()


def check_admin_list(user_id: int) -> bool:
    return user_id in get_admin_list()
