from django.apps import AppConfig
from multiprocessing import Process
import os

class MyProjectConfig(AppConfig):
    name = 'mdp'

    def ready(self):
        if os.environ.get('RUN_MAIN', None) != 'true':
            from .telegram_bot import start_bot
            bot_process = Process(target=start_bot)
            bot_process.start()