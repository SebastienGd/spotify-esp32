#ifndef WEBSOCKET_H
#define WEBSOCKET_H

#include <stdint.h>

#include "app_events.h"

#include "esp_websocket_client.h"

struct WebSocketInput {
    static constexpr int FRAMEBUFFER_SIZE = 1024;

    uint8_t data[FRAMEBUFFER_SIZE];
    int data_len;
};

class WebSocketClient {
  public:
    explicit WebSocketClient(esp_websocket_client_config_t config);
    static WebSocketClient &websocket_client();

  private:
    void register_event_handlers();
    static void websocket_event_handler(void *handler_args, esp_event_base_t base, int32_t event_id,
                                        void *event_data);
    static void spotify_event_playback_handler(void *handler_args, esp_event_base_t base,
                                               int32_t event_id, void *event_data);

    void handle_websocket_event(esp_event_base_t event_base, int32_t event_id, void *event_data);
    void handle_spotify_playback_event(const char *event_data);

    esp_websocket_client_config_t config_;
    esp_websocket_client_handle_t client_;
};

#endif // WEBSOCKET_H
