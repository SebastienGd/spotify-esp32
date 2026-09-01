#ifndef DRAW_H
#define DRAW_H

#include <stdint.h>

#include "esp32_hw_i2c.h"
#include "esp_event.h"
#include "u8g2.h"

class OledDrawer {
  public:
    explicit OledDrawer(const u8g2_esp32_i2c_config_t &i2c_config);
    static OledDrawer &oled_drawer();

  private:
    void register_event_handlers();
    static void draw_display_event_handler(void *handler_args, esp_event_base_t base,
                                           int32_t event_id, void *event_data);

    void draw_clear();
    void draw_string(int x, int y, const char *text);
    void draw_websocket_data(const uint8_t *data, int data_len);

    u8g2_t oled_;
    u8g2_esp32_i2c_ctx_t i2c_ctx_;
};

#endif // DRAW_H
