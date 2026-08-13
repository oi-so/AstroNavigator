from __future__ import annotations

from PySide6.QtWidgets import QButtonGroup, QDialog, QDialogButtonBox, QGroupBox, QLabel, QRadioButton, QVBoxLayout, QWidget

from astronavigator.mount.slew_path import PierSide



class MountSyncDialog(QDialog):
    def __init__(self, target_name: str, ra_text: str, dec_text: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.setWindowTitle("マウント同期")
        self.setMinimumWidth(420)

        self._east_button = QRadioButton("東向き")
        self._west_button = QRadioButton("西向き")

        self._side_group = QButtonGroup(self)
        self._side_group.addButton(self._east_button)
        self._side_group.addButton(self._west_button)

        layout = QVBoxLayout(self)

        target_label = QLabel(
            f"{target_name} にマウント位置を同期します。\n"
            f"赤経: {ra_text}\n"
            f"赤緯: {dec_text}"
        )
        layout.addWidget(target_label)

        explanation = QLabel("現在の架台姿勢を選択してください。")
        explanation.setWordWrap(True)
        layout.addWidget(explanation)

        side_box = QGroupBox("現在の架台姿勢")
        side_layout = QVBoxLayout(side_box)
        side_layout.addWidget(self._east_button)
        side_layout.addWidget(self._west_button)
        layout.addWidget(side_box)

        self._button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)

        self._ok_button = self._button_box.button(QDialogButtonBox.StandardButton.Ok)
        self._ok_button.setText("同期")
        self._ok_button.setEnabled(False)

        self._east_button.toggled.connect(self._update_ok_button)
        self._west_button.toggled.connect(self._update_ok_button)

        self._button_box.accepted.connect(self.accept)
        self._button_box.rejected.connect(self.reject)

        layout.addWidget(self._button_box)


    @property
    def selected_pier_side(self) -> PierSide | None:
        if self._east_button.isChecked():
            return PierSide.EAST
        elif self._west_button.isChecked():
            return PierSide.WEST
        else:
            return None

    def _update_ok_button(self) -> None:
        self._ok_button.setEnabled(self.selected_pier_side is not None)