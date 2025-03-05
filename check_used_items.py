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
            send_telegram_message(f"Used RSP20 has stock: {used_count}")
            
            # 查找所有产品列表项
            product_items = soup.find_all('li', class_='search_main_list_product')
            
            # 遍历查找含有"中古"的产品
            for item in product_items:
                # 检查产品描述中是否含有"中古"
                if '中古' in str(item):
                    # 提取产品链接和标题
                    title_element = item.find('a', class_='search_main_list_product_title')
                    if title_element:
                        href = title_element.get('href')
                        title = title_element.text.strip()
                        
                        # 提取价格
                        price_element = item.find('div', class_='search_main_list_product_amount')
                        price = price_element.text.strip() if price_element else "价格未知"
                        
                        # 提取店铺信息
                        shop_element = item.find('div', class_='search_main_list_product_sub_1')
                        shop = shop_element.text.strip() if shop_element else "店铺未知"
                        
                        # 构建详细信息消息并发送
                        detail_message = f"{title}\n价格: {price}\n{shop}\n链接: https://www.ishibashi.co.jp{href}"
                        send_telegram_message(detail_message)
    else:
        logging.info(f"{get_japan_time()}: No Data: RSP20")
        send_telegram_message("No Data: RSP20")


if __name__ == "__main__":
    main()
