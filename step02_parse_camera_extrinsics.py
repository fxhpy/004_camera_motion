"""第2步 解析相机外参 得到相机相对船体的固定安装姿态。"""

import numpy as np
import pandas as pd

from config import (
    CAMERA_HEIGHT_ABOVE_DESIGN_WATERLINE_M,
    CAMERA_PARAM_DIR,
    CAMERA_X_FROM_MIDSHIP_M,
    CAMERA_Y_FROM_CENTERLINE_M,
    EXPECTED_CAMERA_COUNT,
    OUTPUT_DIR,
)
from rotation_utils import extrinsic_to_body_camera_rotation, matrix_to_euler_zyx


def parse_extrinsic_file(path) -> dict:
    values = np.fromstring(path.read_text(encoding="utf-8").splitlines()[0], sep=",")
    if len(values) != 6:
        raise ValueError(f"{path.name} 首行应有6个数 实际为{len(values)}个")

    rvec, tvec = values[:3], values[3:]
    body_from_camera = extrinsic_to_body_camera_rotation(rvec)
    yaw, pitch, roll = matrix_to_euler_zyx(body_from_camera)
    
    row = {
        "camera_id": path.stem.replace("ExtrinsicParams", ""),
        "extrinsic_file": path.name,
        "mount_yaw_deg": yaw,
        "mount_pitch_deg": pitch,
        "mount_roll_deg": roll,
        "rvec_x": rvec[0], "rvec_y": rvec[1], "rvec_z": rvec[2],
        "tvec_x": tvec[0], "tvec_y": tvec[1], "tvec_z": tvec[2],
        "ship_x_from_midship_m": CAMERA_X_FROM_MIDSHIP_M,
        "ship_y_from_centerline_m": CAMERA_Y_FROM_CENTERLINE_M,
        "height_above_design_waterline_m": CAMERA_HEIGHT_ABOVE_DESIGN_WATERLINE_M,
    }
    for i in range(3):
        for j in range(3):
            row[f"r{i}{j}"] = body_from_camera[i, j]
    return row


def build_camera_mounts() -> pd.DataFrame:
    files = sorted(CAMERA_PARAM_DIR.glob("ExtrinsicParams*.txt"))
    if not files:
        raise FileNotFoundError(f"没有找到相机外参：{CAMERA_PARAM_DIR}")
    mounts = pd.DataFrame([parse_extrinsic_file(path) for path in files])
    if len(mounts) != EXPECTED_CAMERA_COUNT:
        print(f"注意：说明写{EXPECTED_CAMERA_COUNT}路相机，但实际发现{len(mounts)}份外参，当前全部处理。")
    return mounts


def main() -> None:
    mounts = build_camera_mounts()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUTPUT_DIR / "step02_camera_mounts.csv"
    mounts.to_csv(path, index=False, encoding="utf-8-sig")
    print(mounts[["camera_id", "mount_yaw_deg", "mount_pitch_deg", "mount_roll_deg"]].to_string(index=False))
    print(f"已写入：{path}")


if __name__ == "__main__":
    main()
