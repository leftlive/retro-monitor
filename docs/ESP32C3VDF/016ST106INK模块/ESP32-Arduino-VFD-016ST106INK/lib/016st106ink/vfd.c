#include "vfd.h"

#define Write_DCRAM_CMD     0x20    // Write Data Control RAM Command
#define Write_DCRAM_CMD2    0x1F    // Write Data Control RAM Command
#define Set_Timing_CMD      0xE0    // Set Display Timming Command
#define Set_Dimming_CMD     0xE4    // Write Brightness Control Data Command
#define Light_Normal_CMD    0xE8    // Display Light Normal Operation

#define DEFAULT_BRIGHTNESS 0xff  //默认亮度

static void VFD_SendByte(uint8_t dat) {
    uint8_t i;
    for (i = 0; i < 8; i++) {
        VFD_IO_Write(VFD_PIN_CP, LOW);

        if (dat & 0x01) {
            VFD_IO_Write(VFD_PIN_DA, HIGH);
        }
        else {
            VFD_IO_Write(VFD_PIN_DA, LOW);
        }
        dat = dat >> 1;

        VFD_DelayUs(1);

        VFD_IO_Write(VFD_PIN_CP, HIGH);

        VFD_DelayUs(1);
    }
}

void  VFD_Init(void) {
    VFD_IO_Write(VFD_PIN_CS, HIGH);
    VFD_DelayMs(100);
    VFD_IO_Write(VFD_PIN_RST, LOW);
    VFD_DelayMs(5);
    VFD_IO_Write(VFD_PIN_RST, HIGH);

    VFD_IO_Write(VFD_PIN_CS, LOW);
    VFD_SendByte(Set_Timing_CMD);
    VFD_DelayMs(1);
    VFD_SendByte(0x0F);
    VFD_IO_Write(VFD_PIN_CS, HIGH);

    VFD_DelayMs(1);

    VFD_SetBrightness(DEFAULT_BRIGHTNESS);

    VFD_DelayMs(1);

    VFD_IO_Write(VFD_PIN_CS, LOW);
    VFD_SendByte(Light_Normal_CMD);
    VFD_IO_Write(VFD_PIN_CS, HIGH);
}

void VFD_SetPower(uint8_t on) {
    if (on) {
        VFD_IO_Write(VFD_PIN_EN, HIGH);
    }
    else {
        VFD_IO_Write(VFD_PIN_EN, LOW);
    }
}

void VFD_SetBrightness(uint8_t brightness) {
    if (brightness < 5) {
        brightness = 5; //最低亮度限制
    }
    VFD_IO_Write(VFD_PIN_CS, LOW);
    VFD_SendByte(Set_Dimming_CMD);
    VFD_DelayMs(1);
    VFD_SendByte(brightness);
    VFD_IO_Write(VFD_PIN_CS, HIGH);
}

void VFD_Clear(void) {
    VFD_PrintString(1, "");
    VFD_PrintString(2, "");
}

void VFD_PrintString(uint8_t line, const char* str) {
    if (line > 2) return;
    if (line == 1) {
        //Line-1 MaxStr = 8
        uint8_t len = strlen(str);
        uint8_t i;
        VFD_IO_Write(VFD_PIN_CS, LOW);
        VFD_SendByte(Write_DCRAM_CMD);
        for (i = 0; i < 8; i++) {
            VFD_SendByte(i < len ? str[i] : 0x00);
        }
        VFD_IO_Write(VFD_PIN_CS, HIGH);
    }
    else {
        //Line-1 MaxStr = 16
        uint8_t len = strlen(str);
        uint8_t i;
        VFD_IO_Write(VFD_PIN_CS, LOW);
        VFD_SendByte(Write_DCRAM_CMD2);
        VFD_SendByte(0x00);
        for (i = 0; i < 16; i++) {
            VFD_SendByte(i < len ? str[i] : 0x00);
        }
        VFD_IO_Write(VFD_PIN_CS, HIGH);
    }
}


void VFD_SetIconNative(uint8_t pos, uint8_t col1, uint8_t col2) {
    VFD_IO_Write(VFD_PIN_CS, LOW);
    VFD_SendByte(0x60 | 8 + pos);
    if (col1 && col2) {
        VFD_SendByte(0x03);
    }
    else if (col1 && !col2) {
        VFD_SendByte(0x02);
    }
    else if (!col1 && col2) {
        VFD_SendByte(0x01);
    }
    else {
        VFD_SendByte(0x00);
    }
    VFD_IO_Write(VFD_PIN_CS, HIGH);
}


// void VFD_SetIcon(uint8_t icon, uint8_t on) {
//     VFD_IO_Write(VFD_PIN_CS, LOW);
//     VFD_SendByte(0x6E + 1);
//     VFD_SendByte(0x0F); //1
//     VFD_IO_Write(VFD_PIN_CS, HIGH);

//     VFD_IO_Write(VFD_PIN_CS, LOW);
//     VFD_SendByte(0x6E + 2);
//     VFD_SendByte(0x0F); //1
//     VFD_IO_Write(VFD_PIN_CS, HIGH);

//     VFD_IO_Write(VFD_PIN_CS, LOW);
//     VFD_SendByte(0x6E + 3);
//     VFD_SendByte(0x0F); //1
//     VFD_IO_Write(VFD_PIN_CS, HIGH);

// }