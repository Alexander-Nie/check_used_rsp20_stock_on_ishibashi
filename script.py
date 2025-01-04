import requests
from bs4 import BeautifulSoup
import os

def check_availability(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # 你需要根据页面结构来调整下面的查找方式
    used_items = soup.find(text='中古').parent.find_next('span').text.strip('()')
    return int(used_items)

def send_telegram_message(message):
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    send_text = f'https://api.telegram.org/bot{token}/sendMessage?chat_id={chat_id}&text={message}'

    response = requests.get(send_text)
    return response.json()

def main():
    url = 'https://www.ishibashi.co.jp/ec/search/?PSTA=&PEND=&SWD=YAMAHA%E3%80%80RSP20&EWD=&CAT1=&CAT2=&CAT3=&SRT=3&LMT=24&TSEL=0'
    used_items_count = check_availability(url)
    
    if used_items_count > 0:
        send_telegram_message(f"中古项目数量为: {used_items_count}")

if __name__ == "__main__":
    main()
