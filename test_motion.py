import unittest

import numpy as np
import pandas as pd

from rotation_utils import (
    euler_zyx_to_matrix,
    extrinsic_to_body_camera_rotation,
    matrix_to_euler_zyx,
)
from step04_build_camera_height import calculate_camera_height


class RotationTests(unittest.TestCase):
    def test_euler_round_trip(self):
        matrix = euler_zyx_to_matrix(350.0, 1.0, -2.0)
        yaw, pitch, roll = matrix_to_euler_zyx(matrix)
        np.testing.assert_allclose([yaw, pitch, roll], [350.0, 1.0, -2.0], atol=1e-9)

    def test_front0_mount_is_forward_and_down(self):
        rvec = np.array([1.797667, -0.003864, 0.001528])
        matrix = extrinsic_to_body_camera_rotation(rvec)
        yaw, pitch, roll = matrix_to_euler_zyx(matrix)
        np.testing.assert_allclose([yaw, pitch, roll], [0.18, -13.00, 0.06], atol=0.03)


class CameraHeightTests(unittest.TestCase):
    def test_level_ship_at_design_draft(self):
        attitude = pd.DataFrame(
            {
                "timestamp_utc": [pd.Timestamp("2025-10-17T09:00:01Z")],
                "d_fore": [11.7],
                "d_aft": [11.7],
                "d_mean": [11.7],
                "trim_deg": [0.0],
                "heel_deg": [0.0],
            }
        )
        result = calculate_camera_height(attitude)
        self.assertAlmostEqual(result.camera_height_above_water_m.iloc[0], 27.25)


if __name__ == "__main__":
    unittest.main()
