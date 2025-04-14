import numpy as np
import cv2 as cv
from ultralytics import YOLO
from camera_control import control_camera_esp_ai_thinker_to_hd
from dotenv import load_dotenv
import os
from mqtt_control import MyMQTTClient

load_dotenv()

if __name__ == "__main__":
    #************** Define Variables **************
    camera = os.environ.get("IP_ADDRESS_CAMERA1")
    broker = os.environ.get("BROKER")
    username = os.environ.get("BROKER_USERNAME")
    port = int(os.environ.get("BROKER_PORT"))
    password = os.environ.get("BROKER_PASSWORD")
    
    # ************* Cek Camera *************
    cek_camera = control_camera_esp_ai_thinker_to_hd(camera)
    if not cek_camera:
        raise ValueError("Camera not connected")
    
    # ************* Connect to MQTT Broker *************
    client = MyMQTTClient(broker, port, username, password)
    if not client:
        raise ValueError("MQTT Broker not connected")

    # ************* Load Model *************
    model_bird = YOLO('Model/yolo11m-birds-detection_best.pt')

    # ************* Start Camera *************
    cap = cv.VideoCapture(f'http://{camera}:81/stream')
    if not cap.isOpened():
        print("Cannot open camera")
        exit()
    while True:
        ret, frame = cap.read()
        
        if not ret:
            print("Can't receive frame (stream end?). Exiting ...")
            break

        frame = cv.resize(frame, (640, 640))
        results = model_bird.predict(source=frame, conf=0.5, show=False, save=False, stream=True)
        
        for result in results:
            for box in result.boxes:
                if int(box.cls[0]) == 14:  
                    x1, y1, x2, y2 = map(int, box.xyxy[0])  
                    conf = box.conf[0]  
                    cls = int(box.cls[0])  
                    label = f"{model_bird.names[cls]} {conf:.2f}"  
                    client.publish_play_sound()  # Publish sound play command
                    
                    # Draw bounding box and label on the frame
                    cv.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv.putText(frame, label, (x1, y1 - 10), cv.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
        cv.imshow('frame', frame)
        if cv.waitKey(1) == ord('q'):
            break
    
    cap.release()
    cv.destroyAllWindows()