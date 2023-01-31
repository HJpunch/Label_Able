from PyQt6 import QtWidgets, QtGui, QtCore

def img_open(self):
    filename, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Open Image File",
                                                        ".", "Images(*.png *.xpm *.jpg")
    if filename != "":
        self.load(filename)


def img_load(self, filename):
    image = QtGui.QImage(filename)
    self.label.setPixmap(QtGui.QPixmap.fromImage(image))
    self.label.pixmap().scaled(QtCore.QSize(200, 200),
                               aspectRatioMode=QtCore.Qt.AspectRatioMode.KeepAspectRatio)