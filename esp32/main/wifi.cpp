#include "wifi.h"

#include <cstring>

#include "app_events.h"
#include "esp_log.h"
#include "esp_netif.h"
#include "secrets.h"

static const char *TAG = "wifi";

WifiManager::WifiManager(const wifi_init_config_t &init_config, const wifi_config_t &config)
    : wifi_init_config_(init_config), wifi_config_(config) {
    ESP_ERROR_CHECK(esp_netif_init());
    ESP_ERROR_CHECK(esp_event_loop_create_default());
    esp_netif_create_default_wifi_sta();
    ESP_ERROR_CHECK(esp_wifi_init(&wifi_init_config_));

    register_event_handlers();
    ESP_ERROR_CHECK(esp_wifi_set_mode(WIFI_MODE_STA));
    ESP_ERROR_CHECK(esp_wifi_set_config(WIFI_IF_STA, &wifi_config_));
    ESP_ERROR_CHECK(esp_wifi_start());
}

WifiManager &WifiManager::wifi_manager() {
    static const wifi_init_config_t init_config = WIFI_INIT_CONFIG_DEFAULT();
    static const wifi_config_t config = [] {
        wifi_config_t wifi_config = {};
        std::strncpy(reinterpret_cast<char *>(wifi_config.sta.ssid), WIFI_SSID,
                     sizeof(wifi_config.sta.ssid) - 1);
        std::strncpy(reinterpret_cast<char *>(wifi_config.sta.password), WIFI_PASS,
                     sizeof(wifi_config.sta.password) - 1);
        return wifi_config;
    }();
    static WifiManager manager(init_config, config);
    return manager;
}

void WifiManager::register_event_handlers() {
    ESP_ERROR_CHECK(
        esp_event_handler_register(WIFI_EVENT, ESP_EVENT_ANY_ID, wifi_event_handler, nullptr));
    ESP_ERROR_CHECK(
        esp_event_handler_register(IP_EVENT, IP_EVENT_STA_GOT_IP, wifi_event_handler, nullptr));
}

void WifiManager::wifi_event_handler(void *, esp_event_base_t event_base, int32_t event_id,
                                     void *) {
    if (event_base == WIFI_EVENT && event_id == WIFI_EVENT_STA_START) {
        esp_wifi_connect();
    } else if (event_base == WIFI_EVENT && event_id == WIFI_EVENT_STA_DISCONNECTED) {
        ESP_LOGI(TAG, "Disconnected. Reconnecting...");
        esp_wifi_connect();
    } else if (event_base == IP_EVENT && event_id == IP_EVENT_STA_GOT_IP) {
        ESP_ERROR_CHECK(
            esp_event_post(APP_EVENTS, WIFI_EVENT_CONNECTED, nullptr, 0, portMAX_DELAY));
    }
}
