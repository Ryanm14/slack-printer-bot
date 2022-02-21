#!/usr/bin/python3

from switchbotpy import Bot
from dotenv import load_dotenv
import os

load_dotenv()

SWITCH_BOT_MAC = os.environ['SWITCH_BOT_MAC']


def press():
    times = 0
    while times < 5:
        try:
            Bot(bot_id=0, name="bot0", mac=SWITCH_BOT_MAC).press()
            return
        except:
            times += 1
