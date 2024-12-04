"""Print bins in eV without changes in the numbers precision.

Was required to OpenMC testing.
"""

from __future__ import annotations

import numpy as np

original_bins_str = """
1.00001e-07  4.13994e-07  5.31579e-07  6.82560e-07
          8.76425e-07  1.12535e-06  1.44498e-06  1.85539e-06  2.38237e-06
          3.05902e-06  3.92786e-06  5.04348e-06  6.47595e-06  8.31529e-06
          1.06770e-05  1.37096e-05  1.76035e-05  2.26033e-05  2.90232e-05
          3.72665e-05  4.78512e-05  6.14421e-05  7.88932e-05  1.01301e-04
          1.30073e-04  1.67017e-04  2.14454e-04  2.75364e-04  3.53575e-04
          4.53999e-04  5.82947e-04  7.48518e-04  9.61117e-04  1.23410e-03
          1.58461e-03  2.03468e-03  2.24867e-03  2.48517e-03  2.61259e-03
          2.74654e-03  3.03539e-03  3.35463e-03  3.70744e-03  4.30742e-03
          5.53084e-03  7.10174e-03  9.11882e-03  1.05946e-02  1.17088e-02
          1.50344e-02  1.93045e-02  2.18749e-02  2.35786e-02  2.41755e-02
          2.47875e-02  2.60584e-02  2.70001e-02  2.85011e-02  3.18278e-02
          3.43067e-02  4.08677e-02  4.63092e-02  5.24752e-02  5.65622e-02
          6.73795e-02  7.20245e-02  7.94987e-02  8.25034e-02  8.65170e-02
          9.80365e-02  1.11090e-01  1.16786e-01  1.22773e-01  1.29068e-01
          1.35686e-01  1.42642e-01  1.49956e-01  1.57644e-01  1.65727e-01
          1.74224e-01  1.83156e-01  1.92547e-01  2.02419e-01  2.12797e-01
          2.23708e-01  2.35177e-01  2.47235e-01  2.73237e-01  2.87246e-01
          2.94518e-01  2.97211e-01  2.98491e-01  3.01974e-01  3.33733e-01
          3.68832e-01  3.87742e-01  4.07622e-01  4.50492e-01  4.97871e-01
          5.23397e-01  5.50232e-01  5.78443e-01  6.08101e-01  6.39279e-01
          6.72055e-01  7.06512e-01  7.42736e-01  7.80817e-01  8.20850e-01
          8.62936e-01  9.07180e-01  9.61672e-01  1.00259e+00  1.10803e+00
          1.16484e+00  1.22456e+00  1.28735e+00  1.35335e+00  1.42274e+00
          1.49569e+00  1.57237e+00  1.65299e+00  1.73774e+00  1.82684e+00
          1.92050e+00  2.01897e+00  2.12248e+00  2.23130e+00  2.30693e+00
          2.34570e+00  2.36533e+00  2.38513e+00  2.46597e+00  2.59240e+00
          2.72532e+00  2.86505e+00  3.01194e+00  3.16637e+00  3.32871e+00
          3.67879e+00  4.06570e+00  4.49329e+00  4.72367e+00  4.96585e+00
          5.22046e+00  5.48812e+00  5.76950e+00  6.06531e+00  6.37628e+00
          6.59241e+00  6.70320e+00  7.04688e+00  7.40818e+00  7.78801e+00
          8.18731e+00  8.60708e+00  9.04837e+00  9.51229e+00  1.00000e+01
          1.05127e+01  1.10517e+01  1.16183e+01  1.22140e+01  1.25232e+01
          1.28403e+01  1.34986e+01  1.38403e+01  1.41907e+01  1.45499e+01
          1.49182e+01  1.56831e+01  1.64872e+01  1.69046e+01  1.73325e+01
          1.96403e+01
"""

original_bins = np.fromiter(map(float, original_bins_str.split()), dtype=np.float32)

in_evs = (f"{x:.5e}" for x in original_bins * 1e6)

print(*in_evs)
