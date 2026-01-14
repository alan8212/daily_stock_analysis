import os
import logging
import requests
import json
from linebot import LineBotApi
from linebot.models import TextSendMessage
from linebot.exceptions import LineBotApiError

logger = logging.getLogger(__name__)

class NotificationManager:
    def __init__(self):
        # 讀取環境變數
        self.wechat_webhook = os.getenv('WECHAT_WEBHOOK_URL')
        self.feishu_webhook = os.getenv('FEISHU_WEBHOOK_URL')
        self.telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID')
        
        # === 新增 LINE 設定 ===
        self.line_token = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
        self.line_user_id = os.getenv('LINE_USER_ID')

    def push(self, title, content):
        """推送消息到所有配置的渠道"""
        message = f"{title}\n\n{content}"
        
        # 1. 企業微信
        if self.wechat_webhook:
            self._push_wechat(title, content)
            
        # 2. 飛書
        if self.feishu_webhook:
            self._push_feishu(title, content)
            
        # 3. Telegram
        if self.telegram_token and self.telegram_chat_id:
            self._push_telegram(message)
            
        # 4. LINE (新增的功能)
        if self.line_token and self.line_user_id:
            self._push_line(message)

    def _push_line(self, message):
        """發送 LINE 訊息"""
        try:
            line_bot_api = LineBotApi(self.line_token)
            # LINE 一次訊息限制 5000 字，如果太長可能要切分，這裡先直接發送
            line_bot_api.push_message(self.line_user_id, TextSendMessage(text=message))
            logger.info("✅ LINE 通知推送成功")
        except Exception as e:
            logger.error(f"❌ LINE 推送失敗: {e}")

    def _push_wechat(self, title, content):
        data = {
            "msgtype": "markdown",
            "markdown": {
                "content": f"## {title}\n{content}"
            }
        }
        try:
            resp = requests.post(self.wechat_webhook, json=data)
            if resp.json().get('errcode') == 0:
                logger.info("✅ 企业微信推送成功")
            else:
                logger.error(f"❌ 企业微信推送失败: {resp.text}")
        except Exception as e:
            logger.error(f"❌ 企业微信推送异常: {e}")

    def _push_feishu(self, title, content):
        data = {
            "msg_type": "interactive",
            "card": {
                "header": {"title": {"content": title, "tag": "plain_text"}},
                "elements": [{"tag": "div", "text": {"content": content, "tag": "lark_md"}}]
            }
        }
        try:
            resp = requests.post(self.feishu_webhook, json=data)
            if resp.json().get('code') == 0:
                logger.info("✅ 飞书推送成功")
            else:
                logger.error(f"❌ 飞书推送失败: {resp.text}")
        except Exception as e:
            logger.error(f"❌ 飞书推送异常: {e}")

    def _push_telegram(self, message):
        url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
        data = {"chat_id": self.telegram_chat_id, "text": message, "parse_mode": "Markdown"}
        try:
            resp = requests.post(url, json=data)
            if resp.json().get('ok'):
                logger.info("✅ Telegram 推送成功")
            else:
                logger.error(f"❌ Telegram 推送失败: {resp.text}")
        except Exception as e:
            logger.error(f"❌ Telegram 推送异常: {e}")
