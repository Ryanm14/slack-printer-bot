import os
from ctypes import Union

from dotenv import load_dotenv
import uuid
import PyPDF2, io, requests

import SwitchBotClicker
from BearerAuth import BearerAuth

load_dotenv()
RYAN_USER_ID = os.environ['RYAN_USER_ID']
SLACK_AUTH_TOKEN = os.environ['SLACK_AUTH_TOKEN']
RYAN_VENMO = os.environ['RYAN_VENMO']

class PrintOrder:
    def __init__(self, user_name, user_email, file_url, copies, total_pages, userId):
        self.user_name = user_name
        self.user_email = user_email
        self.file_url = file_url
        self.total_pages = total_pages
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
            copies = int(copies_text)
        else:
            if copies_text:
                say("You sent an invalid number of copies! Canceling print!")

        pdf_reader = self.get_pdf(file_url)
        total_pages = pdf_reader.numPages * copies

        real_name, email = self.get_user_details(user, client)
        cost = (total_pages - 1) * 0.05 + .25

        print_order = PrintOrder(user_name=real_name, user_email=email, file_url=file_url, copies=copies, total_pages=total_pages, userId=user)
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
        say(f"{print_order.user_name}, {print_order.user_email} requested to print {print_order.total_pages} total pages, "
            f"orderID: {print_order.orderId}. Respond accept/deny." , channel=RYAN_USER_ID)

    def print_pdf(self, orderId, copies=1):
        SwitchBotClicker.press()
        for i in range(copies):
            os.system(f"lp ./pdf/{orderId}.pdf")

    def handle_ryan_command(self, event, say):
        text = event['text']
        print_request = self.latest_request

        if '-' in text:
            parts = text.split(" ")
            text = parts[0]
            order_id = parts[1]
            if order_id not in self.print_queue:
                say("That order was not found", channel=RYAN_USER_ID)
                return
            else:
                print_request = self.print_queue[order_id]

        if text.strip().lower() == "accept" and print_request is not None:
            say(f"Ok! Accepting and printing order {print_request.orderId}", channel=RYAN_USER_ID)
            say(f"Ryan accepted your order", channel=print_request.userId)
            self.print_pdf(print_request.orderId, copies=print_request.copies)
            self.remove_from_queue(print_request)
        elif text.strip().lower() == "deny" and print_request is not None:
            say(f"Ok! Denied order {print_request.orderId}", channel=RYAN_USER_ID)
            say(f"Ryan denied your order", channel=print_request.userId)
            self.remove_from_queue(print_request)
        else:
            if print_request:
                say(f"Error: invalid command", channel=RYAN_USER_ID)
            else:
                say(f"Error: no current order", channel=RYAN_USER_ID)

    def remove_from_queue(self, print_request):
        self.print_queue.pop(print_request.orderId)
        if print_request == self.latest_request:
            self.latest_request = None

