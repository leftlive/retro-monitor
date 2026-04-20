#pragma once
#include <ArduinoJson.h>
#include <Arduino.h>
#include <esp_event.h>
#include <esp_timer.h>
#include <esp_wifi.h>
#include <string>

namespace retro_diag {

static std::string last_wifi_event = "boot";
static uint32_t last_wifi_event_ms = 0;
static uint32_t wifi_disconnect_count = 0;
static uint32_t wifi_connect_count = 0;
static bool wifi_event_registered = false;

inline uint32_t now_ms() { return static_cast<uint32_t>(esp_timer_get_time() / 1000ULL); }

inline const char *disconnect_reason_to_str(uint8_t reason) {
  switch (reason) {
    case WIFI_REASON_UNSPECIFIED:
      return "unspecified";
    case WIFI_REASON_AUTH_EXPIRE:
      return "auth_expire";
    case WIFI_REASON_AUTH_LEAVE:
      return "auth_leave";
    case WIFI_REASON_ASSOC_EXPIRE:
      return "assoc_expire";
    case WIFI_REASON_ASSOC_TOOMANY:
      return "assoc_toomany";
    case WIFI_REASON_NOT_AUTHED:
      return "not_authed";
    case WIFI_REASON_NOT_ASSOCED:
      return "not_assoced";
    case WIFI_REASON_ASSOC_LEAVE:
      return "assoc_leave";
    case WIFI_REASON_ASSOC_NOT_AUTHED:
      return "assoc_not_authed";
    case WIFI_REASON_DISASSOC_PWRCAP_BAD:
      return "disassoc_pwrcap";
    case WIFI_REASON_DISASSOC_SUPCHAN_BAD:
      return "disassoc_supchan";
    case WIFI_REASON_IE_INVALID:
      return "ie_invalid";
    case WIFI_REASON_MIC_FAILURE:
      return "mic_failure";
    case WIFI_REASON_4WAY_HANDSHAKE_TIMEOUT:
      return "4way_timeout";
    case WIFI_REASON_GROUP_KEY_UPDATE_TIMEOUT:
      return "groupkey_timeout";
    case WIFI_REASON_IE_IN_4WAY_DIFFERS:
      return "ie_4way_differs";
    case WIFI_REASON_GROUP_CIPHER_INVALID:
      return "group_cipher_invalid";
    case WIFI_REASON_PAIRWISE_CIPHER_INVALID:
      return "pairwise_cipher_invalid";
    case WIFI_REASON_AKMP_INVALID:
      return "akmp_invalid";
    case WIFI_REASON_UNSUPP_RSN_IE_VERSION:
      return "rsn_version";
    case WIFI_REASON_INVALID_RSN_IE_CAP:
      return "rsn_cap_invalid";
    case WIFI_REASON_802_1X_AUTH_FAILED:
      return "8021x_failed";
    case WIFI_REASON_CIPHER_SUITE_REJECTED:
      return "cipher_rejected";
    case WIFI_REASON_BEACON_TIMEOUT:
      return "beacon_timeout";
    case WIFI_REASON_NO_AP_FOUND:
      return "no_ap_found";
    case WIFI_REASON_AUTH_FAIL:
      return "auth_fail";
    case WIFI_REASON_ASSOC_FAIL:
      return "assoc_fail";
    case WIFI_REASON_HANDSHAKE_TIMEOUT:
      return "handshake_timeout";
    case WIFI_REASON_CONNECTION_FAIL:
      return "connection_fail";
    case WIFI_REASON_AP_TSF_RESET:
      return "ap_tsf_reset";
    case WIFI_REASON_ROAMING:
      return "roaming";
    default:
      return "unknown";
  }
}

inline void set_event(const char *event) {
  last_wifi_event = event;
  last_wifi_event_ms = now_ms();
}

inline void wifi_event_handler(void *arg, esp_event_base_t event_base, int32_t event_id, void *event_data) {
  if (event_base != WIFI_EVENT) return;

  if (event_id == WIFI_EVENT_STA_CONNECTED) {
    wifi_connect_count++;
    set_event("connected");
    return;
  }

  if (event_id == WIFI_EVENT_STA_DISCONNECTED) {
    wifi_disconnect_count++;
    auto *it = static_cast<wifi_event_sta_disconnected_t *>(event_data);
    if (it == nullptr) {
      set_event("disconnected");
      return;
    }
    set_event(disconnect_reason_to_str(it->reason));
  }
}

inline void ensure_wifi_event_handler_registered() {
  if (wifi_event_registered) return;
  esp_event_handler_register(WIFI_EVENT, ESP_EVENT_ANY_ID, &wifi_event_handler, nullptr);
  wifi_event_registered = true;
}

}  // namespace retro_diag
