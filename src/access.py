from src.parse_config import get_white_list, get_admin_list


def check_white_list_decorator(bot_instance):
    def wrapper(func):
        def inner_wrapper(message):
            if message.from_user.id in get_white_list():
                func(message)
            else:
                bot_instance.reply_to(message,
                                      f"❗️Пользователь {message.from_user.username} не авторизован для доступа к "
                                      f"данному ресурсу.")

        return inner_wrapper

    return wrapper


def check_admin_list_decorator(bot_instance):
    def wrapper(func):
        def inner_wrapper(message):
            if message.from_user.id in get_admin_list():
                func(message)
            else:
                bot_instance.reply_to(message,
                                      f"❗️Пользователь {message.from_user.username} не авторизован для доступа к "
                                      f"данному ресурсу.")

        return inner_wrapper

    return wrapper
