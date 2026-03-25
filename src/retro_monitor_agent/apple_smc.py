from __future__ import annotations

import ctypes
import ctypes.util
import struct
from typing import Optional


_IOKIT_PATH = ctypes.util.find_library("IOKit")
if not _IOKIT_PATH:
    raise RuntimeError("IOKit framework not found")

_LIBC_PATH = ctypes.util.find_library("c")
if not _LIBC_PATH:
    raise RuntimeError("libc not found")

_iokit = ctypes.cdll.LoadLibrary(_IOKIT_PATH)
_libc = ctypes.cdll.LoadLibrary(_LIBC_PATH)

_KERNEL_INDEX_SMC = 2
_SMC_CMD_READ_BYTES = 5
_SMC_CMD_READ_KEYINFO = 9
_K_IORETURN_SUCCESS = 0

_KEY_CPU_TEMP = "TC0P"
_KEY_FAN_NUM = "FNum"
_KEY_FAN_SPEED = "F%dAc"
_KEY_CPU_POWER_CANDIDATES = ("PCPT", "PCTR", "PCPR", "PCPC", "PC0C", "PCAM")
_KEY_SYSTEM_POWER_CANDIDATES = ("PSTR", "PDTR")


class _SMCKeyDataVers(ctypes.Structure):
    _fields_ = [
        ("major", ctypes.c_uint8),
        ("minor", ctypes.c_uint8),
        ("build", ctypes.c_uint8),
        ("reserved", ctypes.c_uint8),
        ("release", ctypes.c_uint16),
    ]


class _SMCKeyDataPLimitData(ctypes.Structure):
    _fields_ = [
        ("version", ctypes.c_uint16),
        ("length", ctypes.c_uint16),
        ("cpuPLimit", ctypes.c_uint32),
        ("gpuPLimit", ctypes.c_uint32),
        ("memPLimit", ctypes.c_uint32),
    ]


class _SMCKeyDataKeyInfo(ctypes.Structure):
    _fields_ = [
        ("dataSize", ctypes.c_uint32),
        ("dataType", ctypes.c_uint32),
        ("dataAttributes", ctypes.c_uint8),
    ]


class _SMCKeyData(ctypes.Structure):
    _fields_ = [
        ("key", ctypes.c_uint32),
        ("vers", _SMCKeyDataVers),
        ("pLimitData", _SMCKeyDataPLimitData),
        ("keyInfo", _SMCKeyDataKeyInfo),
        ("result", ctypes.c_uint8),
        ("status", ctypes.c_uint8),
        ("data8", ctypes.c_uint8),
        ("data32", ctypes.c_uint32),
        ("bytes", ctypes.c_uint8 * 32),
    ]


class SMCValue(ctypes.Structure):
    _fields_ = [
        ("key", ctypes.c_char * 5),
        ("dataSize", ctypes.c_uint32),
        ("dataType", ctypes.c_char * 5),
        ("bytes", ctypes.c_uint8 * 32),
    ]


_iokit.IOMasterPort.argtypes = [ctypes.c_uint32, ctypes.POINTER(ctypes.c_uint)]
_iokit.IOMasterPort.restype = ctypes.c_int
_iokit.IOServiceMatching.argtypes = [ctypes.c_char_p]
_iokit.IOServiceMatching.restype = ctypes.c_void_p
_iokit.IOServiceGetMatchingServices.argtypes = [ctypes.c_uint, ctypes.c_void_p, ctypes.POINTER(ctypes.c_uint)]
_iokit.IOServiceGetMatchingServices.restype = ctypes.c_int
_iokit.IOIteratorNext.argtypes = [ctypes.c_uint]
_iokit.IOIteratorNext.restype = ctypes.c_uint
_iokit.IOObjectRelease.argtypes = [ctypes.c_uint]
_iokit.IOObjectRelease.restype = ctypes.c_int
_iokit.IOServiceOpen.argtypes = [ctypes.c_uint, ctypes.c_uint, ctypes.c_uint32, ctypes.POINTER(ctypes.c_uint)]
_iokit.IOServiceOpen.restype = ctypes.c_int
_iokit.IOServiceClose.argtypes = [ctypes.c_uint]
_iokit.IOServiceClose.restype = ctypes.c_int
_iokit.IOConnectCallStructMethod.argtypes = [
    ctypes.c_uint,
    ctypes.c_uint32,
    ctypes.c_void_p,
    ctypes.c_size_t,
    ctypes.c_void_p,
    ctypes.POINTER(ctypes.c_size_t),
]
_iokit.IOConnectCallStructMethod.restype = ctypes.c_int
_libc.mach_task_self.argtypes = []
_libc.mach_task_self.restype = ctypes.c_uint


def _key_to_uint32(key: str) -> int:
    encoded = key.encode("ascii")
    if len(encoded) != 4:
        raise ValueError("SMC key must be 4 ASCII characters")
    return (
        (encoded[0] << 24)
        | (encoded[1] << 16)
        | (encoded[2] << 8)
        | encoded[3]
    )


def _uint32_to_key(value: int) -> str:
    return bytes(
        (
            (value >> 24) & 0xFF,
            (value >> 16) & 0xFF,
            (value >> 8) & 0xFF,
            value & 0xFF,
        )
    ).decode("ascii", errors="ignore")


class AppleSMC:
    def __init__(self) -> None:
        self._connection = self._open()

    def close(self) -> None:
        if self._connection:
            _iokit.IOServiceClose(self._connection)
            self._connection = 0

    def __del__(self) -> None:
        self.close()

    def _open(self) -> int:
        master_port = ctypes.c_uint()
        result = _iokit.IOMasterPort(0, ctypes.byref(master_port))
        if result != _K_IORETURN_SUCCESS:
            raise RuntimeError("failed to obtain IOKit master port")

        matching = _iokit.IOServiceMatching(b"AppleSMC")
        iterator = ctypes.c_uint()
        result = _iokit.IOServiceGetMatchingServices(master_port.value, matching, ctypes.byref(iterator))
        if result != _K_IORETURN_SUCCESS:
            raise RuntimeError("failed to locate AppleSMC service")

        device = _iokit.IOIteratorNext(iterator.value)
        _iokit.IOObjectRelease(iterator.value)
        if not device:
            raise RuntimeError("AppleSMC service not found")

        connection = ctypes.c_uint()
        result = _iokit.IOServiceOpen(device, _libc.mach_task_self(), 0, ctypes.byref(connection))
        _iokit.IOObjectRelease(device)
        if result != _K_IORETURN_SUCCESS:
            raise RuntimeError("failed to open AppleSMC service")
        return int(connection.value)

    def _call(self, input_struct: _SMCKeyData) -> _SMCKeyData:
        output_struct = _SMCKeyData()
        output_size = ctypes.c_size_t(ctypes.sizeof(_SMCKeyData))
        result = _iokit.IOConnectCallStructMethod(
            self._connection,
            _KERNEL_INDEX_SMC,
            ctypes.byref(input_struct),
            ctypes.sizeof(_SMCKeyData),
            ctypes.byref(output_struct),
            ctypes.byref(output_size),
        )
        if result != _K_IORETURN_SUCCESS:
            raise RuntimeError("SMC call failed")
        return output_struct

    def read_key(self, key: str) -> SMCValue:
        input_struct = _SMCKeyData()
        input_struct.key = _key_to_uint32(key)
        input_struct.data8 = _SMC_CMD_READ_KEYINFO
        output_struct = self._call(input_struct)

        value = SMCValue()
        value.dataSize = output_struct.keyInfo.dataSize
        value.dataType = (_uint32_to_key(output_struct.keyInfo.dataType) + "\0").encode("ascii")

        input_struct = _SMCKeyData()
        input_struct.key = _key_to_uint32(key)
        input_struct.keyInfo.dataSize = output_struct.keyInfo.dataSize
        input_struct.data8 = _SMC_CMD_READ_BYTES
        output_struct = self._call(input_struct)

        for idx in range(min(len(output_struct.bytes), len(value.bytes))):
            value.bytes[idx] = output_struct.bytes[idx]
        value.key = (key + "\0").encode("ascii")
        return value

    def read_numeric(self, key: str) -> Optional[float]:
        try:
            value = self.read_key(key)
        except RuntimeError:
            return None

        data_size = int(value.dataSize)
        if data_size <= 0:
            return None

        data_type = bytes(value.dataType).rstrip(b"\0").decode("ascii", errors="ignore")
        payload = bytes(value.bytes[:data_size])
        if not payload:
            return None
        if all(byte == 0 for byte in payload):
            return 0.0

        return _decode_numeric(payload, data_type)

    def read_temperature(self, key: str) -> Optional[float]:
        value = self.read_numeric(key)
        if value is None:
            return None
        return float(value)

    def fan_count(self) -> Optional[int]:
        try:
            value = self.read_key(_KEY_FAN_NUM)
        except RuntimeError:
            return None
        size = int(value.dataSize)
        if size <= 0:
            return None
        data = bytes(value.bytes[:size])
        total = 0
        for idx, byte in enumerate(data):
            total += byte << (8 * (size - 1 - idx))
        return int(total)

    def fan_speed(self, fan_number: int) -> Optional[float]:
        try:
            value = self.read_key(_KEY_FAN_SPEED % fan_number)
        except RuntimeError:
            return None

        if value.dataSize <= 0:
            return None
        data_type = bytes(value.dataType).rstrip(b"\0").decode("ascii", errors="ignore")
        if data_type == "fpe2":
            raw = int(value.bytes[0]) * 256 + int(value.bytes[1])
            return raw / 4.0
        if data_type == "flt ":
            return struct.unpack("<f", bytes(value.bytes[:4]))[0]
        return None

    def cpu_temperature(self) -> Optional[float]:
        return self.read_temperature(_KEY_CPU_TEMP)

    def cpu_power(self) -> Optional[float]:
        return self._read_first_numeric(_KEY_CPU_POWER_CANDIDATES)

    def system_power(self) -> Optional[float]:
        return self._read_first_numeric(_KEY_SYSTEM_POWER_CANDIDATES)

    def _read_first_numeric(self, keys: tuple[str, ...]) -> Optional[float]:
        for key in keys:
            value = self.read_numeric(key)
            if value is not None:
                return value
        return None


def _decode_fixed_point(payload: bytes, fractional_bits: int, signed: bool = False) -> Optional[float]:
    if len(payload) != 2:
        return None
    raw = int.from_bytes(payload, byteorder="big", signed=signed)
    return raw / float(1 << fractional_bits)


def _decode_numeric(payload: bytes, data_type: str) -> Optional[float]:
    if data_type == "ui8 " and len(payload) == 1:
        return float(payload[0])
    if data_type == "ui16" and len(payload) == 2:
        return float(int.from_bytes(payload, byteorder="big", signed=False))
    if data_type == "ui32" and len(payload) == 4:
        return float(int.from_bytes(payload, byteorder="big", signed=False))
    if data_type == "sp1e":
        return _decode_fixed_point(payload, 14)
    if data_type == "sp3c":
        return _decode_fixed_point(payload, 12)
    if data_type == "sp4b":
        return _decode_fixed_point(payload, 11)
    if data_type == "sp5a":
        return _decode_fixed_point(payload, 10)
    if data_type == "sp69":
        return _decode_fixed_point(payload, 9)
    if data_type == "sp78":
        return _decode_fixed_point(payload, 8, signed=True)
    if data_type == "sp87":
        return _decode_fixed_point(payload, 7, signed=True)
    if data_type == "sp96":
        return _decode_fixed_point(payload, 6, signed=True)
    if data_type == "spa5":
        return _decode_fixed_point(payload, 5)
    if data_type == "spb4":
        return _decode_fixed_point(payload, 4, signed=True)
    if data_type == "spf0":
        return _decode_fixed_point(payload, 0, signed=True)
    if data_type == "fpe2" and len(payload) == 2:
        raw = int(payload[0]) * 256 + int(payload[1])
        return raw / 4.0
    if data_type == "flt " and len(payload) == 4:
        return float(struct.unpack("<f", payload)[0])
    return None
