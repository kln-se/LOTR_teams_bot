class MemoryStorage:
    # Unique instance for each chat
    instances = {}
    polls_locations = {}

    def __init__(self, chat_id):
        # inter-module vars
        self.callback_func_ref = None

        # choose_players.py
        self.chosen_players = {}

        # tag_players.py
        self.subscribed_players = {}
        self.not_polled_players = {}
        self.ready_to_play_players = {}
        self.jobs_id = {}
        self.notification_thread = None
        self.stop_event = None

        # teams.py
        self.players_to_play = {}
        self.teams_count = None
        self.consider_rating = False

        # poll.py
        self.last_poll_results = {}
        self.last_poll_message_id = None
        self.last_poll_id = None

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
