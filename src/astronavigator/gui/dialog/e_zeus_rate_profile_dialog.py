from __future__ import annotations

from uuid import uuid4

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QDialogButtonBox, QDoubleSpinBox, QFormLayout, QHeaderView, QLabel, QLineEdit, QMessageBox, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget

from astronavigator.mount.e_zeus.e_zeus2_protocol import EZeus2_Direction, EZeus2_Speed
from astronavigator.mount.mount import Axis
from astronavigator.tracking.e_zeus_rate_profile import EZeusRateOption,EZeusRateProfile


RATE_ROWS = (
    (Axis.RA, EZeus2_Speed.SIDEREAL, EZeus2_Direction.FORWARD),
    (Axis.RA, EZeus2_Speed.SLOW, EZeus2_Direction.FORWARD),
    (Axis.RA, EZeus2_Speed.SLOW, EZeus2_Direction.REVERSE),
    (Axis.RA, EZeus2_Speed.MEDIUM, EZeus2_Direction.FORWARD),
    (Axis.RA, EZeus2_Speed.MEDIUM, EZeus2_Direction.REVERSE),
    (Axis.RA, EZeus2_Speed.FAST, EZeus2_Direction.FORWARD),
    (Axis.RA, EZeus2_Speed.FAST, EZeus2_Direction.REVERSE),
    (Axis.DEC, EZeus2_Speed.SLOW, EZeus2_Direction.FORWARD),
    (Axis.DEC, EZeus2_Speed.SLOW, EZeus2_Direction.REVERSE),
    (Axis.DEC, EZeus2_Speed.MEDIUM, EZeus2_Direction.FORWARD),
    (Axis.DEC, EZeus2_Speed.MEDIUM, EZeus2_Direction.REVERSE),
    (Axis.DEC, EZeus2_Speed.FAST, EZeus2_Direction.FORWARD),
    (Axis.DEC, EZeus2_Speed.FAST, EZeus2_Direction.REVERSE),
)


SIDEREAL_DAY_SECONDS = 86164.0905
SIDEREAL_RATE_DEG_PER_SEC = (
    360.0 / SIDEREAL_DAY_SECONDS
)


# 暫定値
DEFAULT_RATE_VALUES = {
    (
        Axis.RA,
        EZeus2_Speed.SIDEREAL,
        EZeus2_Direction.FORWARD,
    ): -SIDEREAL_RATE_DEG_PER_SEC,

    (
        Axis.RA,
        EZeus2_Speed.MEDIUM,
        EZeus2_Direction.FORWARD,
    ): -0.086418186,

    (
        Axis.RA,
        EZeus2_Speed.MEDIUM,
        EZeus2_Direction.REVERSE,
    ): 0.086418186,

    (
        Axis.RA,
        EZeus2_Speed.FAST,
        EZeus2_Direction.FORWARD,
    ): -0.321745469,

    (
        Axis.RA,
        EZeus2_Speed.FAST,
        EZeus2_Direction.REVERSE,
    ): 0.197527282,

    (
        Axis.DEC,
        EZeus2_Speed.FAST,
        EZeus2_Direction.FORWARD,
    ): 0.216770834,

    (
        Axis.DEC,
        EZeus2_Speed.FAST,
        EZeus2_Direction.REVERSE,
    ): -0.257688621,
}


class EZeusRateProfileDialog(QDialog):
    def __init__(self, profile: EZeusRateProfile | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.setWindowTitle("E-ZEUS II レートプロファイル")
        self.resize(650, 500)

        self._original_profile = profile
        self._profile: EZeusRateProfile | None = None
        self._rate_inputs: list[QDoubleSpinBox] = []

        self._name = QLineEdit()

        if profile is not None:
            self._name.setText(profile.name)
        else:
            self._name.setText("E-ZEUS II 暫定値")

        form = QFormLayout()
        form.addRow("プロファイル名", self._name)

        explanation = QLabel(
            "速度には、実測した架台軸座標上の符号付き速度を度/秒で入力してください。\n"
            "使用しない指令はチェックを外してください。"
        )
        explanation.setWordWrap(True)

        self._table = QTableWidget(len(RATE_ROWS), 5)
        self._table.setHorizontalHeaderLabels(
            [
                "使用",
                "軸",
                "速度帯",
                "指令",
                "実測速度（°/s）",
            ]
        )
        self._table.verticalHeader().setVisible(False)
        self._table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )

        existing_options = {}
        if profile is not None:
            existing_options = {
                (option.axis, option.speed, option.drive_direction, ): 
                option for option in profile.options
            }

        for row, key in enumerate(RATE_ROWS):
            axis, speed, direction = key
            option = existing_options.get(key)

            default_rate = DEFAULT_RATE_VALUES.get(key) if profile is None else None

            has_initial_value = option is not None or default_rate is not None

            enabled_item = QTableWidgetItem()
            enabled_item.setFlags(
                Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsUserCheckable
            )
            enabled_item.setCheckState(
                Qt.CheckState.Checked if has_initial_value else Qt.CheckState.Unchecked
            )
            self._table.setItem(row, 0, enabled_item)

            self._set_read_only_item(row, 1, axis.value)
            self._set_read_only_item(row, 2, speed.name)
            self._set_read_only_item(row, 3, direction.name)

            rate_input = QDoubleSpinBox()
            rate_input.setDecimals(9)
            rate_input.setRange(-360.0, 360.0)
            rate_input.setSingleStep(0.000001)

            if option is not None:
                rate_input.setValue(option.axis_rate_deg_per_sec)
            elif default_rate is not None:
                rate_input.setValue(default_rate)
            else:
                rate_input.setValue(0.0)

            if default_rate is not None:
                rate_input.setToolTip("2026-08-19の実機試験結果から計算した暫定値です。")

            self._table.setCellWidget(row, 4, rate_input)
            self._rate_inputs.append(rate_input)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._accept_profile)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(explanation)
        layout.addWidget(self._table)
        layout.addWidget(buttons)

    @property
    def profile(self) -> EZeusRateProfile:
        if self._profile is None:
            raise RuntimeError("Profile has not been accepted.")
        return self._profile

    def _set_read_only_item(self, row: int, column: int, text: str) -> None:
        item = QTableWidgetItem(text)
        item.setFlags(Qt.ItemFlag.ItemIsEnabled)
        self._table.setItem(row, column, item)

    def _accept_profile(self) -> None:
        name = self._name.text().strip()
        if not name:
            QMessageBox.warning(
                self, "入力エラー", "プロファイル名を入力してください。",
            )
            return

        options: list[EZeusRateOption] = []

        for row, key in enumerate(RATE_ROWS):
            enabled_item = self._table.item(row, 0)
            if (
                enabled_item.checkState()
                is not Qt.CheckState.Checked
            ):
                continue

            rate = self._rate_inputs[row].value()
            if rate == 0.0:
                QMessageBox.warning(
                    self,
                    "入力エラー",
                    f"{key[0].value} {key[1].name} {key[2].name} の速度が0です。",
                )
                return

            options.append(
                EZeusRateOption(
                    axis=key[0],
                    speed=key[1],
                    drive_direction=key[2],
                    axis_rate_deg_per_sec=rate,
                )
            )

        try:
            profile_id = self._original_profile.profile_id if self._original_profile is not None else str(uuid4())

            self._profile = EZeusRateProfile(
                profile_id=profile_id,
                name=name,
                options=tuple(options),
            )
        except (TypeError, ValueError) as error:
            QMessageBox.warning(
                self,
                "入力エラー",
                str(error),
            )
            return

        self.accept()