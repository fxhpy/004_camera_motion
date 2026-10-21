"""第5步 将1 Hz相机架高线性插值到 Front0 对应视频的每一帧。"""

import re
from pathlib import Path

import cv2
import numpy as np
import pandas as pd

from config import (
    END_TIME_UTC,
    OUTPUT_DIR,
    REFERENCE_CAMERA_ID,
    REFERENCE_VIDEO_GLOB,
    START_TIME_UTC,
    VIDEO_DIR,
)


TIME_PATTERN = re.compile(r"_(\d{14})_(\d{14})_")


def parse_video_times(path: Path) -> tuple[pd.Timestamp, pd.Timestamp]:
    match = TIME_PATTERN.search(path.name)
    if not match:
        raise ValueError(f"视频名中没有起止时间：{path.name}")
    start = pd.to_datetime(match.group(1), format="%Y%m%d%H%M%S", utc=True)
    end = pd.to_datetime(match.group(2), format="%Y%m%d%H%M%S", utc=True)
    return start, end


def read_video_timeline(path: Path) -> pd.DataFrame:
    video_start, video_end = parse_video_times(path)
    capture = cv2.VideoCapture(str(path))
    fps = float(capture.get(cv2.CAP_PROP_FPS))
    frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
    capture.release()
    if fps <= 0 or frame_count <= 0:
        raise ValueError(f"无法读取视频帧率/帧数：{path.name}")

    measured_duration = frame_count / fps
    named_duration = (video_end - video_start).total_seconds()
    if abs(measured_duration - named_duration) >= 0.5:
        print(
            f"注意：{path.name} 文件名时长{named_duration:.3f}s"
            f"按帧数计算{measured_duration:.3f}s"
        )

    frame_index = np.arange(frame_count, dtype=np.int64)
    timestamp_ns = video_start.value + np.rint(frame_index / fps * 1e9).astype(np.int64)
    return pd.DataFrame(
        {
            "timestamp_utc": pd.to_datetime(timestamp_ns, utc=True),
            "video_file": path.name,
            "frame_index": frame_index,
            "fps": fps,
        }
    )


def interpolate_to_frames(height_1hz: pd.DataFrame, frames: pd.DataFrame) -> pd.DataFrame:
    source_time = height_1hz["timestamp_utc"].astype("int64").to_numpy()
    target_time = frames["timestamp_utc"].astype("int64").to_numpy()
    result = frames.copy()
    result.insert(1, "camera_id_reference", REFERENCE_CAMERA_ID)
    for column in [
        "d_mean_m",
        "ship_pitch_deg",
        "ship_roll_deg",
        "camera_height_above_water_m",
    ]:
        result[column] = np.interp(
            target_time,
            source_time,
            height_1hz[column].to_numpy(dtype=float),
        )
    return result


def build_frame_height() -> pd.DataFrame:
    videos = sorted(VIDEO_DIR.glob(REFERENCE_VIDEO_GLOB))
    if not videos:
        raise FileNotFoundError(
            f"没有找到 Front0 参考视频：{VIDEO_DIR / REFERENCE_VIDEO_GLOB}"
        )

    start, end = pd.Timestamp(START_TIME_UTC), pd.Timestamp(END_TIME_UTC)
    timelines = []
    for path in videos:
        video_start, video_end = parse_video_times(path)
        if video_end >= start and video_start <= end:
            timelines.append(read_video_timeline(path))
    frames = pd.concat(timelines, ignore_index=True)
    frames = frames[frames["timestamp_utc"].between(start, end)]
    # 以 (视频文件, 帧号) 为唯一标识，保留分段边界处的重叠帧。
    frames = frames.sort_values(
        ["timestamp_utc", "video_file", "frame_index"]
    ).reset_index(drop=True)

    height = pd.read_csv(
        OUTPUT_DIR / "step04_camera_height_1hz.csv",
        parse_dates=["timestamp_utc"],
    )
    return interpolate_to_frames(height, frames)


def main() -> None:
    frame_height = build_frame_height()
    path = OUTPUT_DIR / "step05_front0_frame_height.csv"
    frame_height.to_csv(path, index=False, encoding="utf-8-sig")
    print(
        f"Front0逐帧架高：{len(frame_height)}帧，"
        f"{frame_height.timestamp_utc.iloc[0]} ~ {frame_height.timestamp_utc.iloc[-1]}"
    )
    
    unique_time = frame_height["timestamp_utc"].drop_duplicates().sort_values()
    gaps = unique_time.diff().dt.total_seconds()
    duplicate_count = int(frame_height.duplicated("timestamp_utc").sum())
    gap_count = int((gaps > 0.051).sum())
    print(f"分段边界检查：{duplicate_count}帧时间重叠，{gap_count}处时间缺口")
    print(f"已写入：{path}")


if __name__ == "__main__":
    main()
