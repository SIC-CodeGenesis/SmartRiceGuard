from urllib.request import urlopen, Request
from dotenv import load_dotenv
import os
import json

load_dotenv()

def cek_camera_esp_ai_thinker(ip):
    """
    Check the connection to the ESP AI Thinker camera.
    :param ip: IP address of the camera
    :return: Response from the camera
    """
    if not ip:
        raise ValueError("IP address is required")
    url = "http://" + ip
    full_url = url + "/status"
    httprequest = Request(full_url, method='GET')
    httprequest.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3')
    httprequest.add_header('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8')

    with urlopen(httprequest) as response:
        if response.status != 200:
            raise Exception(f"Failed to connect to camera: {response.status}")
    return True

def control_camera_esp_ai_thinker_to_hd(ip):
    """
    Control the ESP AI Thinker camera to HD resolution.
    :param ip: IP address of the camera
    :return: Response from the camera control command
    """
    if not ip:
        raise ValueError("IP address is required")
    url = "http://" + ip
    full_url = url + "/control?var=framesize&val=12"
    httprequest = Request(full_url, method='GET')
    httprequest.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3')
    httprequest.add_header('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8')

    with urlopen(httprequest) as response:
        print(response.status)
        print(response.read().decode())
    return "Camera control command sent successfully"

def cek_camera_configuration(ip):
    """
    Check the camera configuration.
    :param ip: IP address of the camera
    :return: Response from the camera configuration command
    """
    if not ip:
        raise ValueError("IP address is required")
    url = "http://" + ip
    full_url = url + "/status"
    httprequest = Request(full_url, method='GET')
    httprequest.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3')
    httprequest.add_header('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8')
    data = None
    with urlopen(httprequest) as response:
        if response.status != 200:
            raise Exception(f"Failed to get camera configuration: {response.status}")
        response_data = response.read().decode()
        try:
            data = json.loads(response_data)
        except json.JSONDecodeError as e:
            raise Exception(f"Failed to parse camera configuration: {e}")
    return data
    

if __name__ == "__main__":
    url = os.environ.get("IP_ADDRESS_CAMERA1")
    