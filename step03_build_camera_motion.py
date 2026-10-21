"""第3步 组合船体姿态与相机安装旋转 生成相机 Yaw/Pitch/Roll。"""

import numpy as np
import pandas as pd

from config import OUTPUT_DIR
from rotation_utils import euler_zyx_to_matrix, matrix_to_euler_zyx


def matrix_from_mount_row(row) -> np.ndarray:
    return np.array([[getattr(row, f"r{i}{j}") for j in range(3)] for i in range(3)])


def build_one_camera(ship: pd.DataFrame, mount_row) -> pd.DataFrame:
    mount_rotation = matrix_from_mount_row(mount_row)
    camera_angles = []
    for row in ship.itertuples(index=False):
        navigation_from_ship = euler_zyx_to_matrix(
            row.ship_yaw_deg, row.ship_pitch_deg, row.ship_roll_deg
        )
        navigation_from_camera = navigation_from_ship @ mount_rotation ## 核心运算
        camera_angles.append(matrix_to_euler_zyx(navigation_from_camera))

    angles = np.asarray(camera_angles)
    result = ship.copy()
    result.insert(1, "camera_id", mount_row.camera_id)
    result["camera_yaw_deg"] = angles[:, 0]
    result["camera_pitch_deg"] = angles[:, 1]
    result["camera_roll_deg"] = angles[:, 2]
    return result


def build_camera_motion(ship: pd.DataFrame, mounts: pd.DataFrame) -> pd.DataFrame:
    frames = [build_one_camera(ship, row) for row in mounts.itertuples(index=False)]
    return pd.concat(frames, ignore_index=True)


def main() -> None:
    ship = pd.read_csv(OUTPUT_DIR / "step01_ship_motion.csv", parse_dates=["timestamp_utc"])
    mounts = pd.read_csv(OUTPUT_DIR / "step02_camera_mounts.csv")
    motion = build_camera_motion(ship, mounts)

    all_path = OUTPUT_DIR / "step03_camera_motion_all.csv"
    motion.to_csv(all_path, index=False, encoding="utf-8-sig")
    for camera_id, group in motion.groupby("camera_id"):
        group.to_csv(OUTPUT_DIR / f"camera_{camera_id}_motion.csv", index=False, encoding="utf-8-sig")
    print(f"相机姿态：{motion.camera_id.nunique()}台，共{len(motion)}行")
    print(f"已写入：{all_path}")


if __name__ == "__main__":
    main()
