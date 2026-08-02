from __future__ import annotations

from PySide6.QtWidgets import QFrame, QLabel, QPushButton, QWidget, QVBoxLayout, QHBoxLayout

from astronavigator.application.application import Application



class SelectionPanel(QWidget):
    def __init__(self, application: Application):
        super().__init__()

        self._application = application

        self._name_value = QLabel("-")
        self._type_value = QLabel("-")
        self._ra_value = QLabel("-")
        self._dec_value = QLabel("-")
        self._magnitude_value = QLabel("-")


        self._goto_button = QPushButton("導入")
        self._sync_button = QPushButton("同期")
        self._center_button = QPushButton("中央")


        layout = QVBoxLayout(self)

        self._add_field(layout, "名前", self._name_value)
        self._add_field(layout, "種類", self._type_value)
        self._add_field(layout, "RA", self._ra_value)
        self._add_field(layout, "Dec", self._dec_value)
        self._add_field(layout, "等級", self._magnitude_value)

        layout.addStretch()

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(line)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self._goto_button)
        button_layout.addWidget(self._sync_button)
        button_layout.addWidget(self._center_button)

        layout.addLayout(button_layout)


    def _add_field(self, layout: QVBoxLayout, label_text: str, value_label: QLabel) -> None:
        layout.addWidget(QLabel(label_text))
        layout.addWidget(value_label)