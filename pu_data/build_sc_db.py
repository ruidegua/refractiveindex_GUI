"""Build the local Sc (Scandium) optical-constants YAML from the source PDF.

Source: "Optical Constants of Sc" — Table 2.28 from "Optical Constants
of Sc" book/handbook (p. 130-131). Polycrystalline Sc at 300 K.

Citations in the source:
  [1] M. Sigrist, G. Chassaing, J. C. François, F. Antonangeli, N. Zema,
      and M. Piacentini, Phys. Rev. B 35, 3760 (1987).
  [2] J. I. Larruquert, J. A. Aznárez, J. A. Méndez, A. M. Malvezzi,
      L. Poletto, and S. Covini, Appl. Opt. 43, 3271 (2004).
  [3] B. L. Henke, E. M. Gullikson, and J. C. Davis, At. Data Nucl. Data
      Tables 54, 181 (1993); http://henke.lbl.gov/optical_constants.

This script reads the raw tabulated n,k data (eV → converted to µm),
writes the data YAML to pu_data/db/Sc/Sc-Sigrist.yml, and creates the
catalog entry to pu_data/db/catalog-sc.yml.

Run from anywhere; output paths are computed relative to this file.

Usage
-----
    python build_sc_db.py          # write YAML + catalog
    python build_sc_db.py --verify # also print a quick n/k sanity check
"""

from __future__ import annotations

import sys
from pathlib import Path
from textwrap import dedent

# (eV, n, k) — extracted verbatim from the source table. Rows where n
# or k is missing in the source (0.23 eV and 0.25 eV, only ε₂ listed)
# are excluded -- the loader needs n and k to produce optical constants.
SC_DATA_EV_NK: list[tuple[float, float, float]] = [
    # --- low-energy block (Sigrist 1987 / Larruquert 2004) ---
    (0.27, 3.595,   9.558),
    (0.29, 3.486,   8.791),
    (0.31, 3.392,   8.272),
    (0.33, 3.377,   7.711),
    (0.35, 3.302,   7.256),
    (0.37, 3.273,   6.838),
    (0.39, 3.232,   6.437),
    (0.41, 3.258,   6.097),
    (0.43, 3.229,   5.761),
    (0.45, 3.223,   5.477),
    (0.47, 3.269,   5.208),
    (0.49, 3.265,   5.021),
    (0.51, 3.296,   4.783),
    (0.53, 3.269,   4.630),
    (0.55, 3.309,   4.478),
    (0.60, 3.427,   4.176),
    (0.65, 3.554,   3.974),
    (0.70, 3.654,   3.848),
    (0.75, 3.699,   3.767),
    (0.80, 3.729,   3.720),
    (0.85, 3.735,   3.680),
    (0.90, 3.718,   3.655),
    (0.95, 3.685,   3.628),
    (1.0,  3.656,   3.639),
    (1.2,  3.395,   3.632),
    (1.4,  3.104,   3.574),
    (1.6,  2.793,   3.467),
    (1.8,  2.475,   3.315),
    (2.0,  2.167,   3.113),
    (2.2,  1.889,   2.861),
    (2.4,  1.656,   2.571),
    (2.6,  1.490,   2.273),
    (2.8,  1.421,   2.017),
    (3.0,  1.474,   1.882),
    (3.5,  1.519,   1.722),
    (4.0,  1.368,   1.622),
    (4.5,  1.281,   1.353),
    (5.0,  1.285,   1.261),
    (5.5,  1.331,   1.333),
    (6.0,  1.309,   1.324),
    (6.5,  1.236,   1.262),
    (7.0,  1.127,   1.171),
    (7.5,  0.997,   1.080),
    (8.0,  0.871,   1.028),
    (8.5,  0.779,   0.969),
    (9.0,  0.775,   0.913),
    (9.5,  0.791,   0.945),
    (10.0, 0.705,   0.865),
    (10.5, 0.643,   0.780),
    (11.0, 0.564,   0.689),
    (11.5, 0.560,   0.706),
    (12.0, 0.509,   0.449),
    (12.5, 0.524,   0.390),
    (13.0, 0.544,   0.400),
    (13.5, 0.561,   0.322),
    (14.0, 0.589,   0.290),
    (14.5, 0.619,   0.295),
    (15.0, 0.648,   0.290),
    (15.5, 0.681,   0.255),
    (16.0, 0.717,   0.203),
    (16.5, 0.755,   0.151),
    (17.0, 0.788,   0.114),
    (17.5, 0.812,   0.095),
    (18.0, 0.828,   0.087),
    (18.5, 0.841,   0.083),
    (19.0, 0.854,   0.078),
    (19.5, 0.867,   0.072),
    (20.0, 0.880,   0.066),
    (20.5, 0.892,   0.060),
    (21.0, 0.905,   0.054),
    (21.5, 0.916,   0.049),
    (22.0, 0.928,   0.045),
    (22.5, 0.938,   0.042),
    (23.0, 0.948,   0.041),
    # --- high-energy block (Henke 1993) ---
    (30.00, 1.1441,    8.35e-2),
    (30.88, 1.1440,    1.00e-1),
    (31.79, 1.1537,    1.07e-1),
    (32.73, 1.1739,    1.29e-1),
    (33.70, 1.1858,    1.67e-1),
    (34.69, 1.1785,    2.13e-1),
    (35.71, 1.1687,    2.46e-1),
    (36.76, 1.1454,    2.89e-1),
    (37.85, 1.1022,    3.27e-1),
    (38.96, 1.0538,    3.45e-1),
    (40.11, 1.0011,    3.57e-1),
    (41.29, 0.9421,    3.54e-1),
    (42.51, 0.8842,    3.30e-1),
    (43.76, 0.8358,    2.91e-1),
    (45.05, 0.8043,    2.39e-1),
    (46.38, 0.7943,    1.84e-1),
    (47.75, 0.7952,    1.43e-1),
    (49.15, 0.8057,    1.02e-1),
    (50.60, 0.8260,    6.89e-2),
    (52.09, 0.8470,    5.11e-2),
    (53.63, 0.8644,    3.87e-2),
    (55.21, 0.8795,    2.99e-2),
    (56.84, 0.8929,    2.32e-2),
    (58.51, 0.9046,    1.86e-2),
    (60.24, 0.9149,    1.51e-2),
    (62.01, 0.9239,    1.30e-2),
    (63.84, 0.9316,    1.16e-2),
    (65.72, 0.9383,    1.06e-2),
    (67.66, 0.9441,    1.01e-2),
    (69.65, 0.9491,    9.69e-3),
    (71.71, 0.9535,    9.37e-3),
    (73.82, 0.9574,    9.16e-3),
    (75.99, 0.9608,    9.06e-3),
    (78.23, 0.9638,    9.00e-3),
    (80.54, 0.9665,    8.95e-3),
    (82.91, 0.9688,    8.91e-3),
    (85.36, 0.9709,    8.83e-3),
    (87.87, 0.9728,    8.72e-3),
    (90.46, 0.9745,    8.61e-3),
    (93.13, 0.9760,    8.50e-3),
    (95.87, 0.9773,    8.39e-3),
    (98.70, 0.9784,    8.19e-3),
    (101.6, 0.9795,    7.91e-3),
    (104.6, 0.9805,    7.58e-3),
    (107.7, 0.9815,    7.25e-3),
    (110.9, 0.9824,    6.84e-3),
    (114.1, 0.9834,    6.46e-3),
    (117.5, 0.9843,    6.12e-3),
    (121.0, 0.9852,    5.87e-3),
    (124.5, 0.9860,    5.68e-3),
    (128.2, 0.9867,    5.51e-3),
    (132.0, 0.9873,    5.33e-3),
    (135.9, 0.9879,    5.08e-3),
    (139.9, 0.9884,    4.79e-3),
    (144.0, 0.9890,    4.51e-3),
    (148.2, 0.9895,    4.23e-3),
    (152.6, 0.9900,    3.96e-3),
    (157.1, 0.9905,    3.70e-3),
    (161.7, 0.9910,    3.47e-3),
    (166.5, 0.9915,    3.25e-3),
    (171.4, 0.9919,    3.06e-3),
    (176.4, 0.9924,    2.88e-3),
    (181.6, 0.9927,    2.71e-3),
    (187.0, 0.9931,    2.52e-3),
    (192.5, 0.9935,    2.34e-3),
    (198.2, 0.9938,    2.17e-3),
    (204.0, 0.9942,    2.00e-3),
    (210.0, 0.9945,    1.85e-3),
    (216.2, 0.9948,    1.72e-3),
    (222.6, 0.9952,    1.60e-3),
    (229.2, 0.9955,    1.49e-3),
    (235.9, 0.9957,    1.39e-3),
    (242.9, 0.9960,    1.29e-3),
    (250.0, 0.9963,    1.19e-3),
    (257.4, 0.9965,    1.10e-3),
    (265.0, 0.9967,    1.01e-3),
    (272.8, 0.9970,    9.29e-4),
    (280.8, 0.9972,    8.55e-4),
    (289.1, 0.9974,    7.86e-4),
    (297.6, 0.9977,    7.22e-4),
    (306.4, 0.9979,    6.64e-4),
    (315.4, 0.9981,    6.10e-4),
    (324.7, 0.9983,    5.59e-4),
    (334.3, 0.9986,    5.11e-4),
    (344.1, 0.9988,    4.68e-4),
    (354.3, 0.9991,    4.28e-4),
    (364.7, 0.9995,    3.92e-4),
    (375.5, 1.0000,    3.59e-4),
    (386.5, 1.0008,    3.29e-4),
    (397.9, 1.0054,    8.19e-4),
    (409.7, 0.9966,    4.14e-3),
    (421.7, 0.9983,    2.05e-3),
    (434.2, 0.9986,    2.06e-3),
    (447.0, 0.9985,    1.86e-3),
    (460.1, 0.9987,    1.72e-3),
    (473.7, 0.9986,    1.69e-3),
    (487.6, 0.9986,    1.49e-3),
    (502.0, 0.9987,    1.51e-3),
    (516.8, 0.9986,    1.44e-3),
    (532.0, 0.9986,    1.28e-3),
    (547.7, 0.9987,    1.21e-3),
    (563.9, 0.9986,    1.12e-3),
    (580.5, 0.9987,    9.96e-4),
    (597.6, 0.9987,    9.25e-4),
    (615.2, 0.9988,    8.48e-4),
    (633.3, 0.9988,    7.68e-4),
    (652.0, 0.9989,    7.05e-4),
    (671.2, 0.9989,    6.45e-4),
    (691.0, 0.9989,    5.87e-4),
    (711.4, 0.9990,    5.34e-4),
    (732.3, 0.99903,   4.88e-4),
    (753.9, 0.99908,   4.45e-4),
    (776.1, 0.99912,   4.06e-4),
    (799.0, 0.99916,   3.70e-4),
    (822.5, 0.99920,   3.37e-4),
    (846.8, 0.99924,   3.07e-4),
    (871.7, 0.99927,   2.78e-4),
    (897.4, 0.99931,   2.52e-4),
    (923.9, 0.99934,   2.28e-4),
    (951.1, 0.99938,   2.05e-4),
    (979.1, 0.99941,   1.86e-4),
    (1008,  0.99944,   1.68e-4),
    (1038,  0.99947,   1.52e-4),
    (1068,  0.99950,   1.38e-4),
    (1100,  0.99953,   1.25e-4),
    (1132,  0.99955,   1.13e-4),
    (1166,  0.99958,   1.02e-4),
    (1200,  0.99960,   9.17e-5),
    (1235,  0.99962,   8.27e-5),
    (1272,  0.99964,   7.45e-5),
    (1309,  0.99966,   6.72e-5),
    (1348,  0.99968,   6.05e-5),
    (1387,  0.99970,   5.46e-5),
    (1428,  0.99972,   4.92e-5),
    (1470,  0.99973,   4.43e-5),
    (1514,  0.99975,   4.00e-5),
    (1558,  0.99976,   3.60e-5),
    (1604,  0.99978,   3.25e-5),
    (1652,  0.99979,   2.93e-5),
    (1700,  0.99980,   2.64e-5),
    (1750,  0.99981,   2.38e-5),
    (1802,  0.99982,   2.15e-5),
    (1855,  0.99983,   1.93e-5),
    (1910,  0.99984,   1.74e-5),
    (1966,  0.99985,   1.56e-5),
    (2024,  0.99986,   1.41e-5),
    (2084,  0.99987,   1.27e-5),
    (2145,  0.99988,   1.14e-5),
    (2208,  0.99988,   1.02e-5),
    (2273,  0.99989,   9.20e-6),
    (2340,  0.99990,   8.28e-6),
    (2409,  0.999903,  7.44e-6),
    (2480,  0.999909,  6.69e-6),
    (2553,  0.999914,  6.02e-6),
    (2629,  0.999919,  5.41e-6),
    (2706,  0.999924,  4.87e-6),
    (2786,  0.999929,  4.38e-6),
    (2868,  0.999933,  3.93e-6),
    (2953,  0.999937,  3.53e-6),
    (3040,  0.999940,  3.17e-6),
    (3129,  0.999944,  2.84e-6),
    (3221,  0.999947,  2.55e-6),
    (3316,  0.999950,  2.29e-6),
    (3414,  0.999953,  2.05e-6),
    (3515,  0.999956,  1.84e-6),
    (3618,  0.999959,  1.65e-6),
    (3725,  0.999962,  1.48e-6),
    (3835,  0.999964,  1.33e-6),
    (3948,  0.999966,  1.19e-6),
    (4064,  0.999969,  1.06e-6),
    (4184,  0.999971,  9.51e-7),
    (4307,  0.999973,  8.51e-7),
    (4434,  0.999977,  7.61e-7),
    (4565,  0.999977,  5.32e-6),
    (4699,  0.999977,  4.80e-6),
    (4838,  0.999977,  4.34e-6),
    (4980,  0.999978,  3.92e-6),
    (5127,  0.999979,  3.54e-6),
    (5278,  0.999980,  3.20e-6),
    (5434,  0.999981,  2.89e-6),
    (5594,  0.999982,  2.61e-6),
    (5759,  0.999983,  2.35e-6),
    (5928,  0.999984,  2.11e-6),
    (6103,  0.999985,  1.90e-6),
    (6283,  0.999985,  1.71e-6),
    (6468,  0.999986,  1.54e-6),
    (6659,  0.999987,  1.38e-6),
    (6855,  0.999988,  1.24e-6),
    (7057,  0.999988,  1.12e-6),
    (7265,  0.999989,  1.00e-6),
    (7479,  0.999989,  9.02e-7),
    (7700,  0.9999901, 8.09e-7),
    (7927,  0.9999906, 7.25e-7),
    (8160,  0.9999911, 6.50e-7),
    (8401,  0.9999916, 5.82e-7),
    (8648,  0.9999921, 5.22e-7),
    (8903,  0.9999925, 4.68e-7),
    (9166,  0.9999930, 4.19e-7),
    (9436,  0.9999934, 3.76e-7),
    (9714,  0.9999937, 3.37e-7),
    (10000, 0.9999941, 3.02e-7),
]

# Table 2.29: Single-crystalline Sc, E perpendicular to c (basal plane),
# 4.2 K. Source [4] (Weaver, Krafka, Lynch, Koch 1981).
SC_DATA_EV_NK_E_PERP_C: list[tuple[float, float, float]] = [
    (0.10, 5.05,  23.2),
    (0.13, 4.02,  18.8),
    (0.15, 3.49,  15.7),
    (0.17, 3.06,  13.5),
    (0.20, 2.74,  11.8),
    (0.25, 2.54,   9.25),
    (0.30, 2.44,   7.55),
    (0.35, 2.49,   6.29),
    (0.40, 2.56,   5.34),
    (0.45, 2.72,   4.56),
    (0.50, 3.05,   3.94),
    (0.55, 3.37,   3.68),
    (0.60, 3.54,   3.65),
    (0.65, 3.55,   3.64),
    (0.70, 3.49,   3.60),
    (0.75, 3.42,   3.48),
    (0.80, 3.39,   3.37),
    (0.85, 3.39,   3.31),
    (0.90, 3.37,   3.26),
    (0.95, 3.34,   3.24),
    (1.00, 3.30,   3.23),
    (1.05, 3.25,   3.24),
    (1.10, 3.18,   3.25),
    (1.15, 3.10,   3.24),
    (1.20, 3.02,   3.24),
    (1.25, 2.93,   3.23),
    (1.30, 2.84,   3.20),
    (1.35, 2.76,   3.17),
    (1.40, 2.74,   3.10),
    (1.45, 2.69,   3.16),
    (1.50, 2.61,   3.16),
    (1.55, 2.53,   3.17),
    (1.60, 2.44,   3.18),
    (1.65, 2.33,   3.19),
    (1.70, 2.21,   3.18),
    (1.75, 2.09,   3.15),
    (1.80, 1.98,   3.11),
    (1.85, 1.87,   3.05),
    (1.90, 1.77,   2.99),
    (1.95, 1.69,   2.91),
    (2.00, 1.62,   2.84),
    (2.05, 1.57,   2.77),
    (2.10, 1.52,   2.71),
    (2.15, 1.47,   2.66),
    (2.20, 1.41,   2.62),
    (2.25, 1.34,   2.55),
    (2.30, 1.29,   2.48),
    (2.35, 1.24,   2.42),
    (2.40, 1.21,   2.34),
    (2.45, 1.17,   2.28),
    (2.50, 1.14,   2.21),
    (2.60, 1.11,   2.08),
    (2.70, 1.09,   1.96),
    (2.80, 1.08,   1.85),
    (2.90, 1.08,   1.76),
    (3.00, 1.09,   1.67),
    (3.10, 1.10,   1.60),
    (3.20, 1.13,   1.53),
    (3.30, 1.16,   1.49),
    (3.40, 1.19,   1.48),
    (3.50, 1.19,   1.49),
    (3.60, 1.17,   1.49),
    (3.70, 1.14,   1.48),
    (3.80, 1.10,   1.46),
    (3.90, 1.05,   1.42),
    (4.00, 1.02,   1.38),
    (4.10, 0.99,   1.32),
    (4.20, 0.98,   1.27),
    (4.30, 0.97,   1.22),
    (4.40, 0.97,   1.17),
    (4.50, 0.97,   1.13),
    (4.60, 0.98,   1.08),
    (4.70, 1.00,   1.04),
    (4.80, 1.03,   1.01),
    (4.90, 1.05,   1.00),
    (5.00, 1.07,   0.99),
]

# Table 2.30: Single-crystalline Sc, E parallel to c (optic axis),
# 4.2 K. Source [4] (Weaver, Krafka, Lynch, Koch 1981).
SC_DATA_EV_NK_E_PAR_C: list[tuple[float, float, float]] = [
    (0.10, 5.05,  32.05),
    (0.13, 3.82,  26.01),
    (0.15, 3.08,  21.89),
    (0.17, 2.59,  18.93),
    (0.20, 2.21,  16.12),
    (0.25, 1.65,  13.26),
    (0.30, 1.43,  10.93),
    (0.35, 1.32,   9.24),
    (0.40, 1.28,   7.94),
    (0.45, 1.33,   6.93),
    (0.50, 1.36,   6.14),
    (0.55, 1.44,   5.49),
    (0.60, 1.49,   4.98),
    (0.65, 1.55,   4.54),
    (0.70, 1.62,   4.18),
    (0.75, 1.66,   3.88),
    (0.80, 1.69,   3.61),
    (0.85, 1.76,   3.35),
    (0.90, 1.81,   3.15),
    (0.95, 1.87,   2.95),
    (1.00, 1.96,   2.80),
    (1.05, 2.01,   2.70),
    (1.10, 2.05,   2.60),
    (1.15, 2.08,   2.50),
    (1.20, 2.11,   2.40),
    (1.25, 2.15,   2.30),
    (1.30, 2.21,   2.21),
    (1.35, 2.28,   2.13),
    (1.40, 2.37,   2.08),
    (1.45, 2.47,   2.06),
    (1.50, 2.56,   2.07),
    (1.55, 2.65,   2.12),
    (1.60, 2.73,   2.19),
    (1.65, 2.77,   2.31),
    (1.70, 2.77,   2.43),
    (1.75, 2.72,   2.56),
    (1.80, 2.65,   2.66),
    (1.85, 2.54,   2.75),
    (1.90, 2.41,   2.80),
    (1.95, 2.30,   2.82),
    (2.00, 2.19,   2.83),
    (2.05, 2.08,   2.82),
    (2.10, 1.98,   2.81),
    (2.15, 1.89,   2.80),
    (2.20, 1.80,   2.79),
    (2.25, 1.70,   2.78),
    (2.30, 1.59,   2.75),
    (2.35, 1.47,   2.70),
    (2.40, 1.37,   2.63),
    (2.45, 1.29,   2.55),
    (2.50, 1.22,   2.46),
    (2.60, 1.13,   2.29),
    (2.70, 1.08,   2.14),
    (2.80, 1.05,   2.01),
    (2.90, 1.04,   1.90),
    (3.00, 1.04,   1.80),
    (3.10, 1.04,   1.71),
    (3.20, 1.06,   1.63),
    (3.30, 1.08,   1.57),
    (3.40, 1.11,   1.54),
    (3.50, 1.11,   1.54),
    (3.60, 1.09,   1.52),
    (3.70, 1.06,   1.51),
    (3.80, 1.02,   1.48),
    (3.90, 0.99,   1.43),
    (4.00, 0.96,   1.39),
    (4.10, 0.94,   1.33),
    (4.20, 0.93,   1.28),
    (4.30, 0.92,   1.23),
    (4.40, 0.92,   1.18),
    (4.50, 0.93,   1.13),
    (4.60, 0.94,   1.09),
    (4.70, 0.95,   1.05),
    (4.80, 0.97,   1.02),
    (4.90, 0.99,   1.00),
    (5.00, 1.01,   0.99),
]

# All sources in build order. Each entry: (output_filename, data_rows,
# header_lines). Header lines are written as YAML comments at the top of
# the data file (table caption, citations, conversion note).
SC_SOURCES: list[tuple[str, list[tuple[float, float, float]], list[str]]] = [
    (
        "Sc-Sigrist.yml",
        SC_DATA_EV_NK,
        [
            "Scandium (Sc) optical constants -- polycrystalline, 300 K",
            "Source: 'Optical Constants of Sc' handbook, Table 2.28 (p. 130-131)",
            "",
            "References:",
            "  [1] Sigrist et al., Phys. Rev. B 35, 3760 (1987)",
            "        (low-energy block, 0.27-23 eV)",
            "  [2] Larruquert et al., Appl. Opt. 43, 3271 (2004)",
            "  [3] Henke, Gullikson, Davis, At. Data Nucl. Data Tables 54, 181 (1993)",
            "        http://henke.lbl.gov/optical_constants",
            "        (high-energy block, 30-10000 eV)",
        ],
    ),
    (
        "Sc-Eperp-c-4K.yml",
        SC_DATA_EV_NK_E_PERP_C,
        [
            "Scandium (Sc) optical constants -- single crystal, E perpendicular to c,",
            "                                    4.2 K",
            "Source: 'Optical Constants of Sc' handbook, Table 2.29 (p. 131-132)",
            "",
            "Reference:",
            "  [4] J. H. Weaver, C. Krafka, D. W. Lynch, and E. E. Koch,",
            "      Physik Daten -- Optical Properties of Metals",
            "      (Fachinformationszentrum, Karlsruhe, 1981), Vol. 18-2, p. 83.",
        ],
    ),
    (
        "Sc-Epar-c-4K.yml",
        SC_DATA_EV_NK_E_PAR_C,
        [
            "Scandium (Sc) optical constants -- single crystal, E parallel to c,",
            "                                    4.2 K",
            "Source: 'Optical Constants of Sc' handbook, Table 2.30 (p. 132-133)",
            "",
            "Reference:",
            "  [4] J. H. Weaver, C. Krafka, D. W. Lynch, and E. E. Koch,",
            "      Physik Daten -- Optical Properties of Metals",
            "      (Fachinformationszentrum, Karlsruhe, 1981), Vol. 18-2, p. 83.",
        ],
    ),
]

# Photon energy (eV) -> wavelength (µm): λ(µm) = 1.23984193 / E(eV)
EV_TO_UM = 1.23984193


def _format_value(v: float) -> str:
    """Match delta-Pu.yml formatting: 6 sig figs, fixed when reasonable."""
    if v == 0:
        return "0"
    if abs(v) < 1e-3 or abs(v) >= 1e4:
        return f"{v:.3e}"
    return f"{v:.6f}".rstrip("0").rstrip(".")


def _build_data_yaml(rows: list[tuple[float, float, float]],
                     header_lines: list[str]) -> str:
    """Convert (eV, n, k) tuples into the refractiveindex YAML body."""
    data_lines = []
    for ev, n, k in rows:
        wl_um = EV_TO_UM / ev
        # Indent by 6 spaces to match delta-Pu.yml convention
        # (DATA: -> "- " + 4 spaces for block scalar content)
        data_lines.append(f"      {wl_um:.6f}  {_format_value(n)}  {_format_value(k)}")
    body = "\n".join(data_lines)
    wl_lo = EV_TO_UM / rows[-1][0]   # highest eV -> shortest λ
    wl_hi = EV_TO_UM / rows[0][0]    # lowest eV -> longest λ
    header = "\n".join(f"# {line}" for line in header_lines)
    return (
        f"{header}\n"
        "#\n"
        "# Original data in photon energy (eV); converted to wavelength (um)\n"
        "# via lambda(um) = 1.23984193 / E(eV). Wavelengths are non-uniform\n"
        "# because the source table is sampled uniformly in energy.\n"
        "#\n"
        "DATA:\n"
        "  - type: tabulated nk\n"
        f"    wavelength_range: {wl_lo:.6f} {wl_hi:.6f}\n"
        "    data: |\n"
        f"{body}\n"
    )


def _build_catalog_yml() -> str:
    """Compose catalog-sc.yml with one shelf and three books."""
    return dedent("""\
        # Local Sc (Scandium) optical constants catalog
        # Source: 'Optical Constants of Sc' handbook, Tables 2.28-2.30
        # Format matches refractiveindex.info catalog-nk.yml structure
        - SHELF: Sc
          name: Scandium (Sigrist 1987, Weaver 1981, Henke 1993)
          content:
            - BOOK: Sc-polycrystalline
              name: "Sc polycrystalline, 300 K - Sigrist 1987 + Henke 1993"
              content:
                - DIVIDER: "E = 0.27 to 10000 eV, lambda ~ 0.124 to 4591 nm"
                - PAGE: nk-Sigrist-Henke
                  name: "Sc n,k (Sigrist 1987 + Henke 1993, Table 2.28)"
                  data: Sc/Sc-Sigrist.yml
            - BOOK: Sc-single-crystal-Eperp-c
              name: "Sc single crystal, E perpendicular to c, 4.2 K - Weaver 1981"
              content:
                - DIVIDER: "E = 0.10 to 5.0 eV, lambda ~ 0.248 to 12.4 um"
                - PAGE: nk-Weaver-Eperp-c
                  name: "Sc n,k E perpendicular to c (Weaver 1981, Table 2.29)"
                  data: Sc/Sc-Eperp-c-4K.yml
            - BOOK: Sc-single-crystal-Epar-c
              name: "Sc single crystal, E parallel to c, 4.2 K - Weaver 1981"
              content:
                - DIVIDER: "E = 0.10 to 5.0 eV, lambda ~ 0.248 to 12.4 um"
                - PAGE: nk-Weaver-Epar-c
                  name: "Sc n,k E parallel to c (Weaver 1981, Table 2.30)"
                  data: Sc/Sc-Epar-c-4K.yml
        """)


def main() -> int:
    here = Path(__file__).resolve().parent
    sc_dir = here / "db" / "Sc"
    catalog_path = here / "db" / "catalog-sc.yml"

    sc_dir.mkdir(parents=True, exist_ok=True)

    # 1. write each data file
    for filename, rows, header_lines in SC_SOURCES:
        path = sc_dir / filename
        path.write_text(_build_data_yaml(rows, header_lines), encoding="utf-8")
        print(f"Wrote {path}  ({len(rows)} rows, "
              f"E = {rows[0][0]:g} - {rows[-1][0]:g} eV, "
              f"lambda = {EV_TO_UM / rows[-1][0]:.3e} - "
              f"{EV_TO_UM / rows[0][0]:.3f} um)")

    # 2. write the catalog
    catalog_path.write_text(_build_catalog_yml(), encoding="utf-8")
    print(f"Wrote {catalog_path}")

    if "--verify" in sys.argv:
        import yaml
        for filename, rows, _ in SC_SOURCES:
            with open(sc_dir / filename, encoding="utf-8") as f:
                doc = yaml.safe_load(f)
            block = doc["DATA"][0]
            parsed = [line.split() for line in block["data"].strip().splitlines()]
            assert len(parsed) == len(rows), (
                f"{filename}: row count mismatch {len(parsed)} != {len(rows)}"
            )
            bad = [r for r in parsed if float(r[1]) <= 0 or float(r[2]) < 0]
            if bad:
                print(f"  {filename}: WARN {len(bad)} rows have non-positive n or negative k")
                return 1
        # catalog sanity: should have 3 pages under Sc
        with open(catalog_path, encoding="utf-8") as f:
            cat = yaml.safe_load(f)
        sc = next(s for s in cat if s.get("SHELF") == "Sc")
        pages = [p for b in sc["content"] if "BOOK" in b
                 for p in b["content"] if "PAGE" in p]
        print(f"  catalog Sc pages: {len(pages)} (expected 3)")
        assert len(pages) == 3
        print("  verify: all OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())