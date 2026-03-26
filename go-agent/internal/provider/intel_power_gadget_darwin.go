//go:build darwin

package provider

/*
#cgo darwin LDFLAGS: -ldl
#include <dlfcn.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdlib.h>

typedef bool (*pg_initialize_fn)(void);
typedef bool (*pg_shutdown_fn)(void);
typedef bool (*pg_is_platform_energy_available_fn)(int, bool *);
typedef bool (*pg_read_sample_fn)(int, uint64_t *);
typedef bool (*pg_sample_release_fn)(uint64_t);
typedef bool (*pg_sample_get_platform_power_fn)(uint64_t, uint64_t, double *, double *);

typedef struct {
  void *handle;
  pg_initialize_fn initialize;
  pg_shutdown_fn shutdown;
  pg_is_platform_energy_available_fn is_platform_energy_available;
  pg_read_sample_fn read_sample;
  pg_sample_release_fn sample_release;
  pg_sample_get_platform_power_fn sample_get_platform_power;
} rm_pg_lib;

static rm_pg_lib *rm_pg_open(const char *path) {
  void *handle = dlopen(path, RTLD_NOW | RTLD_LOCAL);
  if (!handle) {
    return NULL;
  }

  rm_pg_lib *lib = (rm_pg_lib *)calloc(1, sizeof(rm_pg_lib));
  if (!lib) {
    dlclose(handle);
    return NULL;
  }

  lib->handle = handle;
  lib->initialize = (pg_initialize_fn)dlsym(handle, "PG_Initialize");
  lib->shutdown = (pg_shutdown_fn)dlsym(handle, "PG_Shutdown");
  lib->is_platform_energy_available = (pg_is_platform_energy_available_fn)dlsym(handle, "PG_IsPlatformEnergyAvailable");
  lib->read_sample = (pg_read_sample_fn)dlsym(handle, "PG_ReadSample");
  lib->sample_release = (pg_sample_release_fn)dlsym(handle, "PGSample_Release");
  lib->sample_get_platform_power = (pg_sample_get_platform_power_fn)dlsym(handle, "PGSample_GetPlatformPower");

  if (!lib->initialize || !lib->shutdown || !lib->is_platform_energy_available || !lib->read_sample || !lib->sample_release || !lib->sample_get_platform_power) {
    dlclose(handle);
    free(lib);
    return NULL;
  }

  return lib;
}

static void rm_pg_close(rm_pg_lib *lib) {
  if (!lib) {
    return;
  }
  if (lib->handle) {
    dlclose(lib->handle);
  }
  free(lib);
}

static bool rm_pg_initialize(rm_pg_lib *lib) {
  return lib && lib->initialize && lib->initialize();
}

static bool rm_pg_shutdown(rm_pg_lib *lib) {
  return lib && lib->shutdown && lib->shutdown();
}

static bool rm_pg_is_platform_available(rm_pg_lib *lib, int packageIndex, bool *available) {
  return lib && lib->is_platform_energy_available && lib->is_platform_energy_available(packageIndex, available);
}

static bool rm_pg_read_sample(rm_pg_lib *lib, int packageIndex, uint64_t *sample) {
  return lib && lib->read_sample && lib->read_sample(packageIndex, sample);
}

static bool rm_pg_release_sample(rm_pg_lib *lib, uint64_t sample) {
  return lib && lib->sample_release && lib->sample_release(sample);
}

static bool rm_pg_get_platform_power(rm_pg_lib *lib, uint64_t start, uint64_t end, double *power, double *energy) {
  return lib && lib->sample_get_platform_power && lib->sample_get_platform_power(start, end, power, energy);
}
*/
import "C"

import (
	"errors"
	"os"
	"unsafe"
)

const intelPowerGadgetFrameworkPath = "/Library/Frameworks/IntelPowerGadget.framework/IntelPowerGadget"

type intelPowerGadget struct {
	lib               *C.rm_pg_lib
	packageIndex      C.int
	platformAvailable bool
	lastSample        *C.uint64_t
}

func newIntelPowerGadget() (*intelPowerGadget, error) {
	if _, err := os.Stat(intelPowerGadgetFrameworkPath); err != nil {
		return nil, err
	}

	cPath := C.CString(intelPowerGadgetFrameworkPath)
	defer C.free(unsafe.Pointer(cPath))

	lib := C.rm_pg_open(cPath)
	if lib == nil {
		return nil, errors.New("failed to open IntelPowerGadget")
	}

	if ok := C.rm_pg_initialize(lib); !bool(ok) {
		C.rm_pg_close(lib)
		return nil, errors.New("failed to initialize IntelPowerGadget")
	}

	gadget := &intelPowerGadget{
		lib:          lib,
		packageIndex: 0,
	}

	var available C.bool
	if ok := C.rm_pg_is_platform_available(lib, gadget.packageIndex, &available); bool(ok) {
		gadget.platformAvailable = bool(available)
	}

	return gadget, nil
}

func (g *intelPowerGadget) Close() {
	if g == nil || g.lib == nil {
		return
	}
	if g.lastSample != nil {
		C.rm_pg_release_sample(g.lib, *g.lastSample)
		g.lastSample = nil
	}
	C.rm_pg_shutdown(g.lib)
	C.rm_pg_close(g.lib)
	g.lib = nil
}

func (g *intelPowerGadget) platformPower() *float64 {
	if g == nil || g.lib == nil || !g.platformAvailable {
		return nil
	}

	var sample C.uint64_t
	if ok := C.rm_pg_read_sample(g.lib, g.packageIndex, &sample); !bool(ok) {
		return nil
	}

	if g.lastSample == nil {
		g.lastSample = new(C.uint64_t)
		*g.lastSample = sample
		return nil
	}

	var power C.double
	var energy C.double
	ok := C.rm_pg_get_platform_power(g.lib, *g.lastSample, sample, &power, &energy)
	C.rm_pg_release_sample(g.lib, *g.lastSample)
	*g.lastSample = sample
	if !bool(ok) {
		return nil
	}

	return f64(round1(float64(power)))
}
