"""依次运行三个步骤。"""

from step01_build_ship_motion import main as step01
from step02_parse_camera_extrinsics import main as step02
from step03_build_camera_motion import main as step03
from step04_build_camera_height import main as step04
from step05_build_frame_height import main as step05


def main() -> None:
    step01()
    step02()
    step03()
    step04()
    step05()


if __name__ == "__main__":
    main()
