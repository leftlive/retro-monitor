//go:build darwin

package provider

/*
#cgo darwin LDFLAGS: -framework IOKit -framework CoreFoundation
#include <CoreFoundation/CoreFoundation.h>
#include <IOKit/IOCFPlugIn.h>
#include <IOKit/IOKitLib.h>
#include <IOKit/storage/nvme/NVMeSMARTLibExternal.h>
#include <stdlib.h>

static int rm_read_nvme_temperature(const char *bsdName, double *outTemp) {
  io_service_t service = IOServiceGetMatchingService(kIOMainPortDefault, IOBSDNameMatching(kIOMainPortDefault, 0, bsdName));
  if (!service) {
    return -1;
  }

  io_object_t handles[32];
  int handleCount = 0;
  io_registry_entry_t current = service;
  handles[handleCount++] = current;

  while (!IOObjectConformsTo(current, "IOBlockStorageDevice")) {
    io_registry_entry_t parent = IO_OBJECT_NULL;
    kern_return_t result = IORegistryEntryGetParentEntry(current, kIOServicePlane, &parent);
    if (result != kIOReturnSuccess || !parent) {
      for (int i = handleCount - 1; i >= 0; i--) {
        IOObjectRelease(handles[i]);
      }
      return -2;
    }
    if (handleCount < 32) {
      handles[handleCount++] = parent;
    }
    current = parent;
  }

  CFStringRef smartKey = CFStringCreateWithCString(kCFAllocatorDefault, kIOPropertyNVMeSMARTCapableKey, kCFStringEncodingUTF8);
  if (!smartKey) {
    for (int i = handleCount - 1; i >= 0; i--) {
      IOObjectRelease(handles[i]);
    }
    return -3;
  }

  CFTypeRef smartCapableRef = IORegistryEntryCreateCFProperty(current, smartKey, kCFAllocatorDefault, 0);
  CFRelease(smartKey);
  if (!smartCapableRef) {
    for (int i = handleCount - 1; i >= 0; i--) {
      IOObjectRelease(handles[i]);
    }
    return -4;
  }

  Boolean smartCapable = CFGetTypeID(smartCapableRef) == CFBooleanGetTypeID() && CFBooleanGetValue((CFBooleanRef)smartCapableRef);
  CFRelease(smartCapableRef);
  if (!smartCapable) {
    for (int i = handleCount - 1; i >= 0; i--) {
      IOObjectRelease(handles[i]);
    }
    return -5;
  }

  IOCFPlugInInterface **plugin = NULL;
  SInt32 score = 0;
  kern_return_t result = IOCreatePlugInInterfaceForService(current, kIONVMeSMARTUserClientTypeID, kIOCFPlugInInterfaceID, &plugin, &score);
  if (result != kIOReturnSuccess || !plugin) {
    for (int i = handleCount - 1; i >= 0; i--) {
      IOObjectRelease(handles[i]);
    }
    return -6;
  }

  IONVMeSMARTInterface **smart = NULL;
  HRESULT query = (*plugin)->QueryInterface(plugin, CFUUIDGetUUIDBytes(kIONVMeSMARTInterfaceID), (LPVOID *)&smart);
  if (query != S_OK || !smart) {
    IODestroyPlugInInterface(plugin);
    for (int i = handleCount - 1; i >= 0; i--) {
      IOObjectRelease(handles[i]);
    }
    return -7;
  }

  NVMeSMARTData smartData;
  result = (*smart)->SMARTReadData(smart, &smartData);
  (*smart)->Release(smart);
  IODestroyPlugInInterface(plugin);
  for (int i = handleCount - 1; i >= 0; i--) {
    IOObjectRelease(handles[i]);
  }
  if (result != kIOReturnSuccess) {
    return -8;
  }

  int tempC = (int)smartData.TEMPERATURE - 273;
  if (tempC < -100 || tempC > 200) {
    return -9;
  }

  *outTemp = (double)tempC;
  return 0;
}
*/
import "C"

import "unsafe"

func readNVMeTemperatureForBSDName(bsdName string) *float64 {
	cName := C.CString(bsdName)
	defer C.free(unsafe.Pointer(cName))

	var temp C.double
	if rc := C.rm_read_nvme_temperature(cName, &temp); rc != 0 {
		return nil
	}
	return f64(round1(float64(temp)))
}

func readNVMeTemperatureMax(bsdNames []string) *float64 {
	var max *float64
	for _, name := range bsdNames {
		temp := readNVMeTemperatureForBSDName(name)
		if temp == nil {
			continue
		}
		if max == nil || *temp > *max {
			max = temp
		}
	}
	return max
}
