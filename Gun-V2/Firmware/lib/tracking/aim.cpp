#include "aim.h"

#include "homography.h"

bool computeAim(const Point2 ledsCamera[kLedCount], const Point2 ledsScreen[kLedCount],
                Point2 boresight, Point2& aim) {
  Homography cameraToScreen;
  if (!Homography::fromPoints(ledsCamera, ledsScreen, cameraToScreen)) return false;
  aim = cameraToScreen.map(boresight);
  return true;
}

bool calibrateBoresight(const Point2 ledsCamera[kLedCount], const Point2 ledsScreen[kLedCount],
                        Point2 screenTarget, Point2& boresight) {
  Homography screenToCamera;
  if (!Homography::fromPoints(ledsScreen, ledsCamera, screenToCamera)) return false;
  boresight = screenToCamera.map(screenTarget);
  return true;
}
