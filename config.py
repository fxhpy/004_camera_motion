from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
CAMERA_PARAM_DIR = DATA_DIR / "camera_params"
OUTPUT_DIR = ROOT / "output"
VIDEO_DIR = Path(r"D:\Desktop\视频")

HEADING_FILE = DATA_DIR / "heading.xlsx"
ATTITUDE_FILE = DATA_DIR / "02_attitude.csv"

START_TIME_UTC = "2025-10-17T09:00:01Z"
END_TIME_UTC = "2025-10-17T12:00:00Z"

# 船舶主尺度，仅作为项目元数据保留。
LOA_M = 209.95
LPP_M = 206.55
BEAM_M = 34.80
DEPTH_M = 18.00
DESIGN_DRAFT_M = 11.70

# 相机组位于船艘罗经甲板；x向船艏为正，因此船舶纵向坐标取负。
CAMERA_X_FROM_MIDSHIP_M = -85.385
CAMERA_Y_FROM_CENTERLINE_M = 0.0
CAMERA_HEIGHT_ABOVE_DESIGN_WATERLINE_M = 27.25

REFERENCE_CAMERA_ID = "Front0"
REFERENCE_VIDEO_GLOB = "前视_中_*.mp4"

EXPECTED_CAMERA_COUNT = 6

HEADING_COLUMNS = {
    "timestamp": "timestamp_utc",
    "航向（真北）(°)": "yaw_deg",
}
