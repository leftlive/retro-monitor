from __future__ import annotations

import ctypes
import os
from typing import Optional


_FRAMEWORK_PATH = "/Library/Frameworks/IntelPowerGadget.framework/IntelPowerGadget"


class IntelPowerGadget:
    def __init__(self, package_index: int = 0) -> None:
        if not os.path.exists(_FRAMEWORK_PATH):
            raise RuntimeError("IntelPowerGadget framework not found")

        self._library = ctypes.cdll.LoadLibrary(_FRAMEWORK_PATH)
        self._configure_api()
        if not self._library.PG_Initialize():
            raise RuntimeError("failed to initialize Intel Power Gadget")

        self._initialized = True
        self._package_index = package_index
        self._platform_available = self._availability(self._library.PG_IsPlatformEnergyAvailable)
        self._sample_id: Optional[int] = None

    def close(self) -> None:
        if self._sample_id is not None:
            self._library.PGSample_Release(self._sample_id)
            self._sample_id = None
        if getattr(self, "_initialized", False):
            self._library.PG_Shutdown()
            self._initialized = False

    def __del__(self) -> None:
        self.close()

    def platform_power(self) -> Optional[float]:
        if not self._platform_available:
            return None
        current_sample = self._read_sample()
        if current_sample is None:
            return None
        if self._sample_id is None:
            self._sample_id = current_sample
            return None

        power = ctypes.c_double()
        energy = ctypes.c_double()
        ok = self._library.PGSample_GetPlatformPower(
            self._sample_id,
            current_sample,
            ctypes.byref(power),
            ctypes.byref(energy),
        )
        self._library.PGSample_Release(self._sample_id)
        self._sample_id = current_sample
        if not ok:
            return None
        return float(power.value)

    def _configure_api(self) -> None:
        self._library.PG_Initialize.argtypes = []
        self._library.PG_Initialize.restype = ctypes.c_bool
        self._library.PG_Shutdown.argtypes = []
        self._library.PG_Shutdown.restype = ctypes.c_bool
        self._library.PG_IsPlatformEnergyAvailable.argtypes = [ctypes.c_int, ctypes.POINTER(ctypes.c_bool)]
        self._library.PG_IsPlatformEnergyAvailable.restype = ctypes.c_bool
        self._library.PG_ReadSample.argtypes = [ctypes.c_int, ctypes.POINTER(ctypes.c_uint64)]
        self._library.PG_ReadSample.restype = ctypes.c_bool
        self._library.PGSample_Release.argtypes = [ctypes.c_uint64]
        self._library.PGSample_Release.restype = ctypes.c_bool
        self._library.PGSample_GetPlatformPower.argtypes = [
            ctypes.c_uint64,
            ctypes.c_uint64,
            ctypes.POINTER(ctypes.c_double),
            ctypes.POINTER(ctypes.c_double),
        ]
        self._library.PGSample_GetPlatformPower.restype = ctypes.c_bool

    def _availability(self, function) -> bool:
        available = ctypes.c_bool(False)
        if not function(self._package_index, ctypes.byref(available)):
            return False
        return bool(available.value)

    def _read_sample(self) -> Optional[int]:
        sample = ctypes.c_uint64()
        if not self._library.PG_ReadSample(self._package_index, ctypes.byref(sample)):
            return None
        return int(sample.value)
