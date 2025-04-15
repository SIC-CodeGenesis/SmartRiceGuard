import requests
import json
import logging


# Konfigurasi logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # Output ke console
        logging.FileHandler('ubidots_client.log')  # Output ke file
    ]
)

logger = logging.getLogger(__name__)

class ubidots():
    def __init__(self, token, device_label):
        self.token = token
        self.device_label = device_label
        self.url = f"https://industrial.api.ubidots.com/api/v1.6/devices/{self.device_label}"
        self.headers = {
            "X-Auth-Token": self.token,
            "Content-Type": "application/json"
        }
    def send_bird_detection(self, value):
        """
        Send bird detection data to Ubidots.
            :param value: The value to send (1 for detected, 0 for not detected)
            :return: Response from Ubidots API
        """
        if value not in [1, 3]: 
            return None
        data = {
            "bird_detected": value
            }
        try:
            response = requests.post(self.url, headers=self.headers, json=data)
            response.raise_for_status()  # Raise an error for bad responses
            logger.info(f"Bird detection data sent successfully: {data}")
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error sending bird detection data: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding JSON response: {e}")
            return None