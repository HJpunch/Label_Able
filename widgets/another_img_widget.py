import sys
from PyQt6 import QtCore, QtGui, QtWidgets
import os.path as osp


class img_widget(QtWidgets.QWidget):

    def __init__(self, name):
        super().__init__()
        self.setObjectName(name)
        self.setWindowTitle(name)

        formbox = QtWidgets.QHBoxLayout()
        # self.img_label = QtWidgets.QLabel()
        # self.img_label.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Expanding)
        # self.img_label.setScaledContents(True)
        # self.img_label.setPixmap(QtGui.QPixmap())
        # self.plate_pixmap = QtGui.QPixmap(img_widget.image)
        # self.img_label.setPixmap(
        #     self.plate_pixmap.scaled(self.width(), self.height(), QtCore.Qt.AspectRatioMode.KeepAspectRatio,
        #                              QtCore.Qt.TransformationMode.SmoothTransformation)
        #     # pixmap
        # )
        self.draw_mode = 0
        self.btn = QtWidgets.QCheckBox("start draw")
        self.btn.setCheckState(QtCore.Qt.CheckState.Unchecked)
        self.btn.stateChanged.connect(self.set_draw)

        self.view = view(self)
        formbox.addWidget(self.btn)
        formbox.addWidget(self.view)

        self.setLayout(formbox)

    def set_draw(self, s):
        if QtCore.Qt.CheckState(s) == QtCore.Qt.CheckState.Checked:
            self.draw_mode = 1
        else:
            self.draw_mode = 0

class view(QtWidgets.QGraphicsView):
    plate = "CH01_20220601083833_81러6786_01_FR"
    here = osp.dirname(osp.abspath(__file__))
    img_dir = osp.join(here, "plate_number", "2022-06-01")
    image = QtGui.QImage("C:/Users/ohs/Desktop/pycharm/my_labelme/plate_number/2022-06-01/CH01_20220601083833_81러6786_01_FR.jpg")

    def __init__(self, parent):
        super().__init__(parent)
        self.scene = QtWidgets.QGraphicsScene()
        self.setScene(self.scene)
        self.setMinimumSize(500, 500)
        self.plate_num = QtGui.QPixmap(view.image)
        self.plate_num = self.plate_num.scaled(self.rect().width(), self.rect().height(), QtCore.Qt.AspectRatioMode.KeepAspectRatio,
                                               QtCore.Qt.TransformationMode.SmoothTransformation)

        self.scene.addPixmap(self.plate_num)

        self.pen = QtGui.QPen()
        self.pen.setWidth(1)
        self.pen.setColor(QtGui.QColor("green"))

        self.items = list()

        self.start = QtCore.QPointF()
        self.end = QtCore.QPointF()

    def moveEvent(self, e):
        rect = QtCore.QRectF(self.rect())
        self.scene.setSceneRect(rect)

    def mousePressEvent(self, e):
        self.start = QtCore.QPointF(e.pos())
        self.end = QtCore.QPointF(e.pos())

    def mouseMoveEvent(self, e):
        if e.buttons() == QtCore.Qt.MouseButton.LeftButton:
            self.end = QtCore.QPointF(e.pos())

            if self.parent().draw_mode == 1:
                brush = QtGui.QBrush(QtGui.QColor(0, 0, 0, 0))

                rect = QtCore.QRectF(self.start, self.end)
                # self.items.append(self.scene.addRect(rect, self.pen, brush))

    def mouseReleaseEvent(self, e):
        if e.button() == QtCore.Qt.MouseButton.LeftButton:
            if self.parent().draw_mode == 1:
                brush = QtGui.QBrush(QtGui.QColor(0, 0, 0, 0))
                rect = QtCore.QRectF(self.start, self.end)
                self.scene.addRect(rect, self.pen, brush)
                print(self.scene.items())


app = QtWidgets.QApplication(sys.argv)
window = img_widget("test")
window.show()
app.exec()
