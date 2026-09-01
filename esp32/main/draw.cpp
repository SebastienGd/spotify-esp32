#include "draw.h"

#include "app_events.h"
#include "esp_err.h"
#include "esp_log.h"
#include "websocket.h"

static const char *TAG = "draw";

#define OLED_ADDRESS 0x3C

OledDrawer::OledDrawer(const u8g2_esp32_i2c_config_t &i2c_config) : i2c_ctx_{} {
    ESP_LOGI(TAG, "Initializing OLED display...");

    i2c_ctx_.cfg = i2c_config;
    ESP_ERROR_CHECK(u8g2_esp32_i2c_set_default_context(&i2c_ctx_));

    u8g2_Setup_ssd1309_i2c_128x64_noname2_f(&oled_, U8G2_R0, u8x8_byte_esp32_hw_i2c,
                                            u8x8_gpio_and_delay_esp32_i2c);
    u8x8_SetI2CAddress(&oled_.u8x8, OLED_ADDRESS << 1);

    u8g2_InitDisplay(&oled_);
    u8g2_SetPowerSave(&oled_, 0);

    register_event_handlers();
    ESP_LOGI(TAG, "OLED display initialized");
}

OledDrawer &OledDrawer::oled_drawer() {
    static OledDrawer oled_drawer(U8G2_ESP32_I2C_CONFIG_DEFAULT());
    return oled_drawer;
}

void OledDrawer::register_event_handlers() {
    ESP_ERROR_CHECK(esp_event_handler_register(APP_EVENTS, SOCKET_EVENT_RECEIVED_BIN,
                                               draw_display_event_handler, this));
}

void OledDrawer::draw_display_event_handler(void *handler_args, esp_event_base_t, int32_t,
                                            void *event_data) {
    const auto *input = static_cast<const WebSocketInput *>(event_data);
    if (input == nullptr) {
        ESP_LOGW(TAG, "Received empty WebSocket display event");
        return;
    }

    static_cast<OledDrawer *>(handler_args)->draw_websocket_data(input->data, input->data_len);
}

void OledDrawer::draw_clear() { u8g2_ClearBuffer(&oled_); }

void OledDrawer::draw_string(int x, int y, const char *text) {
    u8g2_SetFont(&oled_, u8g2_font_ncenB14_tr);
    u8g2_DrawStr(&oled_, x, y, text);
    u8g2_SendBuffer(&oled_);
}

void OledDrawer::draw_websocket_data(const uint8_t *data, int data_len) {
    ESP_LOGI(TAG, "Drawing WebSocket data (%d bytes) to OLED", data_len);
    if (data == nullptr || data_len < 1024) {
        ESP_LOGW(TAG, "Invalid framebuffer size: %d", data_len);
        return;
    }

    draw_clear();
    for (int y = 0; y < 64; y++) {
        for (int x = 0; x < 128; x++) {
            const int byte_idx = y * 16 + (x / 8);
            const int bit_pos = x % 8;
            const uint8_t pixel = (data[byte_idx] >> bit_pos) & 0x01;

            if (pixel) {
                u8g2_DrawPixel(&oled_, x, y);
            }
        }
    }

    u8g2_SendBuffer(&oled_);
}
