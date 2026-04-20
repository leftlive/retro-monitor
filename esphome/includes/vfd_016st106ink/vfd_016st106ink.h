#pragma once

#include <Arduino.h>
#include <cstring>

#ifndef VFD_PIN_RST
#define VFD_PIN_RST 0
#endif

#ifndef VFD_PIN_CS
#define VFD_PIN_CS 1
#endif

#ifndef VFD_PIN_CP
#define VFD_PIN_CP 12
#endif

#ifndef VFD_PIN_DA
#define VFD_PIN_DA 18
#endif

#ifndef VFD_PIN_EN
#define VFD_PIN_EN 19
#endif

namespace vfd_016st106ink {

static constexpr uint8_t WRITE_DCRAM_CMD_LINE_1 = 0x20;
static constexpr uint8_t WRITE_DCRAM_CMD_LINE_2 = 0x1F;
static constexpr uint8_t WRITE_CGRAM_CMD = 0x40;
static constexpr uint8_t SET_TIMING_CMD = 0xE0;
static constexpr uint8_t SET_DIMMING_CMD = 0xE4;
static constexpr uint8_t LIGHT_NORMAL_CMD = 0xE8;

inline void write_pin(uint8_t pin, bool high) {
  digitalWrite(pin, high ? HIGH : LOW);
}

inline void send_byte(uint8_t data) {
  for (uint8_t i = 0; i < 8; i++) {
    write_pin(VFD_PIN_CP, false);
    write_pin(VFD_PIN_DA, (data & 0x01) != 0);
    data >>= 1;
    delayMicroseconds(1);
    write_pin(VFD_PIN_CP, true);
    delayMicroseconds(1);
  }
}

inline void set_power(bool on) {
  write_pin(VFD_PIN_EN, on);
}

inline void set_brightness(uint8_t brightness) {
  if (brightness < 5) brightness = 5;
  write_pin(VFD_PIN_CS, false);
  send_byte(SET_DIMMING_CMD);
  delay(1);
  send_byte(brightness);
  write_pin(VFD_PIN_CS, true);
}

inline void print_line_bytes(uint8_t line, const uint8_t *data, uint8_t length) {
  if (line == 1) {
    write_pin(VFD_PIN_CS, false);
    send_byte(WRITE_DCRAM_CMD_LINE_1);
    for (uint8_t i = 0; i < 16; i++) {
      send_byte(i < length ? data[i] : 0x20);
    }
    write_pin(VFD_PIN_CS, true);
    return;
  }

  if (line == 2) {
    write_pin(VFD_PIN_CS, false);
    send_byte(WRITE_DCRAM_CMD_LINE_2);
    send_byte(0x00);
    for (uint8_t i = 0; i < 16; i++) {
      send_byte(i < length ? data[i] : 0x20);
    }
    write_pin(VFD_PIN_CS, true);
  }
}

inline void print_line(uint8_t line, const char *text) {
  print_line_bytes(line, reinterpret_cast<const uint8_t *>(text), strlen(text));
}

inline void clear() {
  print_line(1, "");
  print_line(2, "");
}

inline void set_grid_icon(uint8_t grid, bool ad2_top, bool ad1_bottom, bool ad3 = false, bool ad4 = false) {
  if (grid < 1 || grid > 16) return;
  write_pin(VFD_PIN_CS, false);
  send_byte(0x60 | (grid - 1));
  uint8_t data = 0x00;
  if (ad1_bottom) data |= 0x01; // AD1 (Bottom word: TUNED, SP B, SLEEP, Random)
  if (ad2_top)    data |= 0x02; // AD2 (Top word: STEREO, SP A, MUTE, Loop)
  if (ad3)        data |= 0x04; // AD3 (1)
  if (ad4)        data |= 0x08; // AD4 (F)
  send_byte(data);
  write_pin(VFD_PIN_CS, true);
}

inline void write_cgram(uint8_t address, const uint8_t cols[5]) {
  write_pin(VFD_PIN_CS, false);
  send_byte(WRITE_CGRAM_CMD | (address & 0x07));
  for (uint8_t i = 0; i < 5; i++) {
    send_byte(cols[i] & 0x7F);
  }
  write_pin(VFD_PIN_CS, true);
  delayMicroseconds(4);
}

inline void write_cgram_bitmap(uint8_t address, const uint8_t bitmap_rows[5]) {
  uint8_t cols[5] = {0, 0, 0, 0, 0};

  // The controller expects 5 bytes of column data for a 5x7 character cell.
  // Our design input is a 5x5 bitmap; shift it down by 2 rows so the glyph
  // sits on the bottom edge of the character box instead of floating.
  for (uint8_t col = 0; col < 5; col++) {
    uint8_t packed = 0;
    for (uint8_t row = 0; row < 5; row++) {
      const bool on = (bitmap_rows[row] & (1U << (4 - col))) != 0;
      if (on) {
        packed |= (1U << (row + 2));
      }
    }
    cols[col] = packed;
  }

  write_cgram(address, cols);
}

inline void write_cgram_7x5(uint8_t address, const uint8_t bitmap_rows[7]) {
  uint8_t cols[5] = {0, 0, 0, 0, 0};
  for (uint8_t col = 0; col < 5; col++) {
    uint8_t packed = 0;
    for (uint8_t row = 0; row < 7; row++) {
      const bool on = (bitmap_rows[row] & (1U << (4 - col))) != 0;
      if (on) {
        packed |= (1U << row);
      }
    }
    cols[col] = packed;
  }
  write_cgram(address, cols);
}

inline void load_retro_glyphs() {
  // 5x5 retro glyphs - width 5, single-pixel thickness
  static const uint8_t GLYPH_C[5] = {
    0b11110,
    0b10000,
    0b10000,
    0b10000,
    0b11110,
  };
  static const uint8_t GLYPH_P[5] = {
    0b11110,
    0b10010,
    0b11110,
    0b10000,
    0b10000,
  };
  static const uint8_t GLYPH_U[5] = {
    0b10010,
    0b10010,
    0b10010,
    0b10010,
    0b11110,
  };
  static const uint8_t GLYPH_G[5] = {
    0b11110,
    0b10000,
    0b10110,
    0b10010,
    0b11110,
  };
  // 第一行和第二行的右侧分隔线 (7像素高)
  static const uint8_t GLYPH_SEP_BLINK_ON[7] = {
    0b00001,
    0b00001,
    0b00001,
    0b00001,
    0b00001,
    0b11001, // 左下角2x2方块 + 右侧竖线
    0b11001,
  };
  static const uint8_t GLYPH_SEP_BLINK_OFF[7] = {
    0b00001,
    0b00001,
    0b00001,
    0b00001,
    0b00001,
    0b00001, // 纯右侧竖线
    0b00001,
  };
  static const uint8_t GLYPH_DEGC[5] = {
    0b10111,
    0b00100,
    0b00100,
    0b00100,
    0b00111,
  };
  static const uint8_t GLYPH_PWR[5] = {
    0b00110,
    0b01100,
    0b11111,
    0b00110,
    0b01100,
  };

  write_cgram_bitmap(0, GLYPH_C);
  write_cgram_bitmap(1, GLYPH_P);
  write_cgram_bitmap(2, GLYPH_U);
  write_cgram_bitmap(3, GLYPH_G);
  write_cgram_7x5(4, GLYPH_SEP_BLINK_ON);
  write_cgram_bitmap(5, GLYPH_DEGC);
  write_cgram_bitmap(6, GLYPH_PWR);
  write_cgram_7x5(7, GLYPH_SEP_BLINK_OFF);
}

inline void init_pins() {
  pinMode(VFD_PIN_RST, OUTPUT);
  pinMode(VFD_PIN_CS, OUTPUT);
  pinMode(VFD_PIN_CP, OUTPUT);
  pinMode(VFD_PIN_DA, OUTPUT);
  pinMode(VFD_PIN_EN, OUTPUT_OPEN_DRAIN);
}

inline void init_display() {
  write_pin(VFD_PIN_CS, true);
  delay(100);
  write_pin(VFD_PIN_RST, false);
  delay(5);
  write_pin(VFD_PIN_RST, true);

  write_pin(VFD_PIN_CS, false);
  send_byte(SET_TIMING_CMD);
  delay(1);
  send_byte(0x0F);
  write_pin(VFD_PIN_CS, true);

  delay(1);
  set_brightness(0xFF);
  delay(1);

  write_pin(VFD_PIN_CS, false);
  send_byte(LIGHT_NORMAL_CMD);
  write_pin(VFD_PIN_CS, true);
}

inline void begin(uint8_t brightness = 0xFF) {
  init_pins();
  set_power(true);
  init_display();
  set_brightness(brightness);
  load_retro_glyphs();
  clear();
}

}  // namespace vfd_016st106ink
