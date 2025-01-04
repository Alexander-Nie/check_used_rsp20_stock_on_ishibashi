import requests
from bs4 import BeautifulSoup
import os

def send_telegram_message(message):
    """Send a message to a Telegram user specified by chat ID."""
    token = os.environ['TELEGRAM_BOT_TOKEN']
    chat_id = os.environ['TELEGRAM_CHAT_ID']
    url = f"https://api.telegram.org/bot{token}/sendMessage?chat_id={chat_id}&text={message}"
    requests.get(url)

def main():
    url = 'https://www.ishibashi.co.jp/ec/search/?PSTA=&PEND=&SWD=YAMAHA%E3%80%80RSP20&EWD=&CAT1=&CAT2=&CAT3=&SRT=3&LMT=24&TSEL=0'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    used_tab = soup.find('div', class_='search_main_list_bar_tab', string=lambda text: '中古' in text if text else False)
    
    if used_tab:
        used_count = used_tab.text.split('(')[1].strip(')')
        if int(used_count) > 0:
            send_telegram_message(f"Usde RSP20 has stock: {used_count}")
        else:
            pass
    else:
        send_telegram_message("No Data: RSP20")


if __name__ == "__main__":
    main()

