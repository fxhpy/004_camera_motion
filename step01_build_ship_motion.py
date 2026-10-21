"""第1步 把真航向、纵倾和横倾合并成船体 Yaw/Pitch/Roll。"""

import numpy as np
import pandas as pd

from config import (
    ATTITUDE_FILE,
    END_TIME_UTC,
    HEADING_COLUMNS,
    HEADING_FILE,
    OUTPUT_DIR,
    START_TIME_UTC,
)


def interpolate_heading(source: pd.DataFrame, target_time: pd.Series) -> np.ndarray:
    """在单位圆上插值航向，避免 359° 到 1°经过180°。"""
    source_seconds = source["timestamp_utc"].astype("int64").to_numpy() / 1e9
    target_seconds = target_time.astype("int64").to_numpy() / 1e9
    heading_rad = np.radians(source["yaw_deg"].to_numpy(dtype=float))
    sin_value = np.interp(target_seconds, source_seconds, np.sin(heading_rad))
    cos_value = np.interp(target_seconds, source_seconds, np.cos(heading_rad))
    return np.degrees(np.arctan2(sin_value, cos_value)) % 360


def build_ship_motion() -> pd.DataFrame:
    heading_raw = pd.read_excel(HEADING_FILE) ## 读航向文件
    missing = [column for column in HEADING_COLUMNS if column not in heading_raw.columns]
    if missing:
        raise ValueError(f"heading.xlsx 缺少列：{missing}")
    heading = heading_raw[list(HEADING_COLUMNS)].rename(columns=HEADING_COLUMNS)
    heading["timestamp_utc"] = pd.to_datetime(heading["timestamp_utc"], utc=True)
    heading["yaw_deg"] = pd.to_numeric(heading["yaw_deg"], errors="coerce") ## 把所有错误转成NaN
    heading = heading.dropna().sort_values("timestamp_utc").drop_duplicates("timestamp_utc")

    attitude = pd.read_csv(ATTITUDE_FILE, usecols=["timestamp", "trim_deg", "heel_deg"]) ## 读高度文件
    attitude["timestamp_utc"] = pd.to_datetime(attitude.pop("timestamp"), utc=True)
    start, end = pd.Timestamp(START_TIME_UTC), pd.Timestamp(END_TIME_UTC)
    attitude = attitude[attitude["timestamp_utc"].between(start, end)].copy()

    ship = pd.DataFrame({"timestamp_utc": attitude["timestamp_utc"]})
    ship["ship_yaw_deg"] = interpolate_heading(heading, ship["timestamp_utc"])
    ship["ship_pitch_deg"] = attitude["trim_deg"].to_numpy(dtype=float)
    ship["ship_roll_deg"] = attitude["heel_deg"].to_numpy(dtype=float)
    return ship.reset_index(drop=True)


def main() -> None:
    ship = build_ship_motion()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUTPUT_DIR / "step01_ship_motion.csv"
    ship.to_csv(path, index=False, encoding="utf-8-sig")
    print(f"船体姿态：{len(ship)} 行，{ship.timestamp_utc.iloc[0]} ~ {ship.timestamp_utc.iloc[-1]}")
    print(f"已写入：{path}")


if __name__ == "__main__":
    main()
