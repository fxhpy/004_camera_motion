# 004_camera_motion

根据船舶真航向、纵倾、横倾、吃水记录和相机外参，计算船体姿态、各相机的 Yaw/Pitch/Roll，以及参考相机高出实际水面的高度。可进一步把架高插值到参考视频的每一帧。

项目从本地文件读取数据，不调用网络接口。默认处理 `2025-10-17 09:00:01` 至 `12:00:00 UTC`，时间范围、数据位置和相机安装位置在 `config.py` 中配置。

## 文件结构

```text
004_camera_motion/
  config.py                         # 路径、时间范围、船舶与相机参数
  rotation_utils.py                 # Rodrigues / ZYX 欧拉角转换
  run_all.py                        # 依次执行全部五个步骤
  step01_build_ship_motion.py
  step02_parse_camera_extrinsics.py
  step03_build_camera_motion.py
  step04_build_camera_height.py
  step05_build_frame_height.py
  test_motion.py                    # 离线单元测试
  requirements.txt
  data/
    camera_params/                  # 仓库保留的小型标定文本
    heading.xlsx                    # 自行准备，不上传
    02_attitude.csv                  # 自行准备，不上传
  output/                           # 程序生成，不上传
```

原始 Excel/CSV、视频、生成结果、Python 缓存和编辑器配置由 `.gitignore` 排除。整理仓库时这些文件仍保留在本机，GitHub 上的代码需要配套自己的输入数据才能执行完整流程。本机解压目录可继续使用 `04_camera_motion-main`，不影响代码按项目目录定位文件。

## 环境准备

使用 Python 3.9 或更高版本。源码依赖 NumPy、pandas、openpyxl 和 OpenCV；`openpyxl` 用于读取 `.xlsx`，OpenCV 用于读取视频帧率与帧数。

在项目目录打开 PowerShell：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## 输入与配置

修改 `config.py` 后再运行。路径默认相对于项目目录，视频目录是单独配置的绝对路径。

| 配置 | 默认值 / 用途 |
| --- | --- |
| `HEADING_FILE` | `data/heading.xlsx`，读取首个工作表 |
| `ATTITUDE_FILE` | `data/02_attitude.csv` |
| `CAMERA_PARAM_DIR` | `data/camera_params/` |
| `OUTPUT_DIR` | `output/` |
| `VIDEO_DIR` | `D:\Desktop\视频`，需要改成实际位置 |
| `START_TIME_UTC`、`END_TIME_UTC` | 起止时间，包含两个端点 |
| `REFERENCE_CAMERA_ID` | `Front0`，架高输出中的参考相机标识 |
| `REFERENCE_VIDEO_GLOB` | `前视_中_*.mp4`，参考视频文件名匹配规则 |

### 航向 Excel

默认需要以下表头，修改表头时同时修改 `HEADING_COLUMNS`：

| 列名 | 内容 |
| --- | --- |
| `timestamp` | 可解析的时间戳，代码按 UTC 处理 |
| `航向（真北）(°)` | 真航向，单位为度 |

代码将航向转换为数值，去掉空值、按时间排序并去掉重复时间戳。航向使用正弦、余弦分量插值到姿态记录的时刻，以处理 0°/360° 边界。

### 姿态与吃水 CSV

| 列名 | 内容 |
| --- | --- |
| `timestamp` | 可解析的时间戳，代码按 UTC 处理 |
| `trim_deg` | 纵倾角，度；按代码约定船艏上抬为正 |
| `heel_deg` | 横倾角，度；按代码约定右舷下沉为正 |
| `d_fore` | 艏吃水，米 |
| `d_aft` | 艉吃水，米 |
| `d_mean` | 平均吃水，米 |

步骤 1 只读取时间、纵倾和横倾；步骤 4 还需要三列吃水数据，并检查筛选结果非空、数值列无空值。请保证记录按时间递增、时间覆盖所需视频时段。步骤 1 和步骤 4 保留输入记录的采样时刻，**不会把任意采样率重采样为 1 Hz**；输出文件名中的 `1hz` 依赖输入本身为 1 Hz。

### 相机外参

步骤 2 扫描 `ExtrinsicParams*.txt`。每个文件的**第一行**必须是逗号分隔的 6 个数：

```text
rvec_x, rvec_y, rvec_z, tvec_x, tvec_y, tvec_z
```

前三个数按 OpenCV Rodrigues 旋转向量解释，用于计算安装旋转；后三个平移量只写入输出表，当前不参与姿态或架高计算。文件其他行不解析。`IntrinsicParamsFront0.txt` 随项目保留，但这五个步骤没有读取内参。

默认 `EXPECTED_CAMERA_COUNT = 6`，当前目录实际有 7 份外参；数量不一致时只打印提示，仍全部处理。

### 参考视频

步骤 5 从 `VIDEO_DIR` 中查找符合 `REFERENCE_VIDEO_GLOB` 的视频。文件名中必须包含 `_YYYYMMDDhhmmss_YYYYMMDDhhmmss_` 格式的起止时间，例如：

```text
前视_中_20251017090000_20251017091000_001.mp4
```

文件名时间按 UTC 解释。帧时间使用“文件名中的开始时间 + 从 0 开始的帧号 / 视频 FPS”生成；文件名结束时间用于筛选视频和核对时长。分段视频边界的重叠帧会保留，以 `video_file` 和 `frame_index` 区分。

## 执行顺序

准备好全部输入与视频后，可以运行全部 **五个** 步骤：

```powershell
.\.venv\Scripts\python.exe run_all.py
```

也可以按依赖执行单独步骤。只需要相机姿态、不需要架高时运行前三步；需要架高但暂时没有视频时运行到第四步。

```powershell
.\.venv\Scripts\python.exe step01_build_ship_motion.py
.\.venv\Scripts\python.exe step02_parse_camera_extrinsics.py
.\.venv\Scripts\python.exe step03_build_camera_motion.py
.\.venv\Scripts\python.exe step04_build_camera_height.py
.\.venv\Scripts\python.exe step05_build_frame_height.py
```

步骤 3 依赖步骤 1、2 的 CSV；步骤 5 依赖步骤 4 的 CSV 和参考视频。重复执行会覆盖对应输出文件。

## 计算约定

姿态转换采用 ZYX 欧拉角，矩阵组合为：

```text
R_navigation_from_camera = R_navigation_from_ship @ R_ship_from_camera
R_navigation_from_ship  = Rz(yaw) @ Ry(pitch) @ Rx(roll)
```

代码中的船体轴为前、右、下，导航轴为北、东、下；相机 OpenCV 轴为右、下、前。外参转换**假设**标定坐标轴为右、前、上，再转换到相机和船体的前、右、下表示。Yaw 输出位于 `[0, 360)`，Pitch/Roll 单位为度。

默认架高参数为设计吃水 `11.70 m`、相机相对船舯纵向位置 `x = -85.385 m`、横向位置 `y = 0 m`、高出设计水线 `z = 27.25 m`。步骤 4 按以下公式计算（角度先转换为弧度）：

```text
H = (DESIGN_DRAFT_M - d_mean)
    + x * sin(pitch)
    - y * cos(pitch) * sin(roll)
    + z * cos(pitch) * cos(roll)
```

这是采用配置安装位置和吃水、纵倾、横倾的计算结果。默认位置与标定轴向是假设，使用其他船舶或标定资料时需要核对；程序不会自动估计这些参数。当前只计算一组以 Front0 标识的参考架高，没有根据每台相机的外参平移分别计算光心高度，也没有叠加独立的波面变化或升沉观测。

## 输出

CSV 均写入 `OUTPUT_DIR`，编码为 UTF-8 BOM（`utf-8-sig`）。

| 步骤 | 文件 | 主要内容 |
| --- | --- | --- |
| 1 | `step01_ship_motion.csv` | `timestamp_utc`、`ship_yaw_deg`、`ship_pitch_deg`、`ship_roll_deg` |
| 2 | `step02_camera_mounts.csv` | 相机标识、安装欧拉角、外参原值、旋转矩阵 `r00` 至 `r22`、配置安装位置 |
| 3 | `step03_camera_motion_all.csv` | 全部相机的船体姿态及 `camera_yaw_deg`、`camera_pitch_deg`、`camera_roll_deg` |
| 3 | `camera_<camera_id>_motion.csv` | 按相机拆分的姿态表 |
| 4 | `step04_camera_height_1hz.csv` | 吃水、姿态、吃水修正、竖直分量、`camera_height_above_water_m` |
| 5 | `step05_front0_frame_height.csv` | 视频名、帧号、FPS、UTC 帧时间，以及逐帧插值的平均吃水、纵倾、横倾和架高 |

步骤 5 使用线性插值，超出输入数据时间范围时 `numpy.interp` 会使用端点值，并不会报错，因此应先确认输入覆盖范围。文件名不合规则、视频无法读取或缺少必要输入时，流程会中止；当前没有完整的空数据与时间覆盖检查。

## 离线测试

```powershell
.\.venv\Scripts\python.exe -B -m unittest -v test_motion.py
```

现有 3 个测试覆盖欧拉角往返转换、Front0 安装旋转示例、设计吃水且船体水平时的架高。测试使用合成数据，不读取原始 Excel/CSV、不处理视频，也不写入 `output/`。这些测试通过不代表真实记录、标定和视频的完整处理流程已经验证。
