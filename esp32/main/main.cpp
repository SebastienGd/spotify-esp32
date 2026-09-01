#include "esp_err.h"
#include "nvs_flash.h"

#include "button.h"
#include "draw.h"
#include "websocket.h"
#include "wifi.h"

extern "C" void app_main() {
    esp_err_t ret = nvs_flash_init();
    if (ret == ESP_ERR_NVS_NO_FREE_PAGES || ret == ESP_ERR_NVS_NEW_VERSION_FOUND) {
        ESP_ERROR_CHECK(nvs_flash_erase());
        ret = nvs_flash_init();
    }
    ESP_ERROR_CHECK(ret);

    WifiManager::wifi_manager();
    OledDrawer::oled_drawer();
    WebSocketClient::websocket_client();
    ESP_ERROR_CHECK(button_init());
}
