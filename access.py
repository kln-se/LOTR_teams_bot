from parse_config import get_white_list, get_admin_list


def check_white_list(user_id: int) -> bool:
    if user_id in get_white_list():
        return True
    else:
        return False


def check_admin_list(user_id: int) -> bool:
    if user_id in get_admin_list():
        return True
    else:
        return False
