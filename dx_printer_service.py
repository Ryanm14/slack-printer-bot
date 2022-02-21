from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
import os
from dotenv import load_dotenv

from Controller import DxPrinterController

load_dotenv()
SLACK_AUTH_TOKEN = os.environ['SLACK_AUTH_TOKEN']
SLACK_APP_TOKEN = os.environ['SLACK_APP_TOKEN']

RYAN_USER_ID = os.environ['RYAN_USER_ID']
RYAN_VENMO = os.environ['RYAN_VENMO']

app = App(token=SLACK_AUTH_TOKEN)
controller = DxPrinterController()

@app.event("message")
def message(client, say, event):
    controller.received_message(client, say, event)

if __name__ == "__main__":
    handler = SocketModeHandler(app, SLACK_APP_TOKEN)
    handler.start()