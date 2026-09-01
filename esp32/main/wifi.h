#ifndef WIFI_H
#define WIFI_H

#include "esp_event.h"
#include "esp_wifi.h"

class WifiManager {
  public:
    explicit WifiManager(const wifi_init_config_t &init_config, const wifi_config_t &config);

    static WifiManager &wifi_manager();

  private:
    void register_event_handlers();
    static void wifi_event_handler(void *handler_args, esp_event_base_t event_base,
                                   int32_t event_id, void *event_data);

    wifi_init_config_t wifi_init_config_;
    wifi_config_t wifi_config_;
};

#endif // WIFI_H
