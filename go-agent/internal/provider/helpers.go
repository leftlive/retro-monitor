package provider

import "math"

func f64(v float64) *float64 {
	return &v
}

func round1(v float64) float64 {
	return math.Round(v*10) / 10
}
