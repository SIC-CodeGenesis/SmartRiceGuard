#include "esp_camera.h"
#include <WiFi.h>
#include <freertos/FreeRTOS.h>
#include <freertos/task.h>
#include <freertos/semphr.h>

// ===========================
// Enter your WiFi credentials
// ===========================
const char *ssid = "Mymifi";
const char *password = "Moleyukgas";

// Select camera model
#define CAMERA_MODEL_AI_THINKER
#include "camera_pins.h"

// Shared buffer and semaphore
camera_fb_t *shared_frame = NULL;
SemaphoreHandle_t frame_semaphore;

// Function declarations
void startCameraServer();
void setupLedFlash(int pin);
void cameraCaptureTask(void *pvParameters);
void httpStreamTask(void *pvParameters);

void setup()
{
    Serial.begin(115200);
    Serial.setDebugOutput(true);
    Serial.println();

    // Initialize semaphore
    frame_semaphore = xSemaphoreCreateMutex();
    if (frame_semaphore == NULL)
    {
        Serial.println("Failed to create semaphore");
        return;
    }

    // Camera configuration
    camera_config_t config;
    config.ledc_channel = LEDC_CHANNEL_0;
    config.ledc_timer = LEDC_TIMER_0;
    config.pin_d0 = Y2_GPIO_NUM;
    config.pin_d1 = Y3_GPIO_NUM;
    config.pin_d2 = Y4_GPIO_NUM;
    config.pin_d3 = Y5_GPIO_NUM;
    config.pin_d4 = Y6_GPIO_NUM;
    config.pin_d5 = Y7_GPIO_NUM;
    config.pin_d6 = Y8_GPIO_NUM;
    config.pin_d7 = Y9_GPIO_NUM;
    config.pin_xclk = XCLK_GPIO_NUM;
    config.pin_pclk = PCLK_GPIO_NUM;
    config.pin_vsync = VSYNC_GPIO_NUM;
    config.pin_href = HREF_GPIO_NUM;
    config.pin_sccb_sda = SIOD_GPIO_NUM;
    config.pin_sccb_scl = SIOC_GPIO_NUM;
    config.pin_pwdn = PWDN_GPIO_NUM;
    config.pin_reset = RESET_GPIO_NUM;
    config.xclk_freq_hz = 20000000;
    config.frame_size = FRAMESIZE_UXGA;
    config.pixel_format = PIXFORMAT_JPEG;
    config.grab_mode = CAMERA_GRAB_WHEN_EMPTY;
    config.fb_location = CAMERA_FB_IN_PSRAM;
    config.jpeg_quality = 12;
    config.fb_count = 1;

    if (config.pixel_format == PIXFORMAT_JPEG)
    {
        if (psramFound())
        {
            config.jpeg_quality = 10;
            config.fb_count = 2;
            config.grab_mode = CAMERA_GRAB_LATEST;
        }
        else
        {
            config.frame_size = FRAMESIZE_SVGA;
            config.fb_location = CAMERA_FB_IN_DRAM;
        }
    }
    else
    {
        config.frame_size = FRAMESIZE_240X240;
#if CONFIG_IDF_TARGET_ESP32S3
        config.fb_count = 2;
#endif
    }

    // Camera init
    esp_err_t err = esp_camera_init(&config);
    if (err != ESP_OK)
    {
        Serial.printf("Camera init failed with error 0x%x", err);
        return;
    }

    sensor_t *s = esp_camera_sensor_get();
    if (s->id.PID == OV3660_PID)
    {
        s->set_vflip(s, 1);
        s->set_brightness(s, 1);
        s->set_saturation(s, -2);
    }
    if (config.pixel_format == PIXFORMAT_JPEG)
    {
        s->set_framesize(s, FRAMESIZE_QVGA);
    }

#if defined(LED_GPIO_NUM)
    setupLedFlash(LED_GPIO_NUM);
#endif

    // WiFi setup
    WiFi.begin(ssid, password);
    WiFi.setSleep(false);

    Serial.print("WiFi connecting");
    while (WiFi.status() != WL_CONNECTED)
    {
        delay(500);
        Serial.print(".");
    }
    Serial.println("");
    Serial.println("WiFi connected");

    // Create tasks
    xTaskCreatePinnedToCore(
        cameraCaptureTask,
        "CameraCapture",
        4096,
        NULL,
        5,
        NULL,
        0 // Core 0
    );

    xTaskCreatePinnedToCore(
        httpStreamTask,
        "HttpStream",
        4096,
        NULL,
        5,
        NULL,
        1 // Core 1
    );

    Serial.print("Camera Ready! Use 'http://");
    Serial.print(WiFi.localIP());
    Serial.println("' to connect");
}

void loop()
{
    // Main loop does nothing, tasks handle everything
    delay(10000);
}

void cameraCaptureTask(void *pvParameters)
{
    while (true)
    {
        camera_fb_t *fb = esp_camera_fb_get();
        if (!fb)
        {
            Serial.println("Camera capture failed");
            vTaskDelay(100 / portTICK_PERIOD_MS);
            continue;
        }

        if (xSemaphoreTake(frame_semaphore, portMAX_DELAY) == pdTRUE)
        {
            if (shared_frame)
            {
                esp_camera_fb_return(shared_frame);
            }
            shared_frame = fb;
            xSemaphoreGive(frame_semaphore);
        }
        vTaskDelay(10 / portTICK_PERIOD_MS); // Adjust delay as needed
    }
}

void httpStreamTask(void *pvParameters)
{
    startCameraServer();
    vTaskDelete(NULL); // Task terminates after starting server
}