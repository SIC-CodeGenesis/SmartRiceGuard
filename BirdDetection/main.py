import numpy as np
import cv2 as cv
from ultralytics import YOLO
from camera_control import control_camera_esp_ai_thinker_to_hd, cek_camera_esp_ai_thinker
from dotenv import load_dotenv
import os
from mqtt_control import MyMQTTClient
import asyncio
import websockets
import base64
import threading
import time
import janus
import logging
from ubidots_client import ubidots

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv(override=True)

# Set of WebSocket clients
ws_clients = set()
frame_queue = None

last_detection_time = 0
bird_detected = False

def send_detection_to_ubidots(client, detected):
    """
    Fungsi untuk mengirim data deteksi burung ke Ubidots.
    :param client: Instance dari ubidots client.
    :param detected: Boolean, True jika burung terdeteksi, False jika tidak.
    """
    global last_detection_time, bird_detected
    current_time = time.time()

    if detected:
        if current_time - last_detection_time >= 2:
            client.send_bird_detection(3)
            last_detection_time = current_time
            bird_detected = True
    else:
        # Jika sebelumnya terdeteksi dan sekarang tidak, kirim 0
        if bird_detected:
            client.send_bird_detection(1)
            bird_detected = False

async def send_frame_to_websocket(frame):
    try:
        if frame is None or not isinstance(frame, np.ndarray) or frame.size == 0:
            logger.warning("Invalid frame, skipping WebSocket send")
            return
        ret, buffer = cv.imencode('.jpg', frame, [int(cv.IMWRITE_JPEG_QUALITY), 85])
        if not ret:
            logger.warning("Failed to encode frame as JPEG")
            return
        jpg_as_text = base64.b64encode(buffer).decode('utf-8')
        to_remove = set()
        for websocket in ws_clients:
            try:
                await websocket.send(jpg_as_text)
            except websockets.exceptions.ConnectionClosed:
                to_remove.add(websocket)
            except Exception as e:
                logger.error(f"Error sending frame to client: {e}")
                to_remove.add(websocket)
        for ws in to_remove:
            ws_clients.discard(ws)
            logger.info("Removed disconnected WebSocket client")
    except Exception as e:
        logger.error(f"Error in send_frame_to_websocket: {e}")

async def websocket_server():
    async def handle_connection(websocket):
        logger.info("New WebSocket client connected")
        ws_clients.add(websocket)
        try:
            async for _ in websocket:
                await asyncio.sleep(0.1)
        except websockets.exceptions.ConnectionClosed:
            logger.info("WebSocket client disconnected")
        except Exception as e:
            logger.error(f"Error in handle_connection: {e}")
        finally:
            ws_clients.discard(websocket)
    try:
        server = await websockets.serve(handle_connection, "localhost", 8765, ping_interval=10, ping_timeout=20)
        logger.info("WebSocket server started on ws://localhost:8765")
        await server.wait_closed()
    except Exception as e:
        logger.error(f"WebSocket server error: {e}")

async def websocket_frame_sender(async_q):
    while True:
        try:
            frame = await async_q.get()
            if frame is None:
                logger.warning("Received None frame, skipping")
                continue
            await send_frame_to_websocket(frame)
            async_q.task_done()
        except Exception as e:
            logger.error(f"Error in websocket_frame_sender: {e}")
            await asyncio.sleep(0.1)

def start_async_loop():
    global frame_queue
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        queue = janus.Queue(maxsize=10)
        frame_queue = queue
        loop.run_until_complete(asyncio.gather(
            websocket_server(),
            websocket_frame_sender(queue.async_q)
        ))
    except Exception as e:
        logger.error(f"Async loop error: {e}")
    finally:
        loop.close()
        logger.info("Async loop closed")

def main():
    # Define variables
    camera_ip = os.environ.get("IP_ADDRESS_CAMERA1")
    broker = os.environ.get("BROKER")
    username = os.environ.get("BROKER_USERNAME")
    port = int(os.environ.get("BROKER_PORT"))
    password = os.environ.get("BROKER_PASSWORD")
    ubidots_token = os.environ.get("UBIDOTS_TOKEN")
    ubidots_device_id = os.environ.get("UBIDOTS_CLIENT_ID")

    # Check camera
    if not cek_camera_esp_ai_thinker(camera_ip):
        logger.error("Camera not connected")
        raise ValueError("Camera not connected")
    control_camera_esp_ai_thinker_to_hd(camera_ip)
    logger.info(f"Camera at {camera_ip} set to HD")

    # Connect MQTT
    client = MyMQTTClient(broker, port, username, password)
    ubidots_client = ubidots(ubidots_token, ubidots_device_id)
    if not client:
        logger.error("MQTT Broker not connected")
        raise ValueError("MQTT Broker not connected")
    logger.info("MQTT client connected")

    # Load YOLO model
    model_bird = YOLO('Model/yolo11m-birds-detection.pt')
    logger.info("YOLO model loaded")

    # Start camera
    cap = cv.VideoCapture(f'http://{camera_ip}:81/stream')
    if not cap.isOpened():
        logger.error("Cannot open camera")
        raise RuntimeError("Cannot open camera")
    logger.info("Camera stream opened")

    # Start WebSocket background thread
    thread = threading.Thread(target=start_async_loop, daemon=True)
    thread.start()
    logger.info("WebSocket thread started")

    # Wait for queue initialization
    for _ in range(10):
        if frame_queue is not None:
            break
        time.sleep(0.1)
    else:
        logger.error("Failed to initialize frame queue")
        raise RuntimeError("Failed to initialize frame queue")

    try:
        while True:
            start_time = time.time()
            ret, frame = cap.read()
            if not ret or frame is None or not isinstance(frame, np.ndarray) or frame.size == 0:
                logger.warning("Invalid frame from camera, attempting to reconnect")
                cap.release()
                cap = cv.VideoCapture(f'http://{camera_ip}:81/stream')
                if not cap.isOpened():
                    logger.error("Cannot reopen camera, exiting")
                    break
                time.sleep(0.2)
                continue

            frame = cv.resize(frame, (640, 640))
            results = model_bird.predict(source=frame, conf=0.5, show=False, save=False, stream=True)
            detected = False
            for result in results:
                for box in result.boxes:
                    if int(box.cls[0]) == 14:
                        detected = True
                        x1, y1, x2, y2 = map(int, box.xyxy[0])
                        conf = box.conf[0]
                        cls = int(box.cls[0])
                        # Validate class name
                        class_name = model_bird.names.get(cls, "Unknown")
                        if not isinstance(class_name, str):
                            logger.warning(f"Invalid class name for cls={cls}: {class_name}")
                            class_name = "Unknown"
                        label = f"{class_name} {conf:.2f}"
                        client.publish_play_sound()
                        cv.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                        try:
                            cv.putText(frame, label, (x1, y1 - 10), cv.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                        except Exception as e:
                            logger.error(f"Error in cv.putText: {e}")

            send_detection_to_ubidots(ubidots_client, detected)

            # Remove cv.imshow since Streamlit is the primary display
            cv.imshow('YOLO Detection', frame)
            cv.waitKey(1)

            if frame_queue is not None:
                try:
                    frame_queue.sync_q.put_nowait(frame)
                except janus.SyncQueueFull:
                    logger.debug("Frame queue full, dropping frame")
                    pass

            
            time.sleep(0.033)  # Approx 30 FPS

    except KeyboardInterrupt:
        logger.info("Program interrupted by user")
    except Exception as e:
        logger.error(f"Main loop error: {e}")
    finally:
        cap.release()
        # cv.destroyAllWindows()  # Removed since no cv.imshow
        if frame_queue is not None:
            frame_queue.close()
        logger.info("Resources cleaned up")

if __name__ == "__main__":
    main()