# http://www2.synapse.ne.jp/haya/zeus/e-zeus2_com.html
# https://web.archive.org/web/20240704072325/http://www2.synapse.ne.jp/haya/zeus/e-zeus2_com.html


from __future__ import annotations

from enum import Enum, StrEnum
import serial
import time


class EZeus2Error(Enum):
    NO_ERROR = 0
    ERROR = 1
    UNKNOWN_COMMAND = 2


class EZeus2_RA_DEC(StrEnum):
    RA = "RA"
    DEC = "DC"

class EZeus2_Direction(StrEnum):
    FORWARD = "F"
    REVERSE = "R"

class EZeus2_Speed(Enum):
    STOP = 0
    SIDEREAL = 1
    SLOW = 2
    MEDIUM = 3
    FAST = 4

# E-ZEUS2にstatusを問い合わせた時のindex
class EZeus2StatusIndex(StrEnum):
    RA_STATUS = "ra_status"
    RA_DIRECTION = "ra_direction"
    RA_SPEED = "ra_speed"
    DEC_STATUS = "dec_status"
    DEC_DIRECTION = "dec_direction"
    DEC_SPEED = "dec_speed"

class EZeus2CommandRejectedError(RuntimeError):
    def __init__(self, command: str, response: str) -> None:
        self.command = command
        self.response = response

        self.warning_code = response[1:3] if response.startswith("!") and len(response) >= 3 else None

        super().__init__(f"E-ZEUS2 rejected command: {command!r}, response: {response!r}, warning_code: {self.warning_code!r}")

class EZeus2Protocol:
    def __init__(self, port: str, baudrate: int = 9600, timeout: float = 0.5):
        self._port = port
        self._baundrate = baudrate
        self._timeout = timeout
        self.serial: serial.Serial | None = None
        self._is_connected = False

    @property
    def is_connected(self) -> bool:
        return self._is_connected

    def connect(self):
        self.serial = serial.Serial(
            port=self._port,
            baudrate=self._baundrate,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=self._timeout,
        )
        self._is_connected = True
        time.sleep(2)


    def disconnect(self) -> None:
        if self.serial is None: 
            raise RuntimeError("Serial port is not open")
        self._is_connected = False
        self.serial.close()


    def _send(self, cmd: str) -> str:
        if self.serial is None:
            raise RuntimeError("Serial port is not open")

        self.serial.reset_input_buffer()
        self.serial.write(cmd.encode("ascii") + b"\r")
        self.serial.flush()
        raw = self.serial.readline()
        # print(f"cmd={cmd!r}, raw={raw!r}")
        return raw.decode("ascii", errors="replace").strip()


    def _check_ack(self, resp: str) -> EZeus2Error:
        if resp.startswith("!"):
            return EZeus2Error.ERROR
        elif resp.startswith("?"):
            return EZeus2Error.UNKNOWN_COMMAND
        else:
            return EZeus2Error.NO_ERROR



    def get_position(self) -> tuple[int, int]:
        """
        RA/DECの現在のステップ位置を16進法8桁で取得
        """

        resp = self._send("GP")

        # GP#HHHHHHHH#hhhhhhhh GPは位置返答、#はモーターの値であることを表す
        ra_hex = resp[3:11]
        dec_hex = resp[12:20]

        return int(ra_hex, 16), int(dec_hex, 16)


    def drive(self, axis: EZeus2_RA_DEC, direction: EZeus2_Direction, speed: EZeus2_Speed, steps: int | None = None) -> str:
        """
        指定した軸を指定した方向に指定した速度で駆動する

        Args:
            axis (EZeus2_RA_DEC): 駆動する軸
            direction (EZeus2_Direction): 駆動方向
            speed (EZeus2_Speed): 0=停止、1=恒星時(RAのみ)、2=低速、3=中速、4=高速
            steps (int | None): 駆動するステップ数。Noneの場合はSPが来るまで連続

        Returns:
            str: レスポンス
        """

        if axis == EZeus2_RA_DEC.DEC and speed == EZeus2_Speed.SIDEREAL:
            raise ValueError("DEC軸は恒星時駆動できません")

        # DVRAF2#HHHHHHHH
        # DVはドライブコマンド
        # RA/DCで赤経or赤緯指定
        # F/Rで正転or逆転指定
        # 0=停止、1=恒星時(RAのみ)、2=低速、3=中速、4=高速
        # #で区切り文字(連続の場合はステップ数なし)
        # HHHHHHHHでステップ数
        if steps is None:
            cmd = f"DV{axis.value}{direction.value}{speed.value}"
        else:
            cmd = f"DV{axis.value}{direction.value}{speed.value}#{steps:08X}"

        resp = self._send(cmd)
        self._raise_for_error(resp, cmd)
        return resp


    def stop(self, to_siderial: bool = False) -> str:
        """
        駆動を停止する

        Args:
            to_siderial (bool): Trueの場合は恒星時駆動に切り替える

        Returns:
            str: レスポンス
        """

        cmd = f"SP{1 if to_siderial else 0}"
        resp = self._send(cmd)
        self._check_ack(resp)
        return resp



    def get_status(self) -> dict:
        resp = self._send("ST")

        """
        返答は以下のようになっている
        01: ST→状態返答
        2: P→赤経がPCで動作、B→赤経がE-ZEUS2で動作、I→赤経がアイドル中(恒星運転の場合も含む)
        3: F→赤経が正転、R→赤経が逆転
        4: 設計モーターのスピード(0=停止、1=恒星時(RAのみ)、2=低速、3=中速、4=高速) (E-ZEUS2で動作中は必ず0)

        5: P→赤緯がPCで動作、B→赤緯がE-ZEUS2で動作、I→赤緯がアイドル中
        6: F→赤緯が正転、R→赤緯が逆転
        7: 設計モーターのスピード(0=停止、2=低速、3=中速、4=高速) (E-ZEUS2で動作中は必ず0)
        """

        return {
            EZeus2StatusIndex.RA_STATUS: resp[2],
            EZeus2StatusIndex.RA_DIRECTION: resp[3],
            EZeus2StatusIndex.RA_SPEED: int(resp[4]),
            EZeus2StatusIndex.DEC_STATUS: resp[5],
            EZeus2StatusIndex.DEC_DIRECTION: resp[6],
            EZeus2StatusIndex.DEC_SPEED: int(resp[7]),
        }


    def get_revolution_step(self) -> tuple[int, int]:
        resp = self._send("RD")
        ra_hex = resp[3:11]
        dec_hex = resp[12:20]
        return int(ra_hex, 16), int(dec_hex, 16)

    def set_revolution_step(self, ra_steps: int, dec_steps: int) -> str:
        # モーター停止中か恒星追尾時のみ
        # 現在位置がクリアされる
        cmd = f"RD#{ra_steps:08X}#{dec_steps:08X}"
        resp = self._send(cmd)
        self._check_ack(resp)
        return resp


    def get_arrival_margin(self) -> tuple[int, int]:
        """高速移動から導入位置より何ステップ前で速度を遅くするか"""
        resp = self._send("PA")
        ra_hex = resp[3:5]
        dec_hex = resp[6:8]
        return int(ra_hex, 16), int(dec_hex, 16)


    def set_arrival_margin(self, ra_steps: int, dec_steps: int) -> str:
        """高速移動から導入位置より何ステップ前で速度を遅くするか"""
        cmd = f"PA#{ra_steps:02X}#{dec_steps:02X}"
        resp = self._send(cmd)
        self._check_ack(resp)
        return resp


    def get_handbox_slowdown(self) -> tuple[int, int]:
        resp = self._send("SL")
        return int(resp[3:5], 16), int(resp[6:8], 16)

    def set_handbox_slowdown(self, ra_steps: int, dec_steps: int) -> str:
        cmd = f"SL#{ra_steps:02X}#{dec_steps:02X}"
        resp = self._send(cmd)
        self._check_ack(resp)
        return resp

    def get_backlash(self) -> tuple[bool, int, int]:
        """ギアの遊びを想定するらしい"""
        resp = self._send("BL")
        active = resp[2] == "A"
        ra_backlash = resp[4:12]
        dec_backlash = resp[13:21]
        return active, int(ra_backlash, 16), int(dec_backlash, 16)


    def set_backlash(self, ra_backlash: int, dec_backlash: int) -> str:
        """外部から操作されたり動作中は拒否される。赤緯は普通0"""
        cmd = f"BL#{ra_backlash:08X}#{dec_backlash:08X}"
        resp = self._send(cmd)
        self._check_ack(resp)
        return resp


    def get_version(self) -> str:
        resp = self._send("VR")
        return resp


    def quick_check(self) -> str | None:
        try:
            with serial.Serial(self._port, self._baundrate, timeout=1) as ser:
                time.sleep(0.2)

                ser.reset_input_buffer()
                ser.write(b"VR\r")

                resp = ser.readline().decode(
                    "ascii",
                    errors="replace",
                ).strip()

                if resp.startswith("E-ZEUS2"):
                    return resp

                return None
        except Exception:
            return None


    def _raise_for_error(self, resp: str, cmd: str) -> None:
        error = self._check_ack(resp)

        if error == EZeus2Error.ERROR:
            raise EZeus2CommandRejectedError(cmd, resp)

        if error == EZeus2Error.UNKNOWN_COMMAND:
            raise RuntimeError(
                f"E-ZEUS2 does not recognize command: {cmd!r}, response: {resp!r}"
            )