import time
import paho.mqtt.client as paho
from paho import mqtt
import os
from dotenv import load_dotenv

load_dotenv()

broker = os.environ.get("BROKER")
username = os.environ.get("BROKER_USERNAME")
port = os.environ.get("BROKER_PORT")
password = os.environ.get("BROKER_PASSWORD")

class MyMQTTClient():
    def __init__(self, broker, port, username, password):
        self.broker = broker
        self.port = port
        self.username = username
        self.password = password
        self.client = self.connect_mqtt()
        self.client.loop_start()
        self.timer = time.time()
        self.max_time = 5

    def connect_mqtt(self):
        def on_connect(client, userdata, flags, rc, properties=None):
            print("CONNACK received with code %s." % rc)

        # with this callback you can see if your publish was successful
        def on_publish(client, userdata, mid, properties=None):
            print("mid: " + str(mid))

        # print which topic was subscribed to
        def on_subscribe(client, userdata, mid, granted_qos, properties=None):
            print("Subscribed: " + str(mid) + " " + str(granted_qos))

        # print message, useful for checking if it was successful
        def on_message(client, userdata, msg):
            print(msg.topic + " " + str(msg.qos) + " " + str(msg.payload))
        
        def on_disconnect(client, userdata, rc):
            FIRST_RECONNECT_DELAY = 1
            RECONNECT_RATE = 2
            MAX_RECONNECT_COUNT = 12
            MAX_RECONNECT_DELAY = 60
            print("Disconnected with result code: %s", rc)
            reconnect_count, reconnect_delay = 0, FIRST_RECONNECT_DELAY
            while reconnect_count < MAX_RECONNECT_COUNT:
                print("Reconnecting in %d seconds...", reconnect_delay)
                time.sleep(reconnect_delay)

                try:
                    client.reconnect()
                    print("Reconnected successfully!")
                    return
                except Exception as err:
                    print("%s. Reconnect failed. Retrying...", err)

                reconnect_delay *= RECONNECT_RATE
                reconnect_delay = min(reconnect_delay, MAX_RECONNECT_DELAY)
                reconnect_count += 1
            print("Reconnect failed after %s attempts. Exiting...", reconnect_count)

        client = paho.Client(client_id="server-publish", userdata=None, protocol=paho.MQTTv5)
        client.on_connect = on_connect

        # enable TLS for secure connection
        client.tls_set(tls_version=mqtt.client.ssl.PROTOCOL_TLS)
        # set username and password
        client.username_pw_set(self.username, self.password)
        # connect to HiveMQ Cloud on port 8883 (default for MQTT)
        client.connect(self.broker, 8883)

        # setting callbacks, use separate functions like above for better visibility
        client.on_subscribe = on_subscribe
        client.on_message = on_message
        client.on_publish = on_publish
        client.on_disconnect = on_disconnect
        return client


    def publish_play_sound(self):
        topic = "control/sawah1/mp3player/play"
        payload = "{\"action\": \"play sound test\"}"
        if time.time() - self.timer < self.max_time:
            print(time.time() - self.timer)
            print("Waiting for the previous command to finish...")
            return
        result = self.client.publish(topic, payload, qos=1)
        self.timer = time.time()
        status = result[0]
        if status == 0:
            print(f"Send `{payload}` to topic `{topic}`")
        else:
            print(f"Failed to send message to topic {topic}")

