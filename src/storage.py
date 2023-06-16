class MemoryStorage:
    # Unique instance for each chat
    instances = {}
    polls_locations = {}

    def __init__(self, chat_id):
        # inter-module vars
        self.callback_func_ref = None

        # choose_players.py
        self.chosen_players = {}

        # teams.py
        self.chosen_players_names = {}
        self.teams_count = None

        # poll.py
        self.last_poll_results = {}

        MemoryStorage.instances[chat_id] = self

    @classmethod
    def get_instance(cls, chat_id):
        if chat_id in cls.instances:
            return cls.instances[chat_id]
        else:
            MemoryStorage(chat_id)
            return cls.instances[chat_id]

    @classmethod
    def get_poll_location(cls, poll_id):
        if poll_id in cls.polls_locations:
            return cls.polls_locations[poll_id]
