import cv2
import os
from PyQt6 import QtWidgets, QtCore, QtGui

here = os.path.dirname(os.path.abspath(__file__))


def iconPath(icon):
    icons_dir = os.path.join(here, "icons")
    return os.path.join(":/", icons_dir, f"{icon}.png")


class VideoSelectDialog(QtWidgets.QDialog):
    loadImgSignal = QtCore.pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select File and Directory")
        self.file = None
        self.dir = None
        self.layout = QtWidgets.QGridLayout()
        QBtn = QtWidgets.QDialogButtonBox.StandardButton.Ok | QtWidgets.QDialogButtonBox.StandardButton.Cancel
        self.buttonbox = QtWidgets.QDialogButtonBox(QBtn)

        # self.loadLayout = QtWidgets.QHBoxLayout()
        # self.loadLayout.addWidget(QtWidgets.QLabel("Video : "))
        self.fileEdit = QtWidgets.QLineEdit()
        self.fileEdit.setPlaceholderText("Enter file name")

        self.fileSelect = QtWidgets.QPushButton()
        pixmap = QtGui.QPixmap(iconPath("folder-search-result"))
        icon = QtGui.QIcon(pixmap)
        self.fileSelect.setIcon(icon)
        self.fileSelect.setIconSize(pixmap.rect().size())

        self.layout.addWidget(QtWidgets.QLabel("Video : "), 0, 0)
        self.layout.addWidget(self.fileEdit, 0, 1)
        self.layout.addWidget(self.fileSelect, 0, 2)

        # self.saveLayout = QtWidgets.QHBoxLayout()
        self.layout.addWidget(QtWidgets.QLabel("Save at : "), 1, 0)
        self.dirEdit = QtWidgets.QLineEdit()
        self.dirEdit.setPlaceholderText("Enter directory to save")

        self.dirSelect = QtWidgets.QPushButton()
        icon = QtGui.QIcon(pixmap)
        self.dirSelect.setIcon(icon)
        self.dirSelect.setIconSize(pixmap.rect().size())

        self.layout.addWidget(self.dirEdit, 1, 1)
        self.layout.addWidget(self.dirSelect, 1, 2)

        self.fileSelect.clicked.connect(self.loadVideo)
        self.dirSelect.clicked.connect(self.loadDir)

        self.layout.addWidget(self.buttonbox)
        self.setLayout(self.layout)

        self.buttonbox.accepted.connect(self.dialogOpen)
        self.buttonbox.rejected.connect(self.reject)

    def loadVideo(self, checked):
        filename, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Open Video File", ".",
                                                            "Video File(*.avi *.mp4 *.wmv *.mov *.mkv *.3gp)")

        if filename != "":
            self.fileEdit.setText(filename)

    def loadDir(self, checked):
        dirname = QtWidgets.QFileDialog.getExistingDirectory(self, "Folder to Save", ".",
                                                             QtWidgets.QFileDialog.Option.ShowDirsOnly)
        self.dirEdit.setText(dirname)

    def dialogOpen(self):
        if len(self.fileEdit.text()) == 0 or len(self.dirEdit.text()) == 0:
            return
        self.file = self.fileEdit.text()
        self.dir = self.dirEdit.text()
        dialog = VideoParseDialog(self.file, self.dir, self)
        dialog.open()
        dialog.btnClicked.connect(self.afterParse)

    def afterParse(self):
        print("btnclick catch")
        self.loadImgSignal.emit(self.dir)

    def reject(self):
        self.fileEdit.clear()
        self.dirEdit.clear()
        super().reject()


class VideoParseDialog(QtWidgets.QDialog):
    btnClicked = QtCore.pyqtSignal()

    def __init__(self, file, directory, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Loading...")
        self.layout = QtWidgets.QVBoxLayout()
        self.file = file
        self.dir = directory

        self.video = cv2.VideoCapture(self.file)
        self.length = int(self.video.get(cv2.CAP_PROP_FRAME_COUNT))
        self.width = int(self.video.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.video.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.fps = self.video.get(cv2.CAP_PROP_FPS)

        # self.btn = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Ok)
        self.start = QtWidgets.QPushButton("Start parsing")
        self.start.clicked.connect(self.videoParsing)
        self.cancel = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Close)
        self.cancel.rejected.connect(self.reject)
        self.load = QtWidgets.QPushButton("Load Images")
        self.load.setEnabled(False)
        self.load.clicked.connect(self.btnClickedEvent)

        self.buttonbox = QtWidgets.QHBoxLayout()
        self.buttonbox.addWidget(self.start)
        self.buttonbox.addWidget(self.load)
        self.buttonbox.addWidget(self.cancel)

        self.progress = QtWidgets.QProgressBar()
        self.maximum = int(self.length/self.fps) - 1  # num of parsed images
        self.progress.setRange(0, self.maximum)
        self.progress.setValue(0)
        self.progress.valueChanged.connect(self.loading)

        self.layout.addWidget(QtWidgets.QLabel(f"File : {file}"))
        self.layout.addWidget(QtWidgets.QLabel(f"Save at : {directory}"))
        self.layout.addWidget(self.progress)
        self.layout.addLayout(self.buttonbox)
        self.setLayout(self.layout)

    def loading(self, value):
        if value == self.maximum:
            self.load.setEnabled(True)

    def btnClickedEvent(self):
        self.btnClicked.emit()  # assert video cropped successfully. Trigger to load parsed video images on file list.
        self.close()
        self.parent().close()

    def videoParsing(self):
        if not self.video.isOpened():
            return

        count = 0
        while (self.video.isOpened()):
            ret, image = self.video.read()
            # print(ret)
            # print(image)
            if not ret:
                break
            if (int(self.video.get(1)) % self.fps == 0):  # 앞서 불러온 fps 값을 사용하여 1초마다 추출
                cv2.imwrite(self.dir + "\\frame%d.jpg" % count, image)
                # print('Saved frame number :', str(int(self.video.get(1))))
                count += 1
                self.progress.setValue(count)

        self.video.release()


def video_parsing_second(file_name, dir):

    video = cv2.VideoCapture(file_name)

    if not video.isOpened():
        print("Could not Open :", file_name)
        exit(0)
    length = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(video.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = video.get(cv2.CAP_PROP_FPS)

    print("length :", length)
    print("width :", width)
    print("height :", height)
    print("fps :", fps)

    try:
        if not os.path.exists(dir):
            os.makedirs(dir)
    except OSError:
        print('Error: Creating directory. ' + file_name[:-4])
    # try:
    #     if not os.path.exists(r'C:\Users\ohs\Desktop\pycharm\my_labelme\privacy_video_annotation/3'):
    #         os.makedirs(r'C:\Users\ohs\Desktop\pycharm\my_labelme\privacy_video_annotation/3')
    # except OSError:
    #     print('Error: Creating directory. ' + file_name[:-4])

    count = 0

    while (video.isOpened()):

        ret, image = video.read()
        # print(ret)
        # print(image)
        if not ret:
            break
        if (int(video.get(1)) % fps == 0):  # 앞서 불러온 fps 값을 사용하여 1초마다 추출
            # print(file_name[:-4])
            # cv2.imshow('1', image)
            # cv2.waitKey(0)
            # cv2.imwrite(r'C:\Users\ohs\Desktop\pycharm\my_labelme\privacy_video_annotation/3' + "\\frame%d.jpg" % count, image)
            cv2.imwrite(dir + "\\frame%d.jpg" % count, image)
            print('Saved frame number :', str(int(video.get(1))))
            count += 1

    video.release()


# if __name__ == '__main__':
#     video_parsing_second(r'C:\Users\ohs\Desktop\pycharm\my_labelme\privacy_video_annotation/연세대학교 원주캠퍼스 영문학과 김아름 1.wmv')