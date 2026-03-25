from __future__ import annotations

import ctypes
import ctypes.util
import plistlib
from typing import Any, Iterable, Optional


_IOKIT_PATH = ctypes.util.find_library("IOKit")
_COREFOUNDATION_PATH = ctypes.util.find_library("CoreFoundation")
if not _IOKIT_PATH or not _COREFOUNDATION_PATH:
    raise RuntimeError("required macOS frameworks not found")

_iokit = ctypes.cdll.LoadLibrary(_IOKIT_PATH)
_cf = ctypes.cdll.LoadLibrary(_COREFOUNDATION_PATH)

_K_IORETURN_SUCCESS = 0
_K_CFSTRING_ENCODING_UTF8 = 0x08000100
_K_CFPROPERTYLIST_BINARY_FORMAT_V1_0 = 200
_K_IO_SERVICE_PLANE = b"IOService"
_K_IO_BLOCK_STORAGE_DEVICE_CLASS = b"IOBlockStorageDevice"
_K_IO_PROPERTY_NVME_SMART_CAPABLE_KEY = "NVMe SMART Capable"


class CFUUIDBytes(ctypes.Structure):
    _fields_ = [
        ("byte0", ctypes.c_uint8),
        ("byte1", ctypes.c_uint8),
        ("byte2", ctypes.c_uint8),
        ("byte3", ctypes.c_uint8),
        ("byte4", ctypes.c_uint8),
        ("byte5", ctypes.c_uint8),
        ("byte6", ctypes.c_uint8),
        ("byte7", ctypes.c_uint8),
        ("byte8", ctypes.c_uint8),
        ("byte9", ctypes.c_uint8),
        ("byte10", ctypes.c_uint8),
        ("byte11", ctypes.c_uint8),
        ("byte12", ctypes.c_uint8),
        ("byte13", ctypes.c_uint8),
        ("byte14", ctypes.c_uint8),
        ("byte15", ctypes.c_uint8),
    ]


class NVMeSMARTData(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("CRITICAL_WARNING", ctypes.c_uint8),
        ("TEMPERATURE", ctypes.c_uint16),
        ("AVAILABLE_SPARE", ctypes.c_uint8),
        ("AVAILABLE_SPARE_THRESHOLD", ctypes.c_uint8),
        ("PERCENTAGE_USED", ctypes.c_uint8),
        ("RESERVED1", ctypes.c_uint8 * 26),
        ("DATA_UNITS_READ", ctypes.c_uint64 * 2),
        ("DATA_UNITS_WRITTEN", ctypes.c_uint64 * 2),
        ("HOST_READ_COMMANDS", ctypes.c_uint64 * 2),
        ("HOST_WRITE_COMMANDS", ctypes.c_uint64 * 2),
        ("CONTROLLER_BUSY_TIME", ctypes.c_uint64 * 2),
        ("POWER_CYCLES", ctypes.c_uint64 * 2),
        ("POWER_ON_HOURS", ctypes.c_uint64 * 2),
        ("UNSAFE_SHUTDOWNS", ctypes.c_uint64 * 2),
        ("MEDIA_ERRORS", ctypes.c_uint64 * 2),
        ("NUM_ERROR_INFO_LOG_ENTRIES", ctypes.c_uint64 * 2),
        ("RESERVED2", ctypes.c_uint8 * 320),
    ]


_QueryInterfaceFunc = ctypes.CFUNCTYPE(
    ctypes.c_int32,
    ctypes.c_void_p,
    CFUUIDBytes,
    ctypes.POINTER(ctypes.c_void_p),
)
_IUnknownRefCountFunc = ctypes.CFUNCTYPE(ctypes.c_uint32, ctypes.c_void_p)
_SMARTReadDataFunc = ctypes.CFUNCTYPE(
    ctypes.c_int32,
    ctypes.c_void_p,
    ctypes.POINTER(NVMeSMARTData),
)


class IOCFPlugInInterface(ctypes.Structure):
    _fields_ = [
        ("_reserved", ctypes.c_void_p),
        ("QueryInterface", _QueryInterfaceFunc),
        ("AddRef", _IUnknownRefCountFunc),
        ("Release", _IUnknownRefCountFunc),
        ("version", ctypes.c_uint16),
        ("revision", ctypes.c_uint16),
        ("Probe", ctypes.c_void_p),
        ("Start", ctypes.c_void_p),
        ("Stop", ctypes.c_void_p),
    ]


class IONVMeSMARTInterface(ctypes.Structure):
    _fields_ = [
        ("_reserved", ctypes.c_void_p),
        ("QueryInterface", _QueryInterfaceFunc),
        ("AddRef", _IUnknownRefCountFunc),
        ("Release", _IUnknownRefCountFunc),
        ("version", ctypes.c_uint16),
        ("revision", ctypes.c_uint16),
        ("SMARTReadData", _SMARTReadDataFunc),
        ("GetIdentifyData", ctypes.c_void_p),
        ("reserved0", ctypes.c_uint64),
        ("reserved1", ctypes.c_uint64),
        ("GetLogPage", ctypes.c_void_p),
        ("reserved2", ctypes.c_uint64),
        ("reserved3", ctypes.c_uint64),
        ("reserved4", ctypes.c_uint64),
        ("reserved5", ctypes.c_uint64),
        ("reserved6", ctypes.c_uint64),
        ("reserved7", ctypes.c_uint64),
        ("reserved8", ctypes.c_uint64),
        ("reserved9", ctypes.c_uint64),
        ("reserved10", ctypes.c_uint64),
        ("reserved11", ctypes.c_uint64),
        ("reserved12", ctypes.c_uint64),
        ("reserved13", ctypes.c_uint64),
        ("reserved14", ctypes.c_uint64),
        ("reserved15", ctypes.c_uint64),
        ("reserved16", ctypes.c_uint64),
        ("reserved17", ctypes.c_uint64),
        ("reserved18", ctypes.c_uint64),
        ("reserved19", ctypes.c_uint64),
        ("reserved20", ctypes.c_uint64),
        ("reserved21", ctypes.c_uint64),
        ("reserved22", ctypes.c_uint64),
        ("reserved23", ctypes.c_uint64),
    ]


_K_IONVME_SMART_USER_CLIENT_TYPE = CFUUIDBytes(
    0xAA, 0x0F, 0xA6, 0xF9,
    0xC2, 0xD6, 0x45, 0x7F,
    0xB1, 0x0B, 0x59, 0xA1,
    0x32, 0x53, 0x29, 0x2F,
)
_K_IONVME_SMART_INTERFACE = CFUUIDBytes(
    0xCC, 0xD1, 0xDB, 0x19,
    0xFD, 0x9A, 0x4D, 0xAF,
    0xBF, 0x95, 0x12, 0x45,
    0x4B, 0x23, 0x0A, 0xB6,
)
_K_IOCFPLUGIN_INTERFACE = CFUUIDBytes(
    0xC2, 0x44, 0xE8, 0x58,
    0x10, 0x9C, 0x11, 0xD4,
    0x91, 0xD4, 0x00, 0x50,
    0xE4, 0xC6, 0x42, 0x6F,
)

_iokit.IOMasterPort.argtypes = [ctypes.c_uint32, ctypes.POINTER(ctypes.c_uint)]
_iokit.IOMasterPort.restype = ctypes.c_int
_iokit.IOServiceMatching.argtypes = [ctypes.c_char_p]
_iokit.IOServiceMatching.restype = ctypes.c_void_p
_iokit.IOBSDNameMatching.argtypes = [ctypes.c_uint, ctypes.c_uint32, ctypes.c_char_p]
_iokit.IOBSDNameMatching.restype = ctypes.c_void_p
_iokit.IOServiceGetMatchingService.argtypes = [ctypes.c_uint, ctypes.c_void_p]
_iokit.IOServiceGetMatchingService.restype = ctypes.c_uint
_iokit.IOServiceGetMatchingServices.argtypes = [ctypes.c_uint, ctypes.c_void_p, ctypes.POINTER(ctypes.c_uint)]
_iokit.IOServiceGetMatchingServices.restype = ctypes.c_int
_iokit.IOIteratorNext.argtypes = [ctypes.c_uint]
_iokit.IOIteratorNext.restype = ctypes.c_uint
_iokit.IOObjectRelease.argtypes = [ctypes.c_uint]
_iokit.IOObjectRelease.restype = ctypes.c_int
_iokit.IOObjectConformsTo.argtypes = [ctypes.c_uint, ctypes.c_char_p]
_iokit.IOObjectConformsTo.restype = ctypes.c_int
_iokit.IORegistryEntryCreateCFProperty.argtypes = [ctypes.c_uint, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_uint32]
_iokit.IORegistryEntryCreateCFProperty.restype = ctypes.c_void_p
_iokit.IORegistryEntryGetParentEntry.argtypes = [ctypes.c_uint, ctypes.c_char_p, ctypes.POINTER(ctypes.c_uint)]
_iokit.IORegistryEntryGetParentEntry.restype = ctypes.c_int
_iokit.IORegistryCreateIterator.argtypes = [ctypes.c_uint, ctypes.c_char_p, ctypes.c_uint32, ctypes.POINTER(ctypes.c_uint)]
_iokit.IORegistryCreateIterator.restype = ctypes.c_int
_iokit.IOObjectGetClass.argtypes = [ctypes.c_uint, ctypes.c_char_p]
_iokit.IOObjectGetClass.restype = ctypes.c_int
_iokit.IOCreatePlugInInterfaceForService.argtypes = [
    ctypes.c_uint,
    ctypes.c_void_p,
    ctypes.c_void_p,
    ctypes.POINTER(ctypes.POINTER(ctypes.POINTER(IOCFPlugInInterface))),
    ctypes.POINTER(ctypes.c_int32),
]
_iokit.IOCreatePlugInInterfaceForService.restype = ctypes.c_int
_iokit.IODestroyPlugInInterface.argtypes = [ctypes.POINTER(ctypes.POINTER(IOCFPlugInInterface))]
_iokit.IODestroyPlugInInterface.restype = ctypes.c_int

_cf.CFStringCreateWithCString.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_uint32]
_cf.CFStringCreateWithCString.restype = ctypes.c_void_p
_cf.CFUUIDCreateFromUUIDBytes.argtypes = [ctypes.c_void_p, CFUUIDBytes]
_cf.CFUUIDCreateFromUUIDBytes.restype = ctypes.c_void_p
_cf.CFPropertyListCreateData.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_uint64, ctypes.c_uint64, ctypes.c_void_p]
_cf.CFPropertyListCreateData.restype = ctypes.c_void_p
_cf.CFDataGetLength.argtypes = [ctypes.c_void_p]
_cf.CFDataGetLength.restype = ctypes.c_long
_cf.CFDataGetBytePtr.argtypes = [ctypes.c_void_p]
_cf.CFDataGetBytePtr.restype = ctypes.POINTER(ctypes.c_ubyte)
_cf.CFRelease.argtypes = [ctypes.c_void_p]
_cf.CFRelease.restype = None


def _cfstring(value: str) -> int:
    ref = _cf.CFStringCreateWithCString(None, value.encode("utf-8"), _K_CFSTRING_ENCODING_UTF8)
    if not ref:
        raise RuntimeError("failed to create CFString")
    return int(ref)


def _cf_to_python(value_ref: int) -> Any:
    data_ref = _cf.CFPropertyListCreateData(None, value_ref, _K_CFPROPERTYLIST_BINARY_FORMAT_V1_0, 0, None)
    if not data_ref:
        return None
    try:
        length = _cf.CFDataGetLength(data_ref)
        raw = ctypes.string_at(_cf.CFDataGetBytePtr(data_ref), length)
        return plistlib.loads(raw)
    finally:
        _cf.CFRelease(data_ref)


def _cfuuid(uuid_bytes: CFUUIDBytes) -> int:
    ref = _cf.CFUUIDCreateFromUUIDBytes(None, uuid_bytes)
    if not ref:
        raise RuntimeError("failed to create CFUUID")
    return int(ref)


def _registry_property(service: int, property_name: str) -> Optional[Any]:
    key_ref = _cfstring(property_name)
    try:
        property_ref = _iokit.IORegistryEntryCreateCFProperty(service, key_ref, None, 0)
    finally:
        _cf.CFRelease(key_ref)
    if not property_ref:
        return None
    try:
        return _cf_to_python(property_ref)
    finally:
        _cf.CFRelease(property_ref)


def read_matching_property(class_names: Any, property_name: str) -> Optional[Any]:
    master_port = ctypes.c_uint()
    result = _iokit.IOMasterPort(0, ctypes.byref(master_port))
    if result != _K_IORETURN_SUCCESS:
        return None

    property_ref = None
    iterator = ctypes.c_uint()
    for class_name in class_names:
        matching = _iokit.IOServiceMatching(class_name.encode("ascii"))
        if not matching:
            continue

        result = _iokit.IOServiceGetMatchingServices(master_port.value, matching, ctypes.byref(iterator))
        if result != _K_IORETURN_SUCCESS:
            continue

        try:
            while True:
                service = _iokit.IOIteratorNext(iterator.value)
                if not service:
                    break
                try:
                    key_ref = _cfstring(property_name)
                    try:
                        property_ref = _iokit.IORegistryEntryCreateCFProperty(service, key_ref, None, 0)
                    finally:
                        _cf.CFRelease(key_ref)
                    if property_ref:
                        try:
                            return _cf_to_python(property_ref)
                        finally:
                            _cf.CFRelease(property_ref)
                finally:
                    _iokit.IOObjectRelease(service)
        finally:
            _iokit.IOObjectRelease(iterator.value)
    return None


def search_service_plane_property(property_name: str, class_substring: Optional[str] = None) -> Optional[Any]:
    master_port = ctypes.c_uint()
    result = _iokit.IOMasterPort(0, ctypes.byref(master_port))
    if result != _K_IORETURN_SUCCESS:
        return None

    iterator = ctypes.c_uint()
    result = _iokit.IORegistryCreateIterator(master_port.value, b"IOService", 1, ctypes.byref(iterator))
    if result != _K_IORETURN_SUCCESS:
        return None

    key_ref = _cfstring(property_name)
    try:
        while True:
            service = _iokit.IOIteratorNext(iterator.value)
            if not service:
                break
            try:
                if class_substring:
                    class_name = ctypes.create_string_buffer(128)
                    if _iokit.IOObjectGetClass(service, class_name) != _K_IORETURN_SUCCESS:
                        continue
                    if class_substring not in class_name.value.decode("ascii", errors="ignore"):
                        continue

                property_ref = _iokit.IORegistryEntryCreateCFProperty(service, key_ref, None, 0)
                if not property_ref:
                    continue
                try:
                    return _cf_to_python(property_ref)
                finally:
                    _cf.CFRelease(property_ref)
            finally:
                _iokit.IOObjectRelease(service)
    finally:
        _cf.CFRelease(key_ref)
        _iokit.IOObjectRelease(iterator.value)
    return None


def read_nvme_temperature_for_bsd_name(bsd_name: str) -> Optional[float]:
    matching = _iokit.IOBSDNameMatching(0, 0, bsd_name.encode("utf-8"))
    if not matching:
        return None

    service = _iokit.IOServiceGetMatchingService(0, matching)
    if not service:
        return None

    handles_to_release = []
    current = int(service)
    handles_to_release.append(current)
    try:
        while _iokit.IOObjectConformsTo(current, _K_IO_BLOCK_STORAGE_DEVICE_CLASS) == 0:
            parent = ctypes.c_uint()
            result = _iokit.IORegistryEntryGetParentEntry(current, _K_IO_SERVICE_PLANE, ctypes.byref(parent))
            if result != _K_IORETURN_SUCCESS or not parent.value:
                return None
            current = int(parent.value)
            handles_to_release.append(current)

        smart_capable = _registry_property(current, _K_IO_PROPERTY_NVME_SMART_CAPABLE_KEY)
        if smart_capable is not True:
            return None

        user_client_uuid = _cfuuid(_K_IONVME_SMART_USER_CLIENT_TYPE)
        plugin_uuid = _cfuuid(_K_IOCFPLUGIN_INTERFACE)
        plugin_interface = ctypes.POINTER(ctypes.POINTER(IOCFPlugInInterface))()
        score = ctypes.c_int32(0)
        try:
            result = _iokit.IOCreatePlugInInterfaceForService(
                current,
                user_client_uuid,
                plugin_uuid,
                ctypes.byref(plugin_interface),
                ctypes.byref(score),
            )
        finally:
            _cf.CFRelease(user_client_uuid)
            _cf.CFRelease(plugin_uuid)
        if result != _K_IORETURN_SUCCESS or not plugin_interface:
            return None

        try:
            smart_interface = ctypes.POINTER(ctypes.POINTER(IONVMeSMARTInterface))()
            smart_interface_pp = ctypes.cast(
                ctypes.byref(smart_interface),
                ctypes.POINTER(ctypes.c_void_p),
            )
            result = plugin_interface.contents.contents.QueryInterface(
                plugin_interface,
                _K_IONVME_SMART_INTERFACE,
                smart_interface_pp,
            )
            if result != _K_IORETURN_SUCCESS or not smart_interface:
                return None

            try:
                smart_data = NVMeSMARTData()
                result = smart_interface.contents.contents.SMARTReadData(
                    smart_interface,
                    ctypes.byref(smart_data),
                )
                if result != _K_IORETURN_SUCCESS:
                    return None

                temperature_c = int(smart_data.TEMPERATURE) - 273
                if temperature_c < -100 or temperature_c > 200:
                    return None
                return float(temperature_c)
            finally:
                smart_interface.contents.contents.Release(smart_interface)
        finally:
            _iokit.IODestroyPlugInInterface(plugin_interface)
    finally:
        for handle in reversed(handles_to_release):
            _iokit.IOObjectRelease(handle)


def read_nvme_temperature_max(bsd_names: Iterable[str]) -> Optional[float]:
    temperatures = []
    for bsd_name in bsd_names:
        temperature = read_nvme_temperature_for_bsd_name(bsd_name)
        if temperature is not None:
            temperatures.append(temperature)
    if not temperatures:
        return None
    return max(temperatures)
