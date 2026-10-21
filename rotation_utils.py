"""旋转矩阵工具；统一采用 ZYX 欧拉角和“前-右-下”坐标系。"""

import numpy as np


def rodrigues_to_matrix(rvec: np.ndarray) -> np.ndarray:
    """将 OpenCV 旋转向量转换成 3*3 旋转矩阵。"""
    theta = float(np.linalg.norm(rvec)) ## 向量的模长
    if theta < 1e-12:
        return np.eye(3) ## 3*3 单位矩阵
    x, y, z = rvec / theta
    k = np.array([[0, -z, y], [z, 0, -x], [-y, x, 0]], dtype=float)
    return np.eye(3) + np.sin(theta) * k + (1 - np.cos(theta)) * (k @ k)


def euler_zyx_to_matrix(yaw_deg: float, pitch_deg: float, roll_deg: float) -> np.ndarray:
    """Yaw-Pitch-Roll 转旋转矩阵 Rz(yaw)  Ry(pitch)  Rx(roll)。"""
    yaw, pitch, roll = np.radians([yaw_deg, pitch_deg, roll_deg])
    cy, sy = np.cos(yaw), np.sin(yaw)
    cp, sp = np.cos(pitch), np.sin(pitch)
    cr, sr = np.cos(roll), np.sin(roll)
    rz = np.array([[cy, -sy, 0], [sy, cy, 0], [0, 0, 1]])
    ry = np.array([[cp, 0, sp], [0, 1, 0], [-sp, 0, cp]])
    rx = np.array([[1, 0, 0], [0, cr, -sr], [0, sr, cr]])
    return rz @ ry @ rx


def matrix_to_euler_zyx(matrix: np.ndarray) -> tuple[float, float, float]:
    """旋转矩阵转 Yaw-Pitch-RollYaw 输出到 [0, 360)。"""
    yaw = np.degrees(np.arctan2(matrix[1, 0], matrix[0, 0])) % 360
    pitch = np.degrees(np.arcsin(np.clip(-matrix[2, 0], -1, 1)))
    roll = np.degrees(np.arctan2(matrix[2, 1], matrix[2, 2]))
    return float(yaw), float(pitch), float(roll)


def extrinsic_to_body_camera_rotation(rvec: np.ndarray) -> np.ndarray:
    """把 OpenCV 外参旋转转换为“相机前-右-下 → 船体前-右-下”。"""
    calib_to_cv_camera = rodrigues_to_matrix(rvec)
    cv_camera_to_calib = calib_to_cv_camera.T

    # 标定系假设：x=右、y=前、z=上；船体系：x=前、y=右、z=下。
    calib_to_body = np.array([[0, 1, 0], [1, 0, 0], [0, 0, -1]], dtype=float)

    # OpenCV 相机轴：x=右、y=下、z=前；重排成相机“前-右-下”。
    camera_frd_in_calib = np.column_stack(
        (cv_camera_to_calib[:, 2], cv_camera_to_calib[:, 0], cv_camera_to_calib[:, 1])
    )
    return calib_to_body @ camera_frd_in_calib
