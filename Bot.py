import os
import requests
import time
import logging

# ----------------------------------------------------------------------
# تنظیمات لاگ
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# توکن ربات (از secret گیت‌هاب خوانده می‌شود)
BOT_TOKEN = os.environ.get('BALE_BOT_TOKEN')
if not BOT_TOKEN:
    raise ValueError("لطفاً BALE_BOT_TOKEN را در secrets گیت‌هاب تنظیم کنید.")

# آدرس API بله (ساختار مشابه تلگرام)
BASE_URL = f"https://tapi.bale.ai/bot{BOT_TOKEN}"

# اطلاعات ارسال به سرور JSON
JSON_SERVER_URL = "https://tk-server.ir/json/edit.php"
SERVER_NAME = "T11"
SERVER_PASS = "T11"

OFFSET = 0   # آخرین update_id پردازش‌شده

# ----------------------------------------------------------------------
def init_offset():
    """دریافت آخرین update_id برای نادیده گرفتن پیام‌های قدیمی."""
    global OFFSET
    try:
        resp = requests.get(
            f"{BASE_URL}/getUpdates",
            params={'offset': -1, 'limit': 1, 'timeout': 1}
        )
        if resp.status_code == 200 and resp.json().get('ok'):
            result = resp.json().get('result', [])
            if result:
                OFFSET = result[-1]['update_id'] + 1
                logger.info(f"شروع از update_id = {OFFSET}")
            else:
                logger.info("هنوز پیامی دریافت نشده، از offset=0 شروع می‌کنیم.")
        else:
            logger.warning(f"خطا در دریافت offset اولیه: {resp.text}")
    except Exception as e:
        logger.warning(f"استثناء در init_offset: {e}")
        OFFSET = 0

# ----------------------------------------------------------------------
def send_to_server(text: str):
    """ارسال یک رشته به سرور JSON با پارامترهای مشخص."""
    payload = {
        'name': SERVER_NAME,
        'pass': SERVER_PASS,
        'data': text
    }
    try:
        resp = requests.post(JSON_SERVER_URL, data=payload, timeout=10)
        logger.info(f"پاسخ سرور JSON: {resp.status_code} | {resp.text[:100]}")
    except Exception as e:
        logger.error(f"ارسال به سرور JSON ناموفق: {e}")

# ----------------------------------------------------------------------
def get_updates():
    """دریافت آپدیت‌های جدید از API بله."""
    global OFFSET
    try:
        resp = requests.get(
            f"{BASE_URL}/getUpdates",
            params={'offset': OFFSET, 'timeout': 30},
            timeout=35
        )
        if resp.status_code != 200:
            logger.error(f"getUpdates کد وضعیت {resp.status_code} برگرداند.")
            return []
        data = resp.json()
        if not data.get('ok'):
            logger.error(f"پاسخ getUpdates نامعتبر: {data}")
            return []
        return data.get('result', [])
    except Exception as e:
        logger.error(f"خطا در getUpdates: {e}")
        return []

# ----------------------------------------------------------------------
def process_updates(updates):
    """پردازش پیام‌های دریافت‌شده و ارسال آن‌ها به سرور JSON."""
    global OFFSET
    for upd in updates:
        update_id = upd['update_id']
        # فقط پیام‌های جدیدتر از آخرین offset را پردازش کن
        if update_id >= OFFSET:
            OFFSET = update_id + 1

        message = upd.get('message')
        if not message:
            continue

        text = message.get('text')
        if text:
            logger.info(f"پیام دریافت شد: {text[:50]}...")
            send_to_server(text)

# ----------------------------------------------------------------------
def main():
    init_offset()
    logger.info("ربات آغاز به کار کرد. پس از ۳ ساعت توسط گیت‌هاب اکشنز متوقف خواهد شد.")
    while True:
        updates = get_updates()
        if updates:
            process_updates(updates)
        time.sleep(1)   # تاخیر کوتاه برای کاهش فشار روی سرور

if __name__ == '__main__':
    main()
