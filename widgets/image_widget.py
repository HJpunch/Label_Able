import sys
from PyQt6 import QtCore, QtGui, QtWidgets
import os.path as osp


class img_widget(QtWidgets.QLabel):
    plate = "CH01_20220601083833_81러6786_01_FR"
    here = osp.dirname(osp.abspath(__file__))
    img_dir = osp.join(here, "plate_number", "2022-06-01")
    image = QtGui.QImage("C:/Users/ohs/Desktop/pycharm/my_labelme/plate_number/2022-06-01/CH01_20220601083833_81러6786_01_FR.jpg")

    def __init__(self, name):
        super().__init__()
        self.setObjectName(name)
        self.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Expanding)
        self.setScaledContents(True)
        self.setPixmap(QtGui.QPixmap())
        self.plate_pixmap = QtGui.QPixmap(img_widget.image)
        self.setPixmap(
            self.plate_pixmap.scaled(self.width(), self.height(), QtCore.Qt.AspectRatioMode.KeepAspectRatio,
                          QtCore.Qt.TransformationMode.SmoothTransformation)
            # pixmap
        )

        self.coordinate = list()
        self.past_x = None
        self.coordinate.append(self.past_x)
        self.past_y = None
        self.coordinate.append(self.past_y)
        self.present_x = None
        self.coordinate.append(self.present_x)
        self.present_y = None
        self.coordinate.append(self.present_y)

        # self.draw_rect_onimg(self.plate_pixmap, self.coordinate)

    def set_img(self, pixmap):
        self.setPixmap(pixmap)

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            self.setCursor(QtCore.Qt.CursorShape.CrossCursor)
            self.draw_rect_onimg(event.pos().x(), event.pos().y())

    def mouseRelaseEvent(self, event):
        self.setCursor(QtCore.Qt.CursorShape.ArrowCursor)
        self.draw_rect_onimg(event.pos().x(), event.pos().y())
        self.past_x = None
        self.past_y = None

    # def paintEvent(self, e):
    #     self.canvas = QtGui.QPixmap(self.pixmap())
    #     painter = QtGui.QPainter(self.canvas)
    #     self.draw_rect(painter)
    #     # self.setPixmap(self.canvas)
    #     painter.end()

    def draw_rect_onimg(self, x, y):
        if self.past_x is None:
            self.past_x = x
            self.past_y = y

        else:
            self.present_x = x
            self.present_y = y

            img = self.plate_pixmap.scaled(self.width(), self.height())
            canvas = QtGui.QPainter(img)
            pen = QtGui.QPen()
            pen.setWidth(3)
            pen.setColor(QtGui.QColor("green"))
            canvas.setPen(pen)
            canvas.drawRect(self.past_x, self.past_y, self.present_x, self.present_y)
            canvas.end()
            self.setPixmap(img)


app = QtWidgets.QApplication(sys.argv)
widget = img_widget("test")
widget.show()
app.exec()
