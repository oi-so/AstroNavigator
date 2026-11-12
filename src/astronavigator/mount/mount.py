from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from enum import Enum
from abc import ABC, abstractmethod
from dataclasses import dataclass
from serial.tools import list_ports


from astronavigator.mount.slew_path import PierSide
from astronavigator.sky.position import Position


@dataclass(slots=True)
class MountDevice:
    driver: type[Mount]
    name: str
    identifier: str
    description: str | None = None



class ConnectionState(Enum):
    DISCONNECTED = "Disconnected"
    CONNECTING = "Connecting"
    CONNECTED = "Connected"
    ERROR = "Error"

class Axis(Enum):
    RA = "RA"
    DEC = "DEC"


class Mount(ABC):
    @property
    @abstractmethod
    def state(self) -> ConnectionState:
        ...

    @abstractmethod
    def update_status(self) -> None:
        ...

    @property
    @abstractmethod
    def position(self) -> Position:
        ...

    @property
    @abstractmethod
    def driver_name(self) -> str | None:
        ...

    @property
    @abstractmethod
    def is_tracking(self) -> bool:
        ...

    @property
    def is_connected(self) -> bool:
        return self.state == ConnectionState.CONNECTED

    @property
    @abstractmethod
    def is_slewing(self) -> bool:
        ...

    @property
    def pier_side(self) -> PierSide:
        ...

    @property
    def can_set_pier_side(self) -> bool:
        return False

    @property
    def supports_goto_pier_side(self) -> bool:
        """導入(slew_to)時に架台姿勢(pier_side)を明示指定できるか。

        ``can_set_pier_side``（ASCOM CanSetPierSide＝SideOfPierを強制的に
        書き換えられるか）とは異なる概念であることに注意。GoTo先の座標に
        対してどちらの鏡筒姿勢を使うかを、GoToコマンド自体に含めて
        指定できるプロトコル/実装でのみ True を返す。
        """
        return False

    @property
    def requires_pier_side_for_sync(self) -> bool:
        return False

    @property
    def is_synced(self) -> bool:
        return True

    @property
    def can_home(self) -> bool:
        return False

    def home(self) -> None:
        """架台をホームポジションへ移動する。

        アライメント開始前に架台を既知の基準位置へ戻すための操作。
        SynScanのように機構的なホームポジションを持つ架台のみが対応し、
        E-ZEUS IIのようにsync基準方式の架台では対応しない
        （``can_home`` が False のままとなる）。
        """
        if not self.can_home:
            raise NotImplementedError("This mount does not support finding home.")
        raise NotImplementedError("home() is not implemented for this mount.")


    @abstractmethod
    def set_tracking(self, tracking: bool) -> None:
        ...


    @abstractmethod
    def connect(self) -> None:
        ...


    @abstractmethod
    def disconnect(self) -> None:
        ...


    @abstractmethod
    def move_axis(self, axis: Axis, speed: float) -> None:
        ...

    @abstractmethod
    def stop_axis(self, axis: Axis) -> None:
        ...


    @abstractmethod
    def slew_to(self, position: Position, *, pier_side: PierSide | None = None) -> None:
        ...


    @abstractmethod
    def stop(self) -> None:
        ...


    @abstractmethod
    def sync(self, position: Position, *, pier_side: PierSide | None = None) -> None:
        ...

    def flip_meridian(self) -> None:
        if not self.can_set_pier_side:
            raise NotImplementedError("This mount does not support setting pier side.")
        current_position = self.position
        current_side = self.pier_side

        if current_side == PierSide.EAST:
            new_side = PierSide.WEST
        elif current_side == PierSide.WEST:
            new_side = PierSide.EAST
        else:
            raise RuntimeError("Current pier side is unknown, cannot flip.")

        self.slew_to(current_position, pier_side=new_side)


    @classmethod
    @abstractmethod
    def discover(cls) -> list[MountDevice]:
        ...


    @classmethod
    @abstractmethod
    def create(cls, identifier: str) -> Mount:
        ...


    @staticmethod
    def find_ports() -> list[str]:
        ports = list_ports.comports()
        return [port.device for port in ports]



    @classmethod
    def discover_all(cls) -> list[MountDevice]:
        """登録済みの全Mountサブクラスに対してdiscover()を並列に実行する。

        各ドライバのdiscover()はポート走査やネットワークprobeを伴い、
        それぞれ数秒かかることがある。直列実行だと合計時間が線形に
        伸びるため、サブクラスごとに別スレッドで実行し、最も遅い
        ドライバのdiscover時間だけで全体が完了するようにする。
        """
        subclasses = cls.__subclasses__()
        if not subclasses:
            return []

        all_devices: list[MountDevice] = []

        with ThreadPoolExecutor(max_workers=len(subclasses)) as executor:
            future_to_subclass = {
                executor.submit(subclass.discover): subclass
                for subclass in subclasses
            }

            for future in as_completed(future_to_subclass):
                subclass = future_to_subclass[future]
                try:
                    devices = future.result()
                    all_devices.extend(devices)
                except Exception as e:
                    print(f"Error discovering devices for {subclass.__name__}: {e}")

        return all_devices