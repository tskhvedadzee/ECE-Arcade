#pragma once

#include "geometry.h"

// Assigns camera blobs to the four LEDs and fills in LEDs that have left the
// camera's field of view, using the last complete frame as a reference.
//
//   4 blobs: labelled by angle around their centroid (tolerates +/-45 deg roll)
//   3 blobs: missing LED from an affine fit to the previous frame
//   2 blobs: missing LEDs from a similarity fit to the previous frame
//   0-1 blobs, or 2-3 with no history: tracking lost
class LedTracker {
 public:
  // blobs may be in any order. On success leds[] holds all four LED positions
  // in camera coordinates, indexed by LedIndex.
  bool update(const Point2* blobs, int count, Point2 leds[kLedCount]);
  void reset() { valid_ = false; }
  bool hasHistory() const { return valid_; }

 private:
  Point2 previous_[kLedCount] = {};
  bool valid_ = false;
};
