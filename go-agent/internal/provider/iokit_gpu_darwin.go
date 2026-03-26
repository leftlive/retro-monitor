//go:build darwin

package provider

/*
#cgo darwin LDFLAGS: -framework IOKit -framework CoreFoundation
#include <CoreFoundation/CoreFoundation.h>
#include <IOKit/IOKitLib.h>
#include <string.h>

static double rm_cfnumber_to_double(CFTypeRef ref, int *ok) {
  if (!ref || CFGetTypeID(ref) != CFNumberGetTypeID()) {
    *ok = 0;
    return 0;
  }
  double value = 0;
  if (!CFNumberGetValue((CFNumberRef)ref, kCFNumberDoubleType, &value)) {
    *ok = 0;
    return 0;
  }
  *ok = 1;
  return value;
}

static double rm_read_gpu_stat(const char *statKey, int *ok) {
  mach_port_t masterPort;
  if (IOMasterPort(MACH_PORT_NULL, &masterPort) != kIOReturnSuccess) {
    *ok = 0;
    return 0;
  }

  io_iterator_t iterator;
  if (IORegistryCreateIterator(masterPort, "IOService", kIORegistryIterateRecursively, &iterator) != kIOReturnSuccess) {
    *ok = 0;
    return 0;
  }

  io_object_t service;
  while ((service = IOIteratorNext(iterator))) {
    char className[128];
    kern_return_t classResult = IOObjectGetClass(service, className);
    if (classResult != kIOReturnSuccess || strstr(className, "AMDRadeon") == NULL) {
      IOObjectRelease(service);
      continue;
    }

    CFStringRef perfKey = CFStringCreateWithCString(kCFAllocatorDefault, "PerformanceStatistics", kCFStringEncodingUTF8);
    CFTypeRef perfRef = IORegistryEntryCreateCFProperty(service, perfKey, kCFAllocatorDefault, 0);
    CFRelease(perfKey);
    if (!perfRef || CFGetTypeID(perfRef) != CFDictionaryGetTypeID()) {
      if (perfRef) CFRelease(perfRef);
      IOObjectRelease(service);
      continue;
    }

    CFStringRef statKeyRef = CFStringCreateWithCString(kCFAllocatorDefault, statKey, kCFStringEncodingUTF8);
    CFTypeRef valueRef = CFDictionaryGetValue((CFDictionaryRef)perfRef, statKeyRef);
    double value = rm_cfnumber_to_double(valueRef, ok);
    CFRelease(statKeyRef);
    CFRelease(perfRef);
    IOObjectRelease(service);
    IOObjectRelease(iterator);
    return value;
  }

  IOObjectRelease(iterator);
  *ok = 0;
  return 0;
}
*/
import "C"

import "unsafe"

func readGPUStat(key string) *float64 {
	ckey := C.CString(key)
	defer C.free(unsafe.Pointer(ckey))

	ok := C.int(0)
	value := C.rm_read_gpu_stat(ckey, &ok)
	if ok == 0 {
		return nil
	}
	return f64(round1(float64(value)))
}
