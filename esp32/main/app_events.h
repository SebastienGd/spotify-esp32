#ifndef APP_EVENTS_H
#define APP_EVENTS_H

#include "esp_event.h"

ESP_EVENT_DECLARE_BASE(APP_EVENTS);

typedef enum {
    SPOTIFY_EVENT_PLAYBACK,
    WIFI_EVENT_CONNECTED,
    SOCKET_EVENT_RECEIVED_BIN,
} app_event_id_t;

#endif // APP_EVENTS_H
