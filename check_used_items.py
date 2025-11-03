import requests
from bs4 import BeautifulSoup
import os
import datetime
import pytz
import logging
import json
import hashlib
import re
# 设置日志记录，使用日本时间
logging.basicConfig(filename='check_used_items.log', level=logging.INFO, format='%(asctime)s - %(message)s', datefmt='%m-%d-%Y %H:%M:%S')
japan_timezone = pytz.timezone('Asia/Tokyo')
# 缓存文件路径
CACHE_FILE = 'used_items_cache.json'
def send_telegram_message(message):
    """发送消息到Telegram用户"""
    token = os.environ['TELEGRAM_BOT_TOKEN']
    chat_id = os.environ['TELEGRAM_CHAT_ID']
    url = f"https://api.telegram.org/bot{token}/sendMessage?chat_id={chat_id}&text={message}"
    requests.get(url)
def get_japan_time():
    """返回日本时区的当前时间"""
    return datetime.datetime.now(japan_timezone).strftime('%m-%d-%Y %H:%M:%S')
def get_japan_datetime():
    """返回日本时区的当前datetime对象"""
    return datetime.datetime.now(japan_timezone)
def check_time_and_send_health_message():
    """检查当前时间是否在日本时间14:00到15:00之间，并发送健康检查消息"""
    current_japan_time = get_japan_datetime()
    if current_japan_time.hour == 14:
        send_telegram_message('Check RSP20 Stock Health OK')
def load_cache():
    """加载缓存的商品数据"""
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
                return cache_data
        except Exception as e:
            logging.error(f"加载缓存文件出错: {e}")
    return {"last_notification": "", "items": {}}
def save_cache(cache_data):
    """保存商品数据到缓存"""
    try:
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logging.error(f"保存缓存文件出错: {e}")
def extract_used_item_details(soup):
    """提取所有中古商品详情"""
    used_items = {}
    products_grid = soup.find('div', class_='im-products-grid')
    if not products_grid:
        return used_items
    
    product_items = products_grid.find_all('a', class_='im-products-card')
   
    for item in product_items:
        # 通过标签判断是否为中古：存在 .is-used 标签即视为中古
        used_tag = item.select_one('.im-products-card-icons .is-used')
        title_element = item.find('div', class_='im-products-card-title')
        if not used_tag or not title_element:
            continue  # 非中古或无标题，跳过

        title = title_element.text.strip()
       
        # 从href提取商品ID
        href = item.get('href')
        if not href:
            continue
           
        # 尝试从链接中提取数字ID
        id_match = re.search(r'/item/([^/]+)', href)
        if id_match:
            item_id = id_match.group(1)  # 提取匹配的ID部分
        else:
            # 如果无法提取到ID，使用完整链接作为备用
            item_id = href
       
        # 提取价格
        price_element = item.find('span', {'data-field': 'price'})
        soldout_element = item.find('div', class_='is-souldout')
        if soldout_element:
            price = "Sold Out"
        elif price_element:
            price = "¥" + price_element.text.strip()
        else:
            price = "价格未知"
       
        # 提取店铺信息
        shop_element = item.find('span', {'data-field': 'narrow6'})
        shop = shop_element.text.strip() if shop_element else "店铺未知"
       
        # 规范化URL：如果href是绝对地址，直接使用；否则拼接域名
        if href.startswith('http://') or href.startswith('https://'):
            full_url = href
        else:
            full_url = f"https://store.ishibashi.co.jp{href}"

        # 存储商品信息
        used_items[item_id] = {
            "title": title,
            "price": price,
            "shop": shop,
            "href": href,
            "url": full_url
        }
   
    return used_items
def compare_and_notify(current_items, cached_data):
    """比较当前商品和缓存商品，并通知变化"""
    cached_items = cached_data.get("items", {})
    changes = []
   
    # 检查新上架和价格变化的商品
    for item_id, item_data in current_items.items():
        if item_id not in cached_items:
            # 新上架的商品
            changes.append({
                "type": "new",
                "item": item_data
            })
        elif cached_items[item_id]["price"] != item_data["price"]:
            # 价格变化的商品
            changes.append({
                "type": "price_change",
                "item": item_data,
                "old_price": cached_items[item_id]["price"]
            })
   
    # 检查下架的商品
    for item_id, item_data in cached_items.items():
        if item_id not in current_items:
            changes.append({
                "type": "removed",
                "item": item_data
            })
   
    # 处理通知
    now = get_japan_datetime()
    last_notification = cached_data.get("last_notification", "")
   
    if last_notification:
        last_notification_time = datetime.datetime.strptime(last_notification, '%Y-%m-%d')
        today = now.replace(hour=0, minute=0, second=0, microsecond=0)
       
        # 确定是否需要发送每日汇总
        daily_summary_needed = last_notification_time.date() < today.date()
    else:
        daily_summary_needed = True
   
    # 如果有变化，立即通知
    if changes:
        for change in changes:
            item = change["item"]
            if change["type"] == "new":
                message = f"🆕 新中古商品上架:\n标题: {item['title']}\n价格: {item['price']}\n{item['shop']}\n链接: {item['url']}"
            elif change["type"] == "price_change":
                message = f"💰 价格变动:\n标题: {item['title']}\n{change['old_price']} -> {item['price']}\n{item['shop']}\n链接: {item['url']}"
            elif change["type"] == "removed":
                message = f"❌ 商品已下架:\n标题: {item['title']}\n价格: {item['price']}\n{item['shop']}"
           
            send_telegram_message(message)
            logging.info(f"变动通知: {message}")
       
        # 更新每日通知时间
        cached_data["last_notification"] = now.strftime('%Y-%m-%d')
   
    # 如果需要每日汇总且有中古商品，发送汇总信息
    elif daily_summary_needed and current_items:
        items_count = len(current_items)
        message = f"📊 每日中古RSP20汇总 ({now.strftime('%Y-%m-%d')}):\n"
        message += f"共有 {items_count} 件中古商品\n\n"
       
        for i, (item_id, item) in enumerate(current_items.items(), 1):
            message += f"{i}. {item['title']}\n价格: {item['price']}\n{item['shop']}\n\n"
       
        send_telegram_message(message)
        logging.info(f"发送每日汇总: 共{items_count}件商品")
       
        # 更新每日通知时间
        cached_data["last_notification"] = now.strftime('%Y-%m-%d')
   
    # 更新缓存
    cached_data["items"] = current_items
    return cached_data
def main():
    # 首先执行健康检查
    check_time_and_send_health_message()
   
    # 加载缓存的商品数据
    cache_data = load_cache()
   
    # 抓取页面
    url = 'https://store.ishibashi.co.jp/search?q=YAMAHA%E3%80%80RSP20'
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
       
        # 提取所有中古商品详细信息
        current_used_items = extract_used_item_details(soup)
        used_count = len(current_used_items)
        logging.info(f"{get_japan_time()}: Used RSP20 has stock: {used_count}")
       
        if used_count > 0:
            # 比较当前数据和缓存数据，并发送相应通知
            updated_cache = compare_and_notify(current_used_items, cache_data)
           
            # 保存更新后的缓存
            save_cache(updated_cache)
        else:
            # 如果没有中古库存但缓存中有数据，说明所有商品都下架了
            if cache_data.get("items", {}):
                send_telegram_message("所有中古RSP20商品已下架")
                logging.info("所有中古RSP20商品已下架")
                # 清空缓存中的商品（保留上次通知时间）
                cache_data["items"] = {}
                save_cache(cache_data)
            else:
                logging.info(f"{get_japan_time()}: No Used Data: RSP20")
                send_telegram_message("No Data: RSP20")
           
    except Exception as e:
        error_message = f"执行过程中出错: {str(e)}"
        logging.error(error_message)
        send_telegram_message(f"Error: {error_message}")
if __name__ == "__main__":
    main()
