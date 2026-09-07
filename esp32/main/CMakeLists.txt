set(ESP32_WIFI_SSID "$ENV{ESP32_WIFI_SSID}")
set(ESP32_WIFI_PASSWORD "$ENV{ESP32_WIFI_PASSWORD}")
set(ESP32_WEBSOCKET_URI "$ENV{ESP32_WEBSOCKET_URI}")

foreach(CONFIG_VALUE ESP32_WIFI_SSID ESP32_WIFI_PASSWORD ESP32_WEBSOCKET_URI)
    if("${${CONFIG_VALUE}}" STREQUAL "")
        message(FATAL_ERROR "${CONFIG_VALUE} must be set before building the firmware")
    endif()

    string(REPLACE "\\" "\\\\" ${CONFIG_VALUE}_ESCAPED "${${CONFIG_VALUE}}")
    string(REPLACE "\"" "\\\"" ${CONFIG_VALUE}_ESCAPED "${${CONFIG_VALUE}_ESCAPED}")
endforeach()

configure_file(config.h.in generated/config.h @ONLY)

idf_component_register(
    SRCS "main.cpp" "wifi.cpp" "websocket.cpp" "draw.cpp" "button.cpp" "app_event.c"
    INCLUDE_DIRS "." "${CMAKE_CURRENT_BINARY_DIR}/generated"
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
