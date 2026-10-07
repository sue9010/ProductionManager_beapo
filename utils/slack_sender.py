import threading
import requests
import json
from config import Config

class SlackSender:
    @staticmethod
    def send_message(message):
        """
        슬랙으로 메시지를 전송합니다. (비동기 스레드 실행)
        """
        if not Config.SLACK_WEBHOOK_URL:
            print("Slack Webhook URL is not configured.")
            return

        def _send():
            try:
                payload = {"text": message}
                response = requests.post(
                    Config.SLACK_WEBHOOK_URL, 
                    data=json.dumps(payload),
                    headers={'Content-Type': 'application/json'}
                )
                if response.status_code != 200:
                    print(f"Failed to send slack message: {response.status_code}, {response.text}")
            except Exception as e:
                print(f"Error sending slack message: {e}")

        thread = threading.Thread(target=_send)
        thread.daemon = True
        thread.start()
