from machine import Pin, ADC
import dht
import time
import network
import urequests as requests

# Konfigurasi variable global
DEVICE_ID = "smart-rice-guard"
WIFI_SSID =  "kos orange"
WIFI_PASSWORD = "kosorangejogja"
TOKEN = "BBUS-noZ4cLro76NKaG3kLoy3kvfFgtTQiZ"

# Fungsi membuat JSON untuk Ubidots
def create_json_data(temp, hum, light, soil):
    return {
        "temperature": temp,
        "humidity": hum,
        "light_level": light,
        "soil_moisture": soil
    }

# Fungsi kirim data ke Ubidots
def send_data_to_ubidots(data):
    url = "http://industrial.api.ubidots.com/api/v1.6/devices/" + DEVICE_ID
    headers = {"Content-Type": "application/json", "X-Auth-Token": TOKEN}
    try:
        response = requests.post(url, json=data, headers=headers)
        print("UBIDOTS Response:", response.text)
    except Exception as e:
        print("Gagal mengirim ke Ubidots:", e)

# Koneksi WiFi
wifi = network.WLAN(network.STA_IF)
wifi.active(True)
print("Menghubungkan ke WiFi...")
wifi.connect(WIFI_SSID, WIFI_PASSWORD)

while not wifi.isconnected():
    print("Tunggu koneksi...")
    time.sleep(0.5)

print("WiFi Tersambung:", wifi.ifconfig())

# Inisialisasi sensor
dht_sensor = dht.DHT11(Pin(33))

ldr = ADC(Pin(32))
ldr.atten(ADC.ATTN_11DB)

soil = ADC(Pin(35))
soil.atten(ADC.ATTN_11DB)
soil.width(ADC.WIDTH_10BIT)

# Loop utama
while True:
    try:
        # Baca sensor
        dht_sensor.measure()
        temp = dht_sensor.temperature()
        hum = dht_sensor.humidity()
        ldr_value = ldr.read()
        soil_value = soil.read()
        ldr_percent = (ldr_value / 4095) * 100

        print("=== Sensor Data ===")
        print("Temperature: {:.1f} °C".format(temp))
        print("Humidity   : {:.1f} %".format(hum))
        print("Cahaya     : {} ({:.2f}%)".format(ldr_value, ldr_percent))
        print("Soil Moist.:", soil_value)
        print("====================")

        # Buat dan kirim data
        json_data = create_json_data(temp, hum, ldr_value, soil_value)
        send_data_to_ubidots(json_data)

    except OSError as e:
        print("Gagal membaca sensor:", e)

    time.sleep(5)  # Delay antar kirim
