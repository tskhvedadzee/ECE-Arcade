#pragma once

#include "geometry.h"

// Plane-to-plane perspective transform defined by four point pairs.
class Homography {
 public:
  // Solves for the transform that maps src[i] onto dst[i].
  // Returns false if the points are degenerate (three or more collinear).
  static bool fromPoints(const Point2 src[4], const Point2 dst[4], Homography& out);

  Point2 map(Point2 p) const;

 private:
  double h_[8] = {1, 0, 0, 0, 1, 0, 0, 0};  // row-major 3x3 with h[8] fixed to 1
};

// Gaussian elimination with partial pivoting. Solves a*x = b for an n*n
// row-major matrix; the solution overwrites b and a is destroyed.
bool solveLinearSystem(double* a, double* b, int n);
