"""第4步 由吃水、纵倾和横倾计算相机光心高出实际水面的高度。"""

import numpy as np
import pandas as pd

from config import (
    ATTITUDE_FILE,
    CAMERA_HEIGHT_ABOVE_DESIGN_WATERLINE_M,
    CAMERA_X_FROM_MIDSHIP_M,
    CAMERA_Y_FROM_CENTERLINE_M,
    DESIGN_DRAFT_M,
    END_TIME_UTC,
    OUTPUT_DIR,
    REFERENCE_CAMERA_ID,
    START_TIME_UTC,
)


def calculate_camera_height(attitude: pd.DataFrame) -> pd.DataFrame:
    """计算相机高出实际水面的高度。

    坐标系：x向船艏、y向右舷、z向上。
    纵倾为正表示船艏上抬，横倾为正表示右舷下沉。
    """
    pitch = np.radians(attitude["trim_deg"].to_numpy(dtype=float))
    roll = np.radians(attitude["heel_deg"].to_numpy(dtype=float))

    # 设计水线在船舯处高出当前实际水面的距离。
    draft_correction = DESIGN_DRAFT_M - attitude["d_mean"].to_numpy(dtype=float)

    # 相机位置向量经船体纵倾/横倾后在竖直方向上的分量。
    vertical_from_design_waterline = (
        CAMERA_X_FROM_MIDSHIP_M * np.sin(pitch)
        - CAMERA_Y_FROM_CENTERLINE_M * np.cos(pitch) * np.sin(roll)
        + CAMERA_HEIGHT_ABOVE_DESIGN_WATERLINE_M * np.cos(pitch) * np.cos(roll)
    )

    result = pd.DataFrame(
        {
            "timestamp_utc": attitude["timestamp_utc"],
            "camera_id_reference": REFERENCE_CAMERA_ID,
            "d_fore_m": attitude["d_fore"].to_numpy(dtype=float),
            "d_aft_m": attitude["d_aft"].to_numpy(dtype=float),
            "d_mean_m": attitude["d_mean"].to_numpy(dtype=float),
            "ship_pitch_deg": attitude["trim_deg"].to_numpy(dtype=float),
            "ship_roll_deg": attitude["heel_deg"].to_numpy(dtype=float),
            "draft_correction_m": draft_correction,
            "vertical_from_design_waterline_m": vertical_from_design_waterline,
            "camera_height_above_water_m": draft_correction
            + vertical_from_design_waterline,
        }
    )
    return result


def build_camera_height() -> pd.DataFrame:
    columns = ["timestamp", "d_fore", "d_aft", "d_mean", "trim_deg", "heel_deg"]
    attitude = pd.read_csv(ATTITUDE_FILE, usecols=columns)
    attitude["timestamp_utc"] = pd.to_datetime(attitude.pop("timestamp"), utc=True)
    start, end = pd.Timestamp(START_TIME_UTC), pd.Timestamp(END_TIME_UTC)
    attitude = attitude[attitude["timestamp_utc"].between(start, end)].copy()

    if attitude.empty:
        raise ValueError("指定时间段内没有吃水数据")
    if attitude[columns[1:]].isna().any().any():
        raise ValueError("吃水或姿态数据中存在空值")
    return calculate_camera_height(attitude).reset_index(drop=True)


def main() -> None:
    height = build_camera_height()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUTPUT_DIR / "step04_camera_height_1hz.csv"
    height.to_csv(path, index=False, encoding="utf-8-sig")
    values = height["camera_height_above_water_m"]
    print(
        f"相机架高：{len(height)}行，"
        f"{values.min():.3f} ~ {values.max():.3f} m，平均{values.mean():.3f} m"
    )
    print(f"已写入：{path}")


if __name__ == "__main__":
    main()
