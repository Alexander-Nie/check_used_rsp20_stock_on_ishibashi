import requests
from bs4 import BeautifulSoup
import os
import datetime
import pytz
import logging

# Set up logging with Japan time
logging.basicConfig(filename='check_used_items.log', level=logging.INFO, format='%(asctime)s - %(message)s', datefmt='%m-%d-%Y %H:%M:%S')
japan_timezone = pytz.timezone('Asia/Tokyo')

def send_telegram_message(message):
    """Send a message to a Telegram user specified by chat ID."""
    token = os.environ['TELEGRAM_BOT_TOKEN']
    chat_id = os.environ['TELEGRAM_CHAT_ID']
    url = f"https://api.telegram.org/bot{token}/sendMessage?chat_id={chat_id}&text={message}"
    requests.get(url)

def get_japan_time():
    """Returns the current time in Japan timezone."""
    return datetime.datetime.now(japan_timezone).strftime('%m-%d-%Y %H:%M:%S')

def check_time_and_send_health_message():
    """Check if the current time is between 14:00 and 15:00 in Japan and send a health check message."""
    japan_time_zone = pytz.timezone('Asia/Tokyo')
    current_japan_time = datetime.datetime.now(japan_time_zone)
    if current_japan_time.hour == 14:
        send_telegram_message('Check RSP20 Stock Health OK')

def main():
    # First, perform the health check message.
    check_time_and_send_health_message()

    url = 'https://www.ishibashi.co.jp/ec/search/?PSTA=&PEND=&SWD=YAMAHA%E3%80%80RSP20&EWD=&CAT1=&CAT2=&CAT3=&SRT=3&LMT=24&TSEL=0'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    used_tab = soup.find('div', class_='search_main_list_bar_tab', string=lambda text: '中古' in text if text else False)    
    if used_tab:
        used_count = used_tab.text.split('(')[1].strip(')')
        logging.info(f"{get_japan_time()}: Used RSP20 has stock: {used_count}")
        if int(used_count) > 0:
            send_telegram_message(f"Usde RSP20 has stock: {used_count}")
    else:
        logging.info(f"{get_japan_time()}: No Data: RSP20")
        send_telegram_message("No Data: RSP20")


if __name__ == "__main__":
    main()

