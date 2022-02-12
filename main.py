import sys
from PyQt5.QtCore import Qt
from PyQt5 import uic
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtGui import QPixmap
from Y_search_module import Map


class QMapShower(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('map_ui.ui', self)
        self.mode_combo.addItems(['Гибрид', 'Схема', 'Спутник'])
        self.mode_dict = {'Схема': 'skl', 'Спутник': 'sat', 'Гибрид': 'map'}
        self.map_ = Map(coords=[0, 0], size = [1, 1])
        self.set_map()
        self.show_but.clicked.connect(self.set_map)

    def set_map(self):
        self.map_.remove_self()
        self.map_ = Map(coords=[self.lon_spin.value(), self.lat_spin.value()],
                        size = [self.size_spin.value(),
                                self.size_spin.value()],
                        mode=self.mode_dict[self.mode_combo.currentText()])
        self.map_lab.setPixmap(QPixmap(self.map_.get_map()))

    def closeEvent(self, event):
        self.map_.remove_self()

    def keyPressEvent(self, event):
        size_delta = lon_delta = lat_delta = 0
        if event.key() == Qt.Key_PageUp:
            size_delta = (self.size_spin.value() / 10)
        if event.key() == Qt.Key_PageDown:
            size_delta = -(self.size_spin.value() / 10)
        self.size_spin.setValue(self.size_spin.value() + size_delta)
        if event.key() == Qt.Key_Left:
            lon_delta = -(self.size_spin.value())
        if event.key() == Qt.Key_Right:
            lon_delta = (self.size_spin.value())
        self.lon_spin.setValue(self.lon_spin.value() + lon_delta)
        if event.key() == Qt.Key_Up:
            lat_delta = (self.size_spin.value())
        if event.key() == Qt.Key_Down:
            lat_delta = -(self.size_spin.value())
        self.lat_spin.setValue(self.lat_spin.value() + lat_delta)
        if any([lat_delta, lon_delta, size_delta]):
            self.set_map()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    wind = QMapShower()
    wind.show()
    sys.exit(app.exec())
