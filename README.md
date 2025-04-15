# Smart Rice Guard - Code Genesis

**Project Overview**  
Welcome to the **Smart Farmer Dashboard**, a cutting-edge IoT and AI-powered solution developed by **Team Code Genesis** for the **Samsung Innovation Campus Batch 6 IoT Gen AI Program**. This project aims to revolutionize rice farming by integrating advanced environmental monitoring, bird deterrence, and real-time analytics into a seamless, user-friendly platform. Our system combines ESP32-based hardware, AI-driven computer vision, MQTT communication, and a Streamlit-based dashboard to empower farmers with precision agriculture tools.

---

## Table of Contents
1. [Project Vision](#project-vision)
2. [Features](#features)
3. [System Architecture](#system-architecture)
4. [Components](#components)
   - [Streamlit Dashboard](#streamlit-dashboard)
   - [ESP32 Environment Monitoring](#esp32-environment-monitoring)
   - [ESP32 Bird Deterrence Speaker](#esp32-bird-deterrence-speaker)
   - [ESP32 Camera Webserver](#esp32-camera-webserver)
   - [Bird Detection Service](#bird-detection-service)
5. [Integration Flow](#integration-flow)
6. [Best Practices](#best-practices)
7. [Installation & Setup](#installation--setup)
8. [Usage](#usage)
9. [Challenges & Insights](#challenges--insights)
10. [Future Enhancements](#future-enhancements)
11. [Team Code Genesis](#team-code-genesis)
12. [License](#license)

---

## Project Vision
Rice farming faces challenges like environmental variability, pest control, and labor-intensive monitoring. Our vision is to create a **smart farming ecosystem** that:
- Monitors rice paddy conditions in real-time.
- Protects crops from birds using non-invasive, high-frequency sound.
- Provides farmers with an intuitive dashboard for live insights and control.
- Leverages AI for automated bird detection and response.

By integrating IoT, AI, and user-centric design, we aim to enhance crop yield, reduce manual effort, and promote sustainable farming practices.

---

## Features
- **Real-Time Environment Monitoring**: Tracks temperature, humidity, and soil moisture for optimal rice growth.
- **Automated Bird Deterrence**: Uses high-frequency sound (80-100 dB) to repel birds without harm.
- **Live Camera Feed**: Streams MJPEG video from ESP32-CAM for field surveillance.
- **AI-Powered Bird Detection**: Runs YOLO model for real-time bird detection with WebSocket-based inference streaming.
- **Interactive Dashboard**: Streamlit UI for configuring cameras, speakers, viewing live feeds, and analyzing data.
- **MQTT Control**: Seamless communication between dashboard, speakers, and AI services for responsive actions.
- **Scalable Architecture**: Modular design for easy integration of new sensors or features.

---

## System Architecture
The Smart Farmer Dashboard operates as a distributed system with interconnected hardware and software components:

```
[ESP32 Env. Monitoring] ----> [MQTT] ----> [Streamlit Dashboard]
       |                             |
       |                             |----> [WebSocket] ----> [Bird Detection (YOLO)]
       |                             |                       |
[ESP32 Camera Webserver] ----> [HTTP/MJPEG]                  |----> [MQTT] ----> [ESP32 Speaker]
```

- **ESP32 Devices**: Collect data, stream video, and emit sound.
- **Streamlit Dashboard**: Central UI for configuration and visualization.
- **Bird Detection Service**: Runs YOLO for real-time inference.
- **MQTT Broker**: Facilitates communication between components.
- **WebSocket**: Streams AI inference results to the dashboard.
- **HTTP/MJPEG**: Delivers live camera feeds.

---

## Components

### Streamlit Dashboard
- **Purpose**: User interface for farmers to monitor and control the system.
- **Features**:
  - **Dashboard**: Displays environmental metrics (temperature, humidity, soil moisture) in real-time.
  - **Live Cam**: Streams MJPEG video from ESP32-CAM via HTTP.
  - **Speaker Config**: Adjusts volume and sound files for bird deterrence via MQTT.
  - **Camera Config**: Sets resolution and XCLK for ESP32-CAM via HTTP.
- **Tech Stack**: Streamlit, Python, WebSocket client, MQTT (Paho), HTTP requests.
- **Best Practice**:
  - Use `st.session_state` to persist MQTT client and prevent multiple connections.
  - Implement notification timeouts (3 seconds) to avoid UI clutter.
  - Validate inputs to prevent crashes (e.g., empty camera IP).

### ESP32 Environment Monitoring
- **Purpose**: Monitors rice paddy conditions to inform irrigation and care decisions.
- **Sensors**: DHT22 (temperature/humidity), soil moisture sensor.
- **Functionality**:
  - Publishes sensor data to MQTT topics (e.g., `sensor/sawah1/env`).
  - Low-power mode for energy efficiency.
- **Tech Stack**: ESP32, Arduino IDE, MQTT client library.
- **Best Practice**:
  - Calibrate sensors for accuracy in humid environments.
  - Use deep sleep to extend battery life.
  - Buffer data locally during network outages.

### ESP32 Bird Deterrence Speaker
- **Purpose**: Emits high-frequency sound (80-100 dB) to repel birds.
- **Functionality**:
  - Subscribes to MQTT topic `control/sawah1/mp3player/#` for commands (play, stop, volume, file selection).
  - Plays preloaded sound files based on AI triggers or manual dashboard input.
- **Tech Stack**: ESP32, DFPlayer Mini (MP3 module), MQTT client library.
- **Best Practice**:
  - Use QoS 1 for reliable MQTT message delivery.
  - Test frequency range to ensure bird deterrence without disturbing other wildlife.
  - Implement failsafe to prevent speaker overuse.

### ESP32 Camera Webserver
- **Purpose**: Provides live video feed of the rice paddy.
- **Functionality**:
  - Runs a webserver on ESP32-CAM (AI-Thinker) to serve MJPEG frames over HTTP.
  - Configurable via HTTP endpoints (e.g., `/set_resolution`, `/set_xclk`).
  - Connects to Wi-Fi for seamless integration.
- **Tech Stack**: ESP32-CAM, Arduino IDE, HTTP server library.
- **Best Practice**:
  - Optimize MJPEG frame rate (e.g., 30 FPS) for bandwidth efficiency.
  - Secure HTTP endpoints with basic authentication.
  - Monitor Wi-Fi signal strength to ensure stable streaming.

### Bird Detection Service
- **Purpose**: Detects birds in real-time to trigger deterrence actions.
- **Functionality**:
  - Runs YOLO model on a server using OpenCV for bird detection.
  - Streams inference results (bounding boxes, confidence) to dashboard via WebSocket.
  - Publishes MQTT messages to `control/sawah1/mp3player/play` when birds are detected.
- **Tech Stack**: Python, OpenCV, YOLO, WebSocket server, MQTT (Paho).
- **Best Practice**:
  - Optimize YOLO model for low-latency inference (e.g., use YOLOv5s).
  - Handle WebSocket disconnections gracefully with reconnect logic.
  - Log inference results for debugging and model improvement.

---

## Integration Flow
1. **Environment Data**:
   - ESP32 sensors publish data to MQTT (`sensor/sawah1/env`).
   - Streamlit dashboard subscribes and displays metrics.

2. **Live Video**:
   - ESP32-CAM streams MJPEG frames over HTTP.
   - Streamlit dashboard fetches and renders the feed.

3. **Bird Detection**:
   - Camera feed is processed by the YOLO service.
   - Inference results are sent to dashboard via WebSocket.
   - If birds are detected, YOLO service publishes to MQTT (`control/sawah1/mp3player/play`).

4. **Speaker Control**:
   - ESP32 speaker subscribes to MQTT (`control/sawah1/mp3player/#`).
   - Plays sound when triggered by YOLO or manual dashboard input.
   - Dashboard configures speaker settings (volume, sound file) via MQTT.

5. **Camera Configuration**:
   - Dashboard sends HTTP requests to ESP32-CAM for settings (resolution, XCLK).
   - ESP32-CAM applies changes and updates the stream.

---

## Best Practices
To ensure reliability, scalability, and maintainability, we adopted the following practices:

1. **Modular Design**:
   - Separate Streamlit UI, ESP32 services, and AI inference into distinct modules.
   - Use clear MQTT topic hierarchies (e.g., `control/sawah1/`, `setting/sawah1/`).

2. **Connection Management**:
   - Use unique Client IDs for MQTT clients to prevent conflicts:
     ```python
     client = paho.Client(client_id=f"dashboard-{uuid.uuid4()}")
     ```
   - Implement cleanup logic to disconnect MQTT clients on app shutdown:
     ```python
     atexit.register(cleanup_mqtt_client)
     ```

3. **Error Handling**:
   - Validate environment variables (`.env`) to catch configuration errors early.
   - Log errors to files (`mqtt_client.log`, `streamlit_app.log`) for debugging.
   - Display user-friendly error messages in Streamlit UI.

4. **Performance Optimization**:
   - Limit MJPEG frame rate to balance quality and bandwidth.
   - Use lightweight YOLO models for faster inference.
   - Implement MQTT reconnect logic with exponential backoff.

5. **Security**:
   - Enable TLS for MQTT connections (`port 8883`).
   - Secure ESP32-CAM endpoints with authentication (planned).
   - Restrict MQTT topics with ACLs to prevent unauthorized access.

6. **User Experience**:
   - Show temporary notifications (3 seconds) in Streamlit to avoid UI clutter.
   - Place error messages near relevant controls for clarity.
   - Use responsive layouts (e.g., `st.columns`) for intuitive navigation.

7. **Hardware Reliability**:
   - Calibrate ESP32 sensors for rice paddy conditions (high humidity).
   - Use weatherproof enclosures for outdoor ESP32 devices.
   - Monitor ESP32 power consumption to ensure longevity.

---

## Installation & Setup
### Prerequisites
- **Hardware**:
  - ESP32 (DevKit for sensors, AI-Thinker for camera).
  - DHT22, soil moisture sensor, DFPlayer Mini, speaker.
- **Software**:
  - Python 3.8+, Streamlit, OpenCV, Paho-MQTT, WebSocket libraries.
  - Arduino IDE for ESP32 programming.
  - MQTT broker (e.g., HiveMQ Cloud, Mosquitto).
  - YOLO model weights (e.g., YOLOv5s).

### Steps
1. **Clone Repository**:
   ```bash
   git clone https://github.com/code-genesis/smart-farmer-dashboard.git
   cd smart-farmer-dashboard
   ```

2. **Set Up Environment**:
   - Install Python dependencies:
     ```bash
     pip install -r requirements.txt
     ```
   - Create `.env` file:
     ```
     BROKER=your.broker.com
     BROKER_PORT=8883
     BROKER_USERNAME=your_username
     BROKER_PASSWORD=your_password
     ```

3. **Flash ESP32 Devices**:
   - Use Arduino IDE to upload:
     - Environment monitoring code (`esp32_environment.ino`).
     - Camera webserver code (`esp32_camera.ino`).
     - Speaker code (`esp32_speaker.ino`).
   - Configure Wi-Fi credentials and MQTT broker details.

4. **Run Bird Detection Service**:
   - Start the YOLO server:
     ```bash
     python bird_detection_service.py
     ```
   - Ensure WebSocket port (e.g., 8765) and MQTT broker are accessible.

5. **Launch Streamlit Dashboard**:
   ```bash
   streamlit run app.py
   ```
   - Access at `http://localhost:8501`.

6. **Configure MQTT Broker**:
   - Set up ACLs to allow topics like `control/sawah1/#`, `sensor/sawah1/#`.
   - Verify TLS settings for port 8883.

---

## Usage
1. **Access Dashboard**:
   - Open `http://localhost:8501` in a browser.
   - Navigate via sidebar: Dashboard, Live Cam, Speaker Config, Camera Config.

2. **Monitor Environment**:
   - View temperature, humidity, and soil moisture on the Dashboard tab.

3. **Watch Live Feed**:
   - Go to Live Cam, enter ESP32-CAM IP, and start streaming.

4. **Control Speaker**:
   - In Speaker Config, adjust volume (0-30), select sound files, or trigger test sounds.
   - Sounds auto-play when birds are detected by YOLO.

5. **Configure Camera**:
   - In Camera Config, scan for cameras, set IP, and adjust resolution/XCLK.

6. **Bird Detection**:
   - Monitor WebSocket inference in the Dashboard for real-time bird alerts.
   - MQTT triggers speaker automatically on detection.

---

## Challenges & Insights
### Challenges
1. **MQTT Connection Stability**:
   - Issue: Reloads caused duplicate connections with static Client ID (`dashboard`).
   - Solution: Implemented cleanup logic and planned for unique Client IDs.
   - Insight: Always use dynamic Client IDs to avoid broker conflicts.

2. **Wi-Fi Reliability**:
   - Issue: ESP32-CAM dropped connections in outdoor settings.
   - Insight: Monitor RSSI and use Wi-Fi extenders for robust coverage.

3. **YOLO Latency**:
   - Issue: High inference time on resource-constrained servers.
   - Solution: Used YOLOv5s for balance between speed and accuracy.
   - Insight: Optimize models for edge devices or use GPU for production.

4. **Speaker Calibration**:
   - Issue: High-frequency sounds needed tuning for bird deterrence without disturbing other wildlife.
   - Insight: Field tests are critical for balancing effectiveness and ecology.

### Insights
- **IoT Scalability**: Modular MQTT topics allow easy addition of new sensors.
- **AI Integration**: WebSocket is ideal for streaming real-time AI results.
- **User-Centric Design**: Streamlit’s simplicity accelerates farmer adoption.
- **Sustainability**: Non-lethal bird deterrence aligns with eco-friendly farming.

---

## Future Enhancements
1. **Edge AI**: Deploy YOLO on ESP32 for offline bird detection.
2. **Mobile App**: Extend Streamlit to a mobile-friendly interface.
3. **Advanced Analytics**: Predict crop health using historical sensor data.
4. **Solar Power**: Integrate solar panels for ESP32 to ensure uptime.
5. **Multi-Field Support**: Scale dashboard for multiple rice paddies.
6. **Security**: Add OAuth for dashboard and encrypt MQTT payloads.

---

## Team Code Genesis
We are a passionate team from **Samsung Innovation Campus Batch 6 IoT Gen AI**, dedicated to leveraging technology for agriculture:
- **Member 1**: Thoriq Firdaus Arifin  IOT/DevOps/AI/ML/Streamlit – Lead and design architech.
- **Member 2**: Muhammad Javier Badrudtaman AI Engineer/ML/Iot – Developed YOLO-based bird detection.
- **Member 3**: Muammar Mufid IOT/Design Thinking– Crafted the AI Integration.
- **Member 4**: Muhammad Nanda Build UI/Devops – Ensured seamless MQTT/WebSocket flow.

Our collaboration reflects innovation, teamwork, and a commitment to empowering farmers.

---

## License
This project is licensed under the MIT License. See `LICENSE` for details.

---

**Join us in transforming agriculture with IoT and AI!**  
For questions, contributions, or feedback, contact **Team Code Genesis** at [insert contact].  

*Built with 💡 for Samsung Innovation Campus Batch 6, 2025.*
