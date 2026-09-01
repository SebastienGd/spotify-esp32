#ifndef BUTTON_H
#define BUTTON_H

#include "button_gpio.h"
#include "driver/gpio.h"
#include "esp_err.h"
#include "iot_button.h"

class PlaybackButton {
  public:
    PlaybackButton(gpio_num_t gpio_num, const char *event_data);
    esp_err_t initialize();

  private:
    static void single_click_handler(void *button_handle, void *user_data);

    gpio_num_t gpio_num_;
    const char *event_data_;
    button_handle_t handle_ = nullptr;
};

esp_err_t button_init();

#endif // BUTTON_H
