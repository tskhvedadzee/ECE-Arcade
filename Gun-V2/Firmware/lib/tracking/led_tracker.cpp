#include "led_tracker.h"

#include <math.h>
#include <string.h>

#include <algorithm>

#include "homography.h"

namespace {

constexpr float kPi = 3.14159265358979f;

float wrapAngle(float a) {
  while (a > kPi) a -= 2 * kPi;
  while (a < -kPi) a += 2 * kPi;
  return a;
}

float squaredDistance(Point2 a, Point2 b) {
  const float dx = a.x - b.x, dy = a.y - b.y;
  return dx * dx + dy * dy;
}

// In a diamond each LED lies on an axis through the centre, so seen from the
// centroid they sit at -90, 0, 90 and 180 degrees (y points down).
void labelByAngle(const Point2 blobs[4], Point2 leds[kLedCount]) {
  static const float kExpected[kLedCount] = {-kPi / 2, 0.0f, kPi / 2, kPi};

  Point2 c = {0, 0};
  for (int i = 0; i < 4; ++i) {
    c.x += blobs[i].x / 4;
    c.y += blobs[i].y / 4;
  }
  float angle[4];
  for (int i = 0; i < 4; ++i) angle[i] = atan2f(blobs[i].y - c.y, blobs[i].x - c.x);

  int perm[4] = {0, 1, 2, 3};
  int best[4] = {0, 1, 2, 3};
  float bestCost = INFINITY;
  do {
    float cost = 0;
    for (int i = 0; i < 4; ++i) {
      const float d = wrapAngle(angle[i] - kExpected[perm[i]]);
      cost += d * d;
    }
    if (cost < bestCost) {
      bestCost = cost;
      memcpy(best, perm, sizeof(perm));
    }
  } while (std::next_permutation(perm, perm + 4));

  for (int i = 0; i < 4; ++i) leds[best[i]] = blobs[i];
}

// Minimum-distance assignment of fewer than four blobs to last frame's LEDs.
void labelByHistory(const Point2* blobs, int count, const Point2 previous[kLedCount],
                    int labels[kLedCount]) {
  int perm[4] = {0, 1, 2, 3};
  float bestCost = INFINITY;
  do {
    float cost = 0;
    for (int i = 0; i < count; ++i) cost += squaredDistance(blobs[i], previous[perm[i]]);
    if (cost < bestCost) {
      bestCost = cost;
      memcpy(labels, perm, sizeof(int) * count);
    }
  } while (std::next_permutation(perm, perm + 4));
}

// x' = m0*x + m1*y + m2, y' = m3*x + m4*y + m5, from three point pairs.
bool fitAffine(const Point2 src[3], const Point2 dst[3], double m[6]) {
  double ax[9], ay[9], bx[3], by[3];
  for (int i = 0; i < 3; ++i) {
    ax[i * 3 + 0] = src[i].x;
    ax[i * 3 + 1] = src[i].y;
    ax[i * 3 + 2] = 1;
    bx[i] = dst[i].x;
    by[i] = dst[i].y;
  }
  memcpy(ay, ax, sizeof(ax));
  if (!solveLinearSystem(ax, bx, 3) || !solveLinearSystem(ay, by, 3)) return false;
  for (int i = 0; i < 3; ++i) {
    m[i] = bx[i];
    m[3 + i] = by[i];
  }
  return true;
}

// Rotation, uniform scale and translation from two point pairs, treating the
// points as complex numbers: p' = k*p + t, with m = {Re k, Im k, t.x, t.y}.
bool fitSimilarity(Point2 s0, Point2 s1, Point2 d0, Point2 d1, float m[4]) {
  const float sx = s1.x - s0.x, sy = s1.y - s0.y;
  const float dx = d1.x - d0.x, dy = d1.y - d0.y;
  const float den = sx * sx + sy * sy;
  if (den < 1e-8f) return false;
  const float kr = (dx * sx + dy * sy) / den;
  const float ki = (dy * sx - dx * sy) / den;
  m[0] = kr;
  m[1] = ki;
  m[2] = d0.x - (kr * s0.x - ki * s0.y);
  m[3] = d0.y - (kr * s0.y + ki * s0.x);
  return true;
}

}  // namespace

bool LedTracker::update(const Point2* blobs, int count, Point2 leds[kLedCount]) {
  if (count == 4) {
    labelByAngle(blobs, leds);
  } else if (count >= 2 && valid_) {
    int labels[kLedCount];
    labelByHistory(blobs, count, previous_, labels);

    bool seen[kLedCount] = {false, false, false, false};
    for (int i = 0; i < count; ++i) {
      leds[labels[i]] = blobs[i];
      seen[labels[i]] = true;
    }

    if (count == 3) {
      Point2 src[3];
      for (int i = 0; i < 3; ++i) src[i] = previous_[labels[i]];
      double m[6];
      if (!fitAffine(src, blobs, m)) {
        valid_ = false;
        return false;
      }
      for (int j = 0; j < kLedCount; ++j) {
        if (seen[j]) continue;
        const Point2 p = previous_[j];
        leds[j] = {static_cast<float>(m[0] * p.x + m[1] * p.y + m[2]),
                   static_cast<float>(m[3] * p.x + m[4] * p.y + m[5])};
      }
    } else {
      float m[4];
      if (!fitSimilarity(previous_[labels[0]], previous_[labels[1]], blobs[0], blobs[1], m)) {
        valid_ = false;
        return false;
      }
      for (int j = 0; j < kLedCount; ++j) {
        if (seen[j]) continue;
        const Point2 p = previous_[j];
        leds[j] = {m[0] * p.x - m[1] * p.y + m[2], m[0] * p.y + m[1] * p.x + m[3]};
      }
    }
  } else {
    valid_ = false;
    return false;
  }

  memcpy(previous_, leds, sizeof(previous_));
  valid_ = true;
  return true;
}
