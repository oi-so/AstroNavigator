from __future__ import annotations

from zoneinfo import ZoneInfo

from PySide6.QtCore import QDateTime
from PySide6.QtWidgets import QComboBox, QDateTimeEdit, QDialog, QDialogButtonBox, QFormLayout


class TimeEditDialog(QDialog):
    def __init__(self, datetime_value, timezone_value: ZoneInfo, parent=None):
        super().__init__(parent)

        self.setWindowTitle("時刻設定")

        self._datetime_edit = QDateTimeEdit(
            QDateTime.fromSecsSinceEpoch(
                int(datetime_value.timestamp())
            )
        )

        self._datetime_edit.setCalendarPopup(True)
        self._datetime_edit.setDisplayFormat("yyyy-MM-dd HH:mm:ss")

        self._timezone_combo = QComboBox()

        timezones = [
            "UTC",
            "Asia/Tokyo",
            "America/New_York",
            "Europe/London",
            "Europe/Paris",
            "Australia/Sydney",
        ]
        self._timezone_combo.addItems(timezones)

        current_timezone = str(timezone_value)
        index = self._timezone_combo.findText(current_timezone)

        if index >= 0:
            self._timezone_combo.setCurrentIndex(index)

        layout = QFormLayout(self)

        layout.addRow("日付:", self._datetime_edit)
        layout.addRow("タイムゾーン:", self._timezone_combo)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)

        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout.addWidget(buttons)


    @property
    def datetime(self):
        value = self._datetime_edit.dateTime().toPython()
        timezone = self.timezone
        return value.replace(tzinfo=timezone)

    @property
    def timezone(self) -> ZoneInfo:
        return ZoneInfo(self._timezone_combo.currentText())