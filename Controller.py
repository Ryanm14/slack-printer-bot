import os
from ctypes import Union

from dotenv import load_dotenv
import uuid
import PyPDF2, io, requests

from BearerAuth import BearerAuth

load_dotenv()
RYAN_USER_ID = os.environ['RYAN_USER_ID']
SLACK_AUTH_TOKEN = os.environ['SLACK_AUTH_TOKEN']
RYAN_VENMO = os.environ['RYAN_VENMO']

class PrintOrder:
    def __init__(self, user_name, user_email, file_url, copies, userId):
        self.user_name = user_name
        self.user_email = user_email
        self.file_url = file_url
        self.copies = copies
        self.userId = userId
        self.orderId = str(uuid.uuid4())


class DxPrinterController:
    def __init__(self):
        self.print_queue = {}
        self.latest_request: Union(PrintOrder, None) = None

    def received_message(self, client, say, event):
        if self.is_from_ryan(event):
            self.handle_ryan_command(event, say)
            return

        if 'files' not in event:
            say("No file was sent!")
            return

        user, copies_text, file_url = event['user'], event['text'], event['files'][0]['url_private']
        copies = 1

        if copies_text.isdigit():
            copies = int(copies)
        else:
            if copies_text:
                say("You sent an invalid number of copies! Canceling print!")

        pdf_reader = self.get_pdf(file_url)
        total_pages = pdf_reader.numPages * copies

        if total_pages > 10:
            say('Too many pages. Text Ryan. Canceling print!')
            return

        real_name, email = self.get_user_details(user, client)
        cost = (total_pages - 1) * 0.05 + .25

        print_order = PrintOrder(user_name=real_name, user_email=email, file_url=file_url, copies=copies, userId=user)
        self.save_pdf(pdf_reader, print_order.orderId)
        self.print_queue[print_order.orderId] = print_order
        self.latest_request = print_order
        self.message_ryan_new_order(print_order, say)

        say(f"Print order {print_order.orderId} received with {total_pages} pages. Venmo @{RYAN_VENMO}: ${cost} to print.")

    def is_from_ryan(self, event):
        return event['user'] == RYAN_USER_ID

    def get_user_details(self, user, client):
        id = client.users_profile_get(user=user).data['profile']
        return id['real_name'], id['email']

    def get_pdf(self, file_url):
        response = requests.get(file_url, auth=BearerAuth(SLACK_AUTH_TOKEN))
        pdf_file = io.BytesIO(response.content)
        return PyPDF2.PdfFileReader(pdf_file)

    def save_pdf(self, pdf_reader, print_id):
        pdfWriter = PyPDF2.PdfFileWriter()

        for pageNum in range(pdf_reader.numPages):
            pdfWriter.addPage(pdf_reader.getPage(pageNum))

        with open(f'./pdf/{print_id}.pdf', 'wb') as f:
            pdfWriter.write(f)

    def message_ryan_new_order(self, print_order, say):
        say(f"{print_order.user_name}, {print_order.user_email} requested to print {print_order.copies} copies, "
            f"orderID: {print_order.orderId}", channel=RYAN_USER_ID)

    def print_pdf(self, orderId):
        os.system(f"lp ./pdf/{orderId}.pdf")

    def handle_ryan_command(self, event, say):
        text = event['text']

        if text == "accept" and self.latest_request is not None:
            say(f"Ok! Accepting and printing order {self.latest_request.orderId}", channel=RYAN_USER_ID)
            say(f"Ryan accepted your order", channel=self.latest_request.userId)
            self.print_pdf(self.latest_request.orderId)
            self.print_queue.pop(self.latest_request.orderId)
            self.latest_request = None
        elif text == "deny" and self.latest_request is not None:
            say(f"Ok! Denied order {self.latest_request.orderId}", channel=RYAN_USER_ID)
            say(f"Ryan denied your order", channel=self.latest_request.userId)
            self.print_queue.pop(self.latest_request.orderId)
            self.latest_request = None
        else:
            if self.latest_request:
                say(f"Error: invalid command", channel=RYAN_USER_ID)
            else:
                say(f"Error: no current order", channel=RYAN_USER_ID)

