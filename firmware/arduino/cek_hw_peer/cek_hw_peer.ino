/*
 * cek-hw MCU Peer — apply-only. NO mint. NO Cap verify.
 *
 * JSON floor, one object per line, same shapes as cek-surface carriers:
 *   {"type":"apply","result":{"kind":"ok","ops":[...]}}
 *   {"type":"hello"}
 *   {"type":"done"}
 *
 * Host (cek-host + cek-hw.project_action) already verified the Cap.
 * If kind is authority_refusal / dispatch_error, we do not touch pins.
 *
 * Watchdog: if no landed apply within WATCHDOG_MS, pins go SAFE_LEVEL.
 * That is a local interlock, not a Cap.
 *
 * Port of cek_hw.peer.HwPeer.apply. Do not grow Host duties here.
 */

#ifndef CEK_HW_LED_PIN
#define CEK_HW_LED_PIN 13
#endif
#ifndef WATCHDOG_MS
#define WATCHDOG_MS 1500
#endif
#ifndef SAFE_LEVEL
#define SAFE_LEVEL LOW
#endif
#ifndef BAUD
#define BAUD 115200
#endif

const int KNOWN_PINS[] = {3, 7, 13};
const int KNOWN_COUNT = 3;

char line[384];
uint16_t llen = 0;
unsigned long lastPet = 0;
bool tripped = false;

bool knownPin(int pin) {
  for (int i = 0; i < KNOWN_COUNT; i++) if (KNOWN_PINS[i] == pin) return true;
  return false;
}

void safeState() {
  for (int i = 0; i < KNOWN_COUNT; i++) digitalWrite(KNOWN_PINS[i], SAFE_LEVEL);
}

bool kindIsRefuse(const char *s) {
  return strstr(s, "\"authority_refusal\"") || strstr(s, "\"dispatch_error\"");
}

int extractInt(const char *s, const char *key) {
  const char *p = strstr(s, key);
  if (!p) return -1;
  p += strlen(key);
  while (*p && (*p == ':' || *p == ' ' || *p == '\"')) p++;
  return atoi(p);
}

bool extractQuoted(const char *s, const char *key, char *out, size_t n) {
  const char *p = strstr(s, key);
  if (!p) return false;
  p = strchr(p + strlen(key), '\"');
  if (!p) return false;
  p++;
  size_t i = 0;
  while (*p && *p != '\"' && i + 1 < n) out[i++] = *p++;
  out[i] = 0;
  return true;
}

/* Very small JSON floor: find each "hw.gpio" then nearby pin/level. */
int applyLine(const char *s) {
  if (kindIsRefuse(s)) return 0;
  if (!strstr(s, "\"ok\"")) return 0;
  int landed = 0;
  const char *p = s;
  while ((p = strstr(p, "\"hw.gpio\"")) != NULL) {
    const char *name = strstr(p, "\"set\"");
    if (!name || name > p + 48) { p += 8; continue; }
    int pin = extractInt(p, "\"pin\"");
    int level = extractInt(p, "\"level\"");
    if (pin < 0 || level < 0 || !knownPin(pin)) return -1;
    pinMode(pin, OUTPUT);
    digitalWrite(pin, level ? HIGH : LOW);
    landed++;
    p += 8;
  }
  if (strstr(s, "\"hw.safe\"") && strstr(s, "\"state\"")) {
    safeState();
    landed++;
  }
  return landed;
}

void replyApplied(int landed) {
  Serial.print("{\"type\":\"applied\",\"receipt\":{\"landed_count\":");
  Serial.print(landed < 0 ? 0 : landed);
  Serial.print(",\"failed_count\":");
  Serial.print(landed < 0 ? 1 : 0);
  Serial.println("}}");
}

void setup() {
  for (int i = 0; i < KNOWN_COUNT; i++) {
    pinMode(KNOWN_PINS[i], OUTPUT);
    digitalWrite(KNOWN_PINS[i], SAFE_LEVEL);
  }
  Serial.begin(BAUD);
  lastPet = millis();
  Serial.println("{\"type\":\"manifest\",\"manifest\":{\"profile\":\"hw-v1\",\"mint\":false}}");
}

void loop() {
  while (Serial.available()) {
    char c = (char)Serial.read();
    if (c == '\n' || c == '\r') {
      if (llen) {
        line[llen] = 0;
        if (strstr(line, "\"hello\"")) {
          Serial.println("{\"type\":\"manifest\",\"manifest\":{\"profile\":\"hw-v1\",\"mint\":false}}");
        } else if (strstr(line, "\"apply\"")) {
          int n = applyLine(line);
          if (n > 0) {
            lastPet = millis();
            tripped = false;
          }
          replyApplied(n);
        }
        llen = 0;
      }
    } else if (llen + 1 < sizeof(line)) {
      line[llen++] = c;
    } else {
      llen = 0;
    }
  }
  if (!tripped && (millis() - lastPet) > (unsigned long)WATCHDOG_MS) {
    safeState();
    tripped = true;
    Serial.println("{\"type\":\"event\",\"name\":\"hw.watchdog\",\"payload\":{\"safe\":true}}");
  }
}
