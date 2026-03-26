//go:build darwin

package provider

/*
#cgo darwin LDFLAGS: -framework IOKit -framework CoreFoundation
#include <CoreFoundation/CoreFoundation.h>
#include <IOKit/IOKitLib.h>
#include <stdlib.h>
#include <string.h>

enum {
  KERNEL_INDEX_SMC = 2,
  SMC_CMD_READ_BYTES = 5,
  SMC_CMD_READ_KEYINFO = 9
};

typedef struct {
  uint8_t major;
  uint8_t minor;
  uint8_t build;
  uint8_t reserved;
  uint16_t release;
} SMCKeyDataVers;

typedef struct {
  uint16_t version;
  uint16_t length;
  uint32_t cpuPLimit;
  uint32_t gpuPLimit;
  uint32_t memPLimit;
} SMCKeyDataPLimitData;

typedef struct {
  uint32_t dataSize;
  uint32_t dataType;
  uint8_t dataAttributes;
} SMCKeyDataKeyInfo;

typedef struct {
  uint32_t key;
  SMCKeyDataVers vers;
  SMCKeyDataPLimitData pLimitData;
  SMCKeyDataKeyInfo keyInfo;
  uint8_t result;
  uint8_t status;
  uint8_t data8;
  uint32_t data32;
  uint8_t bytes[32];
} SMCKeyData;

typedef struct {
  char key[5];
  uint32_t dataSize;
  char dataType[5];
  uint8_t bytes[32];
} RM_SMCValue;

static uint32_t rm_smc_key_to_uint32(const char *key) {
  return ((uint32_t)key[0] << 24) | ((uint32_t)key[1] << 16) | ((uint32_t)key[2] << 8) | (uint32_t)key[3];
}

static void rm_smc_uint32_to_key(uint32_t value, char *out) {
  out[0] = (value >> 24) & 0xFF;
  out[1] = (value >> 16) & 0xFF;
  out[2] = (value >> 8) & 0xFF;
  out[3] = value & 0xFF;
  out[4] = '\0';
}

static kern_return_t rm_smc_call(io_connect_t conn, SMCKeyData *input, SMCKeyData *output) {
  size_t outSize = sizeof(SMCKeyData);
  return IOConnectCallStructMethod(conn, KERNEL_INDEX_SMC, input, sizeof(SMCKeyData), output, &outSize);
}

static int rm_smc_open(io_connect_t *conn) {
  mach_port_t masterPort;
  kern_return_t result = IOMasterPort(MACH_PORT_NULL, &masterPort);
  if (result != kIOReturnSuccess) {
    return result;
  }

  CFMutableDictionaryRef matching = IOServiceMatching("AppleSMC");
  if (!matching) {
    return -1;
  }

  io_iterator_t iterator;
  result = IOServiceGetMatchingServices(masterPort, matching, &iterator);
  if (result != kIOReturnSuccess) {
    return result;
  }

  io_service_t device = IOIteratorNext(iterator);
  IOObjectRelease(iterator);
  if (!device) {
    return -2;
  }

  result = IOServiceOpen(device, mach_task_self(), 0, conn);
  IOObjectRelease(device);
  return result;
}

static int rm_smc_read(io_connect_t conn, const char *key, RM_SMCValue *value) {
  SMCKeyData input;
  SMCKeyData output;
  SMCKeyDataKeyInfo keyInfo;
  memset(&input, 0, sizeof(input));
  memset(&output, 0, sizeof(output));

  input.key = rm_smc_key_to_uint32(key);
  input.data8 = SMC_CMD_READ_KEYINFO;
  if (rm_smc_call(conn, &input, &output) != kIOReturnSuccess) {
    return -1;
  }
  keyInfo = output.keyInfo;

  memset(&input, 0, sizeof(input));
  input.key = rm_smc_key_to_uint32(key);
  input.keyInfo.dataSize = keyInfo.dataSize;
  input.data8 = SMC_CMD_READ_BYTES;
  if (rm_smc_call(conn, &input, &output) != kIOReturnSuccess) {
    return -2;
  }

  memset(value, 0, sizeof(RM_SMCValue));
  strncpy(value->key, key, 4);
  value->key[4] = '\0';
  value->dataSize = keyInfo.dataSize;
  rm_smc_uint32_to_key(keyInfo.dataType, value->dataType);
  memcpy(value->bytes, output.bytes, 32);
  return 0;
}
*/
import "C"

import (
	"encoding/binary"
	"errors"
	"fmt"
	"math"
	"unsafe"
)

type appleSMC struct {
	conn C.io_connect_t
}

type smcValue struct {
	dataSize int
	dataType string
	bytes    []byte
}

func newAppleSMC() (*appleSMC, error) {
	var conn C.io_connect_t
	if result := C.rm_smc_open(&conn); result != 0 {
		return nil, errors.New("failed to open AppleSMC")
	}
	return &appleSMC{conn: conn}, nil
}

func (s *appleSMC) Close() {
	if s == nil || s.conn == 0 {
		return
	}
	C.IOServiceClose(s.conn)
	s.conn = 0
}

func (s *appleSMC) readKey(key string) (*smcValue, error) {
	if len(key) != 4 {
		return nil, errors.New("invalid SMC key")
	}

	ckey := C.CString(key)
	defer C.free(unsafe.Pointer(ckey))

	var value C.RM_SMCValue
	if result := C.rm_smc_read(s.conn, ckey, &value); result != 0 {
		return nil, errors.New("SMC read failed")
	}

	dataSize := int(value.dataSize)
	if dataSize < 0 || dataSize > 32 {
		return nil, errors.New("invalid SMC data size")
	}

	dataType := C.GoString(&value.dataType[0])
	raw := C.GoBytes(unsafe.Pointer(&value.bytes[0]), C.int(dataSize))
	return &smcValue{dataSize: dataSize, dataType: dataType, bytes: raw}, nil
}

func (s *appleSMC) readNumeric(key string) *float64 {
	value, err := s.readKey(key)
	if err != nil || value.dataSize == 0 {
		return nil
	}
	v, ok := decodeSMCNumeric(value.dataType, value.bytes)
	if !ok {
		return nil
	}
	return f64(round1(v))
}

func (s *appleSMC) cpuTemperature() *float64 {
	return s.readNumeric("TC0P")
}

func (s *appleSMC) cpuPower() *float64 {
	for _, key := range []string{"PCPT", "PCTR", "PCPR", "PCPC", "PC0C", "PCAM"} {
		if value := s.readNumeric(key); value != nil {
			return value
		}
	}
	return nil
}

func (s *appleSMC) fanCount() int {
	value, err := s.readKey("FNum")
	if err != nil || value.dataSize == 0 {
		return 0
	}

	total := 0
	for _, b := range value.bytes {
		total = (total << 8) | int(b)
	}
	return total
}

func (s *appleSMC) fanSpeed(index int) *float64 {
	key := fmt.Sprintf("F%dAc", index)
	value, err := s.readKey(key)
	if err != nil || value.dataSize < 2 {
		return nil
	}

	switch value.dataType {
	case "fpe2":
		raw := int(value.bytes[0])<<8 | int(value.bytes[1])
		return f64(round1(float64(raw) / 4.0))
	case "flt ":
		if len(value.bytes) < 4 {
			return nil
		}
		bits := binary.LittleEndian.Uint32(value.bytes[:4])
		return f64(round1(float64(math.Float32frombits(bits))))
	default:
		return nil
	}
}

func decodeSMCNumeric(dataType string, payload []byte) (float64, bool) {
	if len(payload) == 0 {
		return 0, false
	}

	switch dataType {
	case "sp78":
		if len(payload) < 2 {
			return 0, false
		}
		raw := int16(binary.BigEndian.Uint16(payload[:2]))
		return float64(raw) / 256.0, true
	case "sp96":
		if len(payload) < 2 {
			return 0, false
		}
		raw := binary.BigEndian.Uint16(payload[:2])
		return float64(raw) / 64.0, true
	case "flt ":
		if len(payload) < 4 {
			return 0, false
		}
		return float64(math.Float32frombits(binary.LittleEndian.Uint32(payload[:4]))), true
	default:
		return 0, false
	}
}
