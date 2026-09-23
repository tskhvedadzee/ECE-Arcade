#pragma once

#include "geometry.h"

// The boresight is the camera coordinate the gun's sights line up with.
// Uncalibrated it is the image centre; calibration corrects for the camera
// not being mounted exactly parallel to the barrel.
constexpr Point2 kDefaultBoresight = {0.5f, 0.375f};

// Screen position the gun is aimed at, given the LED positions seen by the
// camera and their known positions on the screen.
bool computeAim(const Point2 ledsCamera[kLedCount], const Point2 ledsScreen[kLedCount],
                Point2 boresight, Point2& aim);

// Boresight for a gun that is currently aimed at screenTarget.
bool calibrateBoresight(const Point2 ledsCamera[kLedCount], const Point2 ledsScreen[kLedCount],
                        Point2 screenTarget, Point2& boresight);

inline bool isOnScreen(Point2 p) { return p.x >= 0 && p.x <= 1 && p.y >= 0 && p.y <= 1; }
