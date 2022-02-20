from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
import os
from dotenv import load_dotenv

load_dotenv()
SLACK_AUTH_TOKEN = os.environ['SLACK_AUTH_TOKEN']
SLACK_APP_TOKEN = os.environ['SLACK_APP_TOKEN']

app = App(token=SLACK_AUTH_TOKEN)

@app.event("message")
def message(body, say):
    say("Hey")

if __name__ == "__main__":
    handler = SocketModeHandler(app, SLACK_APP_TOKEN)
    handler.start()