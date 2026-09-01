#include "button.h"

#include <cstring>

#include "app_events.h"
#include "esp_log.h"

namespace {

constexpr gpio_num_t SKIP_SONG_BUTTON_GPIO = GPIO_NUM_32;
constexpr gpio_num_t PREVIOUS_SONG_BUTTON_GPIO = GPIO_NUM_33;
constexpr gpio_num_t PLAY_SONG_BUTTON_GPIO = GPIO_NUM_25;

constexpr char SKIP_SONG_EVENT[] = "{\"event\": \"skip_song\"}";
constexpr char PREVIOUS_SONG_EVENT[] = "{\"event\": \"previous_song\"}";
constexpr char PLAY_SONG_EVENT[] = "{\"event\": \"play_song\"}";

static const char *TAG = "button";

}

PlaybackButton::PlaybackButton(gpio_num_t gpio_num, const char *event_data)
    : gpio_num_(gpio_num), event_data_(event_data) {}

esp_err_t PlaybackButton::initialize() {
    const button_config_t button_config = {};
    const button_gpio_config_t gpio_config = {
        .gpio_num = gpio_num_,
        .active_level = 0,
        .enable_power_save = true,
        .disable_pull = false,
    };

    esp_err_t error = iot_button_new_gpio_device(&button_config, &gpio_config, &handle_);
    if (error != ESP_OK) {
        ESP_LOGE(TAG, "Failed to create button on GPIO %d: %s", gpio_num_, esp_err_to_name(error));
        return error;
    }

    return iot_button_register_cb(handle_, BUTTON_SINGLE_CLICK, nullptr, single_click_handler,
                                  this);
}

void PlaybackButton::single_click_handler(void *, void *user_data) {
    const auto *button = static_cast<const PlaybackButton *>(user_data);
    if (button == nullptr || button->event_data_ == nullptr) {
        ESP_LOGW(TAG, "Button is missing event data");
        return;
    }

    ESP_LOGI(TAG, "Posting Spotify playback event: %s", button->event_data_);
    ESP_ERROR_CHECK(esp_event_post(APP_EVENTS, SPOTIFY_EVENT_PLAYBACK, button->event_data_,
                                   std::strlen(button->event_data_) + 1, portMAX_DELAY));
}

esp_err_t button_init() {
    static PlaybackButton skip_song_button(SKIP_SONG_BUTTON_GPIO, SKIP_SONG_EVENT);
    static PlaybackButton previous_song_button(PREVIOUS_SONG_BUTTON_GPIO, PREVIOUS_SONG_EVENT);
    static PlaybackButton play_song_button(PLAY_SONG_BUTTON_GPIO, PLAY_SONG_EVENT);

    esp_err_t error = skip_song_button.initialize();
    if (error != ESP_OK) {
        return error;
    }

    error = previous_song_button.initialize();
    if (error != ESP_OK) {
        return error;
    }

    return play_song_button.initialize();
}
