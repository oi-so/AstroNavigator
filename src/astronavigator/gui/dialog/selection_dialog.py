from __future__ import annotations

from PySide6.QtWidgets import QDialog, QDialogButtonBox, QLabel, QListWidget, QListWidgetItem, QVBoxLayout
from PySide6.QtCore import Qt

from astronavigator.mount.mount import MountDevice


class MountSelectionDialog(QDialog):
    def __init__(self, devices: list[MountDevice], parent=None):
        super().__init__(parent)

        self.devices = devices
        self.selected_device: MountDevice | None = None

        self.setWindowTitle("マウント接続")
        self.resize(400, 300)

        self._init_ui()


    def _init_ui(self):
        layout = QVBoxLayout(self)

        label = QLabel("接続するマウントを選択してください。")
        layout.addWidget(label)

        self.list_widget = QListWidget(self)
        for device in self.devices:
            display_text = f"{device.name} ({device.identifier})"
            if device.description:
                display_text += f" - {device.description}"

            item = QListWidgetItem(display_text)

            item.setData(Qt.ItemDataRole.UserRole, device)
            self.list_widget.addItem(item)

        self.list_widget.itemDoubleClicked.connect(self._on_item_double_clicked)
        layout.addWidget(self.list_widget)

        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        ok_button = self.button_box.button(QDialogButtonBox.StandardButton.Ok)
        if ok_button:
            # OKボタンのテキストを変える
            ok_button.setText("接続")

        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

        if self.devices:
            self.list_widget.setCurrentRow(0)
        else:
            if ok_button:
                ok_button.setEnabled(False)


    def _on_item_double_clicked(self, item: QListWidgetItem):
        self.selected_device = item.data(Qt.ItemDataRole.UserRole)
        self.accept()


    def accept(self):
        current_item = self.list_widget.currentItem()
        if current_item:
            self.selected_device = current_item.data(Qt.ItemDataRole.UserRole)
            super().accept()
        else:
            return