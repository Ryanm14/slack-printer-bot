from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
import os
from dotenv import load_dotenv
import PyPDF2, io, requests

load_dotenv()
SLACK_AUTH_TOKEN = os.environ['SLACK_AUTH_TOKEN']
SLACK_APP_TOKEN = os.environ['SLACK_APP_TOKEN']

RYAN_DM = os.environ['RYAN_DM']
RYAN_VENMO = os.environ['RYAN_VENMO']

app = App(token=SLACK_AUTH_TOKEN)

class BearerAuth(requests.auth.AuthBase):
    def __init__(self, token):
        self.token = token
    def __call__(self, r):
        r.headers["authorization"] = "Bearer " + self.token
        return r

@app.event("message")
def message(client, body, say, event):

    user = event['user']

    copies = event['text']

    if 'files' not in event:
        say("No file was sent!")
        return

    if copies:
        try:
            copies = int(copies)
        except:
            say("You didn't send a number assuming 1")
            copies = 1
    else:
        copies = 1

    # copies = 1

    file = event['files'][0]
    file_url = file['url_private']

    response = requests.get(file_url, auth=BearerAuth(SLACK_AUTH_TOKEN))
    pdf_file = io.BytesIO(response.content)
    pdf_reader = PyPDF2.PdfFileReader(pdf_file)
    num_pages = pdf_reader.numPages

    pdfWriter = PyPDF2.PdfFileWriter()
    for pageNum in range(pdf_reader.numPages):
        pdfWriter.addPage(pdf_reader.getPage(pageNum))

    with open('metadata.pdf', 'wb') as f:
        pdfWriter.write(f)

    total_pages = num_pages * copies

    if total_pages > 10:
        say('Too many pages text Ryan')
        return

    cost = (total_pages - 1) * 0.05 + .25

    say(f"Venmo {RYAN_VENMO}: ${cost}")

    id = client.users_profile_get(user=user).data['profile']
    real_name, email = id['real_name'], id['email']
    say(f"Someone requested a print: {real_name}, {email}" , channel=RYAN_DM)

    os.system("lp metadata.pdf")

if __name__ == "__main__":
    handler = SocketModeHandler(app, SLACK_APP_TOKEN)
    handler.start()