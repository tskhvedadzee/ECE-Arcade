#include "homography.h"

#include <math.h>
#include <string.h>

#include <utility>

bool solveLinearSystem(double* a, double* b, int n) {
  for (int col = 0; col < n; ++col) {
    int pivot = col;
    for (int row = col + 1; row < n; ++row) {
      if (fabs(a[row * n + col]) > fabs(a[pivot * n + col])) pivot = row;
    }
    if (fabs(a[pivot * n + col]) < 1e-12) return false;

    if (pivot != col) {
      for (int k = 0; k < n; ++k) std::swap(a[col * n + k], a[pivot * n + k]);
      std::swap(b[col], b[pivot]);
    }
    for (int row = col + 1; row < n; ++row) {
      const double f = a[row * n + col] / a[col * n + col];
      for (int k = col; k < n; ++k) a[row * n + k] -= f * a[col * n + k];
      b[row] -= f * b[col];
    }
  }
  for (int row = n - 1; row >= 0; --row) {
    double sum = b[row];
    for (int k = row + 1; k < n; ++k) sum -= a[row * n + k] * b[k];
    b[row] = sum / a[row * n + row];
  }
  return true;
}

bool Homography::fromPoints(const Point2 src[4], const Point2 dst[4], Homography& out) {
  // Direct linear transform with h8 = 1: each point pair gives two equations.
  double a[64];
  double b[8];
  for (int i = 0; i < 4; ++i) {
    const double x = src[i].x, y = src[i].y;
    const double u = dst[i].x, v = dst[i].y;
    const double row0[8] = {x, y, 1, 0, 0, 0, -u * x, -u * y};
    const double row1[8] = {0, 0, 0, x, y, 1, -v * x, -v * y};
    memcpy(&a[(2 * i) * 8], row0, sizeof(row0));
    memcpy(&a[(2 * i + 1) * 8], row1, sizeof(row1));
    b[2 * i] = u;
    b[2 * i + 1] = v;
  }
  if (!solveLinearSystem(a, b, 8)) return false;
  memcpy(out.h_, b, sizeof(b));
  return true;
}

Point2 Homography::map(Point2 p) const {
  const double w = h_[6] * p.x + h_[7] * p.y + 1.0;
  return {static_cast<float>((h_[0] * p.x + h_[1] * p.y + h_[2]) / w),
          static_cast<float>((h_[3] * p.x + h_[4] * p.y + h_[5]) / w)};
}
