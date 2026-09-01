#include "websocket.h"

#include "esp_log.h"
#include <cstring>

#define WEBSOCKET_URI "ws://192.168.0.159:8000/ws"

static const char *TAG = "websocket";

WebSocketClient::WebSocketClient(esp_websocket_client_config_t config) : config_(config) {
    ESP_LOGI(TAG, "Initializing WebSocket client...");
    client_ = esp_websocket_client_init(&config_);
    if (client_ == nullptr) {
        ESP_LOGE(TAG, "Failed to initialize WebSocket client");
        return;
    }

    register_event_handlers();
    ESP_ERROR_CHECK(esp_websocket_client_start(client_));
    ESP_LOGI(TAG, "WebSocket client started");
}

WebSocketClient &WebSocketClient::websocket_client() {
    static const esp_websocket_client_config_t config = [] {
        esp_websocket_client_config_t client_config = {};
        client_config.uri = WEBSOCKET_URI;
        return client_config;
    }();
    static WebSocketClient client(config);
    return client;
}

void WebSocketClient::register_event_handlers() {
    ESP_ERROR_CHECK(
        esp_websocket_register_events(client_, WEBSOCKET_EVENT_ANY, websocket_event_handler, this));
    ESP_ERROR_CHECK(esp_event_handler_register(APP_EVENTS, SPOTIFY_EVENT_PLAYBACK,
                                               spotify_event_playback_handler, this));
}

void WebSocketClient::websocket_event_handler(void *handler_args, esp_event_base_t base,
                                              int32_t event_id, void *event_data) {
    static_cast<WebSocketClient *>(handler_args)
        ->handle_websocket_event(base, event_id, event_data);
}

void WebSocketClient::spotify_event_playback_handler(void *handler_args, esp_event_base_t, int32_t,
                                                     void *event_data) {
    static_cast<WebSocketClient *>(handler_args)
        ->handle_spotify_playback_event(static_cast<const char *>(event_data));
}

void WebSocketClient::handle_websocket_event(esp_event_base_t event_base, int32_t event_id,
                                             void *event_data) {
    if (event_base != WEBSOCKET_EVENTS) {
        return;
    }

    switch (event_id) {
    case WEBSOCKET_EVENT_CONNECTED:
        ESP_LOGI(TAG, "WebSocket connected");
        break;
    case WEBSOCKET_EVENT_DISCONNECTED:
        ESP_LOGI(TAG, "WebSocket disconnected");
        break;
    case WEBSOCKET_EVENT_DATA: {
        const auto *data = static_cast<const esp_websocket_event_data_t *>(event_data);
        if (data == nullptr || data->data_ptr == nullptr || data->data_len == 0) {
            ESP_LOGI(TAG, "Received empty data event");
            break;
        }
        if (data->data_len > WebSocketInput::FRAMEBUFFER_SIZE) {
            ESP_LOGW(TAG, "WebSocket frame is too large: %d bytes", data->data_len);
            break;
        }

        WebSocketInput input = {};
        input.data_len = data->data_len;
        std::memcpy(input.data, data->data_ptr, input.data_len);
        ESP_ERROR_CHECK(esp_event_post(APP_EVENTS, SOCKET_EVENT_RECEIVED_BIN, &input, sizeof(input),
                                       portMAX_DELAY));
        break;
    }
    case WEBSOCKET_EVENT_ERROR:
        ESP_LOGE(TAG, "WebSocket error");
        break;
    default:
        break;
    }
}

void WebSocketClient::handle_spotify_playback_event(const char *event_data) {
    if (client_ == nullptr || !esp_websocket_client_is_connected(client_)) {
        ESP_LOGW(TAG, "WebSocket client not connected. Cannot send message.");
        return;
    }

    if (event_data == nullptr || event_data[0] == '\0') {
        ESP_LOGW(TAG, "Received an empty Spotify playback event.");
        return;
    }

    esp_websocket_client_send_text(client_, event_data, std::strlen(event_data), portMAX_DELAY);
    ESP_LOGI(TAG, "Sent Spotify playback event: %s", event_data);
}
