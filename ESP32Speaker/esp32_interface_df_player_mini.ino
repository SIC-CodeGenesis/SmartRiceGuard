#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include "SoftwareSerial.h"
#include "DFRobotDFPlayerMini.h"

// ==== DFPlayer Mini Pins ====
static const uint8_t PIN_MP3_TX = 26; // to DFPlayer RX
static const uint8_t PIN_MP3_RX = 27; // to DFPlayer TX
SoftwareSerial softwareSerial(PIN_MP3_RX, PIN_MP3_TX);
DFRobotDFPlayerMini player;

// ==== WiFi Credentials ====
const char* ssid = "kos orange";
const char* password = "kosorangejogja";

// ==== MQTT Config ====
const char* mqtt_server = "239c5a7e95d945809eafbdebe57802a5.s1.eu.hivemq.cloud"; 
const char* mqtt_user = "codegenesis";
const char* mqtt_pass = "codegenesisUni203";
const int mqtt_port = 8883;
const char* mqtt_topic = "#";

WiFiClientSecure espClient;
PubSubClient client(espClient);

void setup() {
  espClient.setInsecure();

  // Init USB serial port for debugging
  Serial.begin(9600);
  // Init serial port for DFPlayer Mini
  softwareSerial.begin(9600);
  connectToWiFi();
  client.setServer(mqtt_server, mqtt_port);
  client.setCallback(callback);

  if (player.begin(softwareSerial)) {
    Serial.println("✅ DFPlayer Mini connected.");
    player.volume(5);
    player.enableDAC();
    player.enableLoop();
    // player.play(1);
  } else {
    Serial.println("❌ DFPlayer Mini NOT connected.");
  }
}

void loop() {
    if (!client.connected()) {
    reconnectMQTT();
  }
  client.loop();

  static unsigned long timer = millis();

  // if (millis() - timer > 5000) {
  //   timer = millis();
  //   player.stop();
  //   player.next();  //Play next mp3 every 3 second.
  // }
  
  // if (player.available()) {
  //   printDetail(player.readType(), player.read());  //Print the detail message from DFPlayer to handle different errors and states.
  // }
}

void callback(char* topic, byte* payload, unsigned int length) {

  String message;
  for (unsigned int i = 0; i < length; i++) {
    message += (char)payload[i];
  }

  Serial.print("Message arrived [");
  Serial.print(topic);
  Serial.print("]: ");
  Serial.println(message);

  String topicStr = String(topic);
  String action = topicStr.substring(topicStr.lastIndexOf('/') + 1);

  // Parse JSON payload
  DynamicJsonDocument doc(256);
  DeserializationError error = deserializeJson(doc, message);
  if (error) {
    Serial.println("Failed to parse JSON");
    return;
  }
  if (topicStr.startsWith("control/sawah1/mp3player/")) {
    handleMp3playerTopic(action, doc);
  }

}

void handleMp3playerTopic(String action, DynamicJsonDocument payload){
  Serial.print("Received MP3Player action: ");
  Serial.println(action);
  Serial.print("Received MP3Player payload: ");
  // Serial.println(payload.c_str());

  if(action =="play"){
      player.play(1); 
  } 
  else if (action == "pause") {
    player.pause();
  }
  else if (action == "stop") {
    player.stop();
  }
  else if (action == "loop") {
    int filenumber = payload["filenumber"] || 1;
    player.loop(filenumber);
  }
    else if (action == "next") {
    player.next();
  }
  else if (action == "set_volume") {
      int value = payload["value"] | -1;
      player.volume(value);
  }
}

void reconnectMQTT() {
  while (!client.connected()) {
    Serial.print("Connecting to MQTT...");
    if (client.connect("ESP32Client", mqtt_user, mqtt_pass)) {
      Serial.println("connected");
      client.subscribe(mqtt_topic); // if needed
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      delay(2000);
    }
  }
}

void connectToWiFi() {
  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi connected. IP: " + WiFi.localIP().toString());
}

void printDetail(uint8_t type, int value){
  switch (type) {
    case TimeOut:
      Serial.println(F("Time Out!"));
      break;
    case WrongStack:
      Serial.println(F("Stack Wrong!"));
      break;
    case DFPlayerCardInserted:
      Serial.println(F("Card Inserted!"));
      break;
    case DFPlayerCardRemoved:
      Serial.println(F("Card Removed!"));
      break;
    case DFPlayerCardOnline:
      Serial.println(F("Card Online!"));
      break;
    case DFPlayerUSBInserted:
      Serial.println("USB Inserted!");
      break;
    case DFPlayerUSBRemoved:
      Serial.println("USB Removed!");
      break;
    case DFPlayerPlayFinished:
      Serial.print(F("Number:"));
      Serial.print(value);
      Serial.println(F(" Play Finished!"));
      break;
    case DFPlayerError:
      Serial.print(F("DFPlayerError:"));
      switch (value) {
        case Busy:
          Serial.println(F("Card not found"));
          break;
        case Sleeping:
          Serial.println(F("Sleeping"));
          break;
        case SerialWrongStack:
          Serial.println(F("Get Wrong Stack"));
          break;
        case CheckSumNotMatch:
          Serial.println(F("Check Sum Not Match"));
          break;
        case FileIndexOut:
          Serial.println(F("File Index Out of Bound"));
          break;
        case FileMismatch:
          Serial.println(F("Cannot Find File"));
          break;
        case Advertise:
          Serial.println(F("In Advertise"));
          break;
        default:
          break;
      }
      break;
    default:
      break;
  }
  
}