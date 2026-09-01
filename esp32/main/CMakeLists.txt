idf_component_register(
    SRCS "main.cpp" "wifi.cpp" "websocket.cpp" "draw.cpp" "button.cpp" "app_event.c"
    INCLUDE_DIRS "."
    REQUIRES
        esp_wifi
        esp_event
        esp_netif
        nvs_flash
        esp_websocket_client
        nixy4__u8g2
        esp_driver_gpio
        espressif__button
)
