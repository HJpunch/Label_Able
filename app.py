import os.path as osp
import sys
import json
import numpy as np
import functools
import natsort

from PyQt6 import QtCore
from PyQt6 import QtWidgets
from PyQt6 import QtGui

import io
import PIL.Image
import PIL.ImageOps
import PIL.ExifTags
from video_crop import VideoSelectDialog, VideoParseDialog

from Shape import Shape
from canvas import Canvas
from widgets.zoom_widget import ZoomWidget
from widgets.label_dialog import LabelDialog
from widgets.label_list_widget import LabelListWidgetItem, LabelListWidget
from widgets.unique_label_list import UniqLabelListWidgetItem, UniqLabelListWidget


here = osp.dirname(osp.abspath(__file__))

mode_to_bpp = {'1': 1, 'L': 8, 'P': 8, 'RGB': 24, 'RGBA': 32, 'CMYK': 32, 'YCbCr': 24, 'I': 32, 'F': 32}


def newIcon(icon):
    icons_dir = osp.join(here, "icons")
    return QtGui.QIcon(osp.join(":/", icons_dir, f"{icon}.png"))


class MainWindow(QtWidgets.QMainWindow):

    FIT_WINDOW, FIT_WIDTH, MANUAL_ZOOM = 0, 1, 2

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Label-Able")

        self.zoomMode = self.FIT_WINDOW
        self.scalers = {
            self.FIT_WINDOW: self.scaleFitWindow,
            self.FIT_WIDTH: self.scaleFitWidth,
            self.MANUAL_ZOOM: lambda: 1,
        }

        self.filename = None
        self.lastOpenDir = None
        self.outputDir = None
        self.OUTPUT = 0
        self.SEARCH = 0
        self.DRAW_UNIQUE = 0
        self.UNIQUE_LABEL_DATA = dict()

        self._noSelectionSignal = False  # prevent label change signal recursion

        self.setStatusBar(QtWidgets.QStatusBar())

        menu = self.menuBar()
        layout = QtWidgets.QHBoxLayout()
        self.zoomWidget = ZoomWidget()
        self.setAcceptDrops(True)
        zoom = QtWidgets.QWidgetAction(self)
        zoom.setDefaultWidget(self.zoomWidget)
        self.zoomWidget.setEnabled(False)
        self.zoomWidget.valueChanged.connect(self.paintCanvas)

        self.canvas = Canvas()
        scrollArea = QtWidgets.QScrollArea()
        scrollArea.setWidget(self.canvas)
        scrollArea.setWidgetResizable(True)
        self.scrollBars = {
            QtCore.Qt.Orientation.Vertical: scrollArea.verticalScrollBar(),
            QtCore.Qt.Orientation.Horizontal: scrollArea.horizontalScrollBar()
        }
        self.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.canvasContextMenu)

        self.zoom_values = {}  # key = filename, value = (zoom_mode, zoom_value)
        self.scroll_values = {
            QtCore.Qt.Orientation.Horizontal: {},
            QtCore.Qt.Orientation.Vertical: {}  # key=filename, value=scroll_value
        }

        self.setCentralWidget(scrollArea)

        self.image = QtGui.QImage()
        self.imageData = None
        self.imageDepth = None
        self.color = list()
        self.recent_file = list()
        self.defaultSavePath = None

        # create menu-file
        file_menu = menu.addMenu("&File")

        file_open = self.action("Open", icon="open", shortcut="Ctrl+O", tip="Open Image or Label File")
        file_open.triggered.connect(self.img_open)
        file_menu.addAction(file_open)
        next_img = self.action("Next Image", icon="next", shortcut="D", tip="Open next")
        next_img.triggered.connect(self.loadNextImage)
        file_menu.addAction(next_img)
        prev_img = self.action("Prev Image", icon="prev", shortcut="A", tip="Open prev")
        prev_img.triggered.connect(self.loadPrevImage)
        file_menu.addAction(prev_img)
        open_dir = self.action("Open Dir", icon="open", shortcut="CTRL+U", tip="Open Dir")
        open_dir.triggered.connect(self.dir_open)
        file_menu.addAction(open_dir)
        load_video = self.action("Load Video", icon="open", tip="Load Video, Parse per second")
        load_video.triggered.connect(self.video_open)
        file_menu.addAction(load_video)
        self.open_recent = file_menu.addMenu("Open Recent")
        label_save = self.action("Save", icon="save", shortcut="Ctrl+S", tip="Save Labels to File")
        label_save.triggered.connect(self.saveFile)
        file_menu.addAction(label_save)
        self.label_autoSave = self.action("Auto Save", icon="save", tip="Save Automatically in Output Dir")
        file_menu.addAction(self.label_autoSave)
        self.label_autoSave.setCheckable(True)
        change_out_dir = self.action("Change Output Dir", icon="open", tip="Change Where Annotations saved/loaded")
        change_out_dir.triggered.connect(self.dir_output)
        file_menu.addAction(change_out_dir)
        file_menu.addSeparator()
        app_quit = self.action("Quit", icon="quit", shortcut="Ctrl+q", tip="Quit Application")
        file_menu.addAction(app_quit)
        app_quit.triggered.connect(QtCore.QCoreApplication.instance().quit)

        # create menu-edit
        edit_menu = menu.addMenu("&Edit")

        self.draw_box = self.action("Create Box", icon="objects", shortcut="Ctrl+R", tip="Start Drawing Rectangles")
        edit_menu.addAction(self.draw_box)
        self.draw_box.setEnabled(False)
        self.draw_box.triggered.connect(self.setCreateMode)
        self.edit_box = self.action("Edit Box", icon="edit", shortcut="Ctrl+J", tip="Move and Edit the selected Box")
        edit_menu.addAction(self.edit_box)
        self.edit_box.setEnabled(False)
        # self.edit_box.setCheckable(True)
        self.edit_box.triggered.connect(self.setEditMode)
        self.edit_label = self.action("Edit Label", icon="edit", shortcut="Ctrl+E", tip="Modify the label of the selected Box")
        edit_menu.addAction(self.edit_label)
        self.edit_label.triggered.connect(self.editLabel)
        self.delete_box = self.action("Delete Box", icon="cancel", shortcut="Del", tip="Delete the selected Box")
        edit_menu.addAction(self.delete_box)
        self.delete_box.triggered.connect(self.deleteSelectedShape)
        # clear = self.action("Clear", icon="edit", shortcut="Ctrl+O", tip="Clear image and box")
        # clear.triggered.connect(self.canvas.resetState)
        # edit_menu.addAction(clear)

        # create menu-view
        view_menu = menu.addMenu("&View")

        # view_menu.addSeparator()
        # hide_box = self.action("Hide Box")
        # hide_box.setCheckable(True)
        # hide_box.setChecked(False)
        # view_menu.addAction(hide_box)

        # create Docket widget

        # add "Label List"
        self.label_list = QtWidgets.QDockWidget("Label List")
        # self.label_list.setWidget(QtWidgets.QListWidget())
        self.label_list.setWidget(UniqLabelListWidget())
        self.label_list.widget().itemClicked.connect(self.drawUniqMode)
        view_menu.addAction(self.label_list.toggleViewAction())

        # add "Polygon Labels"
        self.polygon_label = QtWidgets.QDockWidget("Polygon Labels")

        self.polygon_list = LabelListWidget()
        self.polygon_list.itemSelectionChanged.connect(self.labelSelectionChanged)
        self.polygon_list.itemDoubleClicked.connect(self.editLabel)
        self.polygon_list.itemChanged.connect(self.labelItemChanged)
        self.polygon_list.itemDropped.connect(self.labelOrderChanged)

        self.polygon_label.setWidget(self.polygon_list)
        view_menu.addAction(self.polygon_label.toggleViewAction())

        # add "File List"
        file_list = QtWidgets.QDockWidget("File List")
        file_container = QtWidgets.QWidget()
        fileListLayout = QtWidgets.QVBoxLayout()

        self.fileListWidget = QtWidgets.QListWidget()
        self.fileListWidget.itemSelectionChanged.connect(self.loadItemSelection)
        self.filesearch = QtWidgets.QLineEdit()
        self.filesearch.setPlaceholderText("Search Filename")
        self.filesearch.textChanged.connect(self.searchFile)

        fileListLayout.addWidget(self.filesearch)
        fileListLayout.addWidget(self.fileListWidget)
        file_container.setLayout(fileListLayout)
        file_list.setWidget(file_container)
        view_menu.addAction(file_list.toggleViewAction())

        self.addDockWidget(QtCore.Qt.DockWidgetArea.RightDockWidgetArea, self.label_list)
        self.addDockWidget(QtCore.Qt.DockWidgetArea.RightDockWidgetArea, self.polygon_label)
        self.addDockWidget(QtCore.Qt.DockWidgetArea.RightDockWidgetArea, file_list)

        # create toolbar
        toolbar = QtWidgets.QToolBar("Tool Bar")
        toolbar.setToolButtonStyle(QtCore.Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        self.addToolBar(toolbar)
        toolbar.addAction(file_open)
        toolbar.addAction(open_dir)
        toolbar.addAction(load_video)
        toolbar.addAction(prev_img)
        toolbar.addAction(next_img)
        toolbar.addAction(label_save)

        toolbar.addSeparator()
        toolbar.addAction(self.draw_box)
        toolbar.addAction(self.edit_box)
        toolbar.addAction(self.delete_box)
        # toolbar.addAction(clear)

        widget = QtWidgets.QWidget()
        widget.setLayout(layout)
        # self.setCentralWidget(widget)

        self.canvas.newShape.connect(self.newShape)
        self.canvas.selectionChanged.connect(self.shapeSelectionChanged)

        self.videoDialog = VideoSelectDialog()
        self.videoDialog.loadImgSignal.connect(self.scanAllImages)

    def canvasContextMenu(self, pos):
        context = QtWidgets.QMenu()
        context.addAction(self.draw_box)
        context.addAction(self.edit_box)
        context.addAction(self.edit_label)
        context.addAction(self.delete_box)
        context.exec(self.mapToGlobal(pos))

    def labelSelectionChanged(self, selection, deselection):
        if self._noSelectionSignal:
            return

        if self.canvas.editing():
            selected_shapes = list()
            for item in self.polygon_list.selectedItems():
                selected_shapes.append(item.shape())
            if selected_shapes:
                self.canvas.selectShapes(selected_shapes)
            else:
                self.canvas.deSelectShape()

    def editLabel(self, item=None):
        if not self.canvas.editing():
            return

        if not item:
            try:
                item = self.polygon_list.selectedItems()[0]

            except IndexError:
                return

        editDlg = LabelDialog(self, self.label_list.widget())
        shape = item.shape()
        editDlg.setName.setText(shape.label)
        if editDlg.exec():
            text = editDlg.setName.text()
            shape.label = text
            item.setText(shape.label)

        else:
            return

    def labelItemChanged(self, item):
        if self.canvas.editing():
            self.label_list.widget().editItem(item)
            if self.label_list.widget().editToExist:
                color = self.label_list.widget().existColor
                self.copyShapeColor(item.shape(), color)

            if self.label_list.widget().editToNew:
                self.setNewColor(item.shape())
                label = UniqLabelListWidgetItem(item.text(), item.shape().line_color)
                self.label_list.widget().addItem(label)

        else:
            label = UniqLabelListWidgetItem(item.text(), item.shape().line_color)
            self.label_list.widget().addItem(label)

    def copyShapeColor(self, shape, color):
        r = color.red()
        g = color.green()
        b = color.blue()
        self.setNewColor(shape, r, g, b)

    def labelOrderChanged(self):
        return

    def newShape(self):
        if self.DRAW_UNIQUE:
            text = self.UNIQUE_LABEL_DATA['label']
            shape = self.canvas.setLastLabel(text, None)
            polygon = LabelListWidgetItem(text, shape)
            color = self.UNIQUE_LABEL_DATA['color']
            self.copyShapeColor(shape, color)
            self.polygon_list.addItem(polygon)
            self.DRAW_UNIQUE = 0
            self.label_list.widget().selectionModel().clearSelection()
            return
        labelDlg = LabelDialog(self, self.label_list.widget())
        if labelDlg.exec():
            text = labelDlg.setName.text()
            shape = self.canvas.setLastLabel(text, None)  # none flag
            polygon = LabelListWidgetItem(text, shape)
            if len(self.canvas.shapes) > 0:
                # for item in self.polygon_list.allItemList():
                for item in self.label_list.widget().allItemList():
                    if polygon.text() == item.text():
                        self.copyShapeColor(shape, item.color())
                        break
                    else:
                        self.setNewColor(shape)
            self.polygon_list.addItem(polygon)

        else:
            self.canvas.shapes.pop()

    def drawUniqMode(self, item):
        if self.canvas.editing():
            return
        self.DRAW_UNIQUE = 1
        color = item.color()
        label = item.text()
        self.UNIQUE_LABEL_DATA['color'] = color
        self.UNIQUE_LABEL_DATA['label'] = label

    def deleteSelectedShape(self):
        shapes = self.canvas.deleteSelected()
        for shape in shapes:
            item = self.polygon_list.itemFromShape(shape)
            self.polygon_list.removeItem(item)

    def shapeSelectionChanged(self, selected_shapes):
        self._noSelectionSignal = True
        self.polygon_list.clearSelection()
        for shape in self.canvas.selectedShapes:
            shape.selected = False
        self.canvas.selectedShapes = selected_shapes

        for shape in self.canvas.selectedShapes:
            shape.selected = True
            item = self.polygon_list.itemFromShape(shape)
            self.polygon_list.selectItem(item)

        self._noSelectionSignal = False

    def recentFileAction(self, file):
        if len(self.recent_file) > 9:
            self.recent_file.pop()
        filename = file[file.rfind('/')+1:]
        if filename not in self.recent_file:
            self.recent_file.insert(0, filename)
            action = QtGui.QAction(self.recent_file[0], self)
            action.triggered.connect(lambda: self.loadFile(file))
            self.open_recent.addAction(action)

    # File list dock widget methods
    def loadItemSelection(self):
        item = self.fileListWidget.selectedItems()
        if not item:
            return
        item = item[0]
        file = self.lastOpenDir + item.text()
        self.loadFile(file)
        # recent_file = QtGui.QAction(item.text(), self)

    def searchFile(self):
        self.SEARCH = 1
        self.scanAllImages(
            folderpath=self.lastOpenDir,
            keyword=self.filesearch.text()
        )

    def scanAllImages(self, folderpath, keyword=None):
        if not folderpath:
            return
        self.lastOpenDir = folderpath
        iterdir = QtCore.QDirIterator(folderpath, QtCore.QDirIterator.IteratorFlag.Subdirectories)
        self.fileListWidget.clear()
        images = list()
        while iterdir.hasNext():
            iterdir.next()
            for i in [".jpg", ".jpeg", ".png"]:
                if i in str(iterdir.filePath()):
                    if keyword:
                        if keyword in str(iterdir.filePath()):
                            # self.fileListWidget.addItem(iterdir.filePath().replace(folderpath, ""))
                            img = iterdir.filePath().replace(folderpath, "")
                            images.append(img)

                    else:
                        img = iterdir.filePath().replace(folderpath, "")
                        images.append(img)
                        # self.fileListWidget.addItem(iterdir.filePath().replace(folderpath, ""))
            if ".json" in str(iterdir.filePath()):
                if keyword:
                    if keyword in str(iterdir.filePath()):
                        data = iterdir.filePath().replace(folderpath, "")
                        images.append(data)

                else:
                    data = iterdir.filePath().replace(folderpath, "")
                    images.append(data)

        images = natsort.os_sorted(images)
        for image in images:
            self.fileListWidget.addItem(image)

        if not self.SEARCH:
            item = self.fileListWidget.item(0)
            item.setSelected(True)
            self.fileListWidget.scrollToItem(item)
            file = self.lastOpenDir + item.text()
            self.loadFile(file)

    def loadNextImage(self):
        if self.label_autoSave.isChecked():
            self.saveFile()
        if not self.fileListWidget.item(0):
            return
        index = self.fileListWidget.selectedIndexes()[0].row()
        index += 1
        item = self.fileListWidget.item(index)
        if item is None:
            return
        item.setSelected(True)
        self.fileListWidget.scrollToItem(item)

    def loadPrevImage(self):
        if self.label_autoSave.isChecked():
            self.saveFile()
        if not self.fileListWidget.item(0):
            return
        index = self.fileListWidget.selectedIndexes()[0].row()
        index -= 1
        item = self.fileListWidget.item(index)
        if item is None:
            return
        item.setSelected(True)
        self.fileListWidget.scrollToItem(item)

    def setCreateMode(self):
        self.canvas.setEditing(False)
        self.draw_box.setEnabled(False)
        self.edit_box.setEnabled(True)

    def setEditMode(self):
        self.canvas.setEditing(True)
        self.edit_box.setEnabled(False)
        self.draw_box.setEnabled(True)

    def action(self, name, icon=None, shortcut=None, tip=None):
        if icon:
            action = QtGui.QAction(newIcon(icon), name, self)
        else:
            action = QtGui.QAction(name, self)
        action.setObjectName(name)
        if shortcut:
            action.setShortcut(shortcut)
        if tip:
            action.setStatusTip(tip)
        return action

    def dir_open(self):
        dir = QtWidgets.QFileDialog.getExistingDirectory(self, "Search Folder", QtCore.QDir.homePath(),
                                                         QtWidgets.QFileDialog.Option.ShowDirsOnly)
        # dir = str(dir)
        self.lastOpenDir = dir
        if not self.OUTPUT:
            self.outputDir = dir
        self.SEARCH = 0
        self.scanAllImages(dir)

    def dir_output(self):
        fDir= QtWidgets.QFileDialog.getExistingDirectory(self, "Search Folder to Save", self.outputDir,
                                                         QtWidgets.QFileDialog.Option.ShowDirsOnly)
        if fDir != "":
            self.outputDir = fDir
            self.OUTPUT = 1
        print(self.OUTPUT)

    def img_open(self):
        filename, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Open Image/Label File",
                                                            ".", "Image&Label(*.png *.xpm *.jpg *.jpeg *.json)")
        if filename != "":
            if "json" in filename:
                self.loadJson(filename)
            else:
                fDir = filename[:filename.rfind('/')]
                self.lastOpenDir = fDir
                if not self.OUTPUT:
                    self.outputDir = fDir
                self.loadFile(filename)

    def video_open(self):
        self.videoDialog.open()

    def img_depth(self, file):
        try:
            data = PIL.Image.open(file)
            bpp = mode_to_bpp[data.mode]
            if bpp != 1:
                bpp /= 8
            return int(bpp)
        except FileNotFoundError:
            return -1

    def loadFile(self, filename=None):
        if ".json" in filename:
            self.loadJson(filename)
            return
        self.draw_box.setEnabled(True)
        self.edit_box.setEnabled(True)
        self.canvas.resetState()
        self.canvas.setEnabled(False)
        self.canvas.resetState()
        self.polygon_list.clear()
        self.color = []
        # self.imageData = self.load_image_file(filename)
        # image = QtGui.QImage.fromData(self.imageData)
        image = QtGui.QImage(filename)
        self.image = image
        self.imageDepth = self.img_depth(filename)
        if self.imageDepth == -1:
            message = QtWidgets.QMessageBox.critical(self, "File Not Found Error", f"No such file or directory: {filename}")
            if message:
                return
        self.filename = filename
        # self.canvas.loadPixmap(QtGui.QPixmap.fromImage(image))
        self.canvas.loadPixmap(QtGui.QPixmap.fromImage(image))
        self.canvas.setEnabled(True)
        self.paintCanvas()
        self.canvas.setFocus()
        self.adjustScale(initial=True)
        self.recentFileAction(filename)

    def saveFile(self):
        if not self.filename:
            return
        file = self.filename
        imgName = file[file.rfind('/')+1:]
        if self.defaultSavePath:
            savePath = self.defaultSavePath
            self.defaultSavePath = None
        else:
            savePath = self.outputDir + "/" + imgName[:imgName.rfind('.')] + ".json"

        if not self.label_autoSave.isChecked():
            save = QtWidgets.QFileDialog.getSaveFileName(self, 'Save label', savePath, "label files (*.json)")
            save = save[0]
        else:
            save = savePath

        # JSON format
        data = dict()

        data['image_filename'] = imgName
        data['image_size'] = {'width': self.image.width(),
                              'height': self.image.height(),
                              'depth': self.imageDepth}
        data['image_path'] = file[:file.rfind('/')+1]

        Object = list()
        for index, item in enumerate(self.polygon_list.allItemList()):
            Object.append({'object_id': index,
                           'object_name': item.text(),
                           'object_coor':
                               {'x1': min(item.shape().points[0].x(), item.shape().points[1].x()),
                                'y1': min(item.shape().points[0].y(), item.shape().points[1].y()),
                                'x2': max(item.shape().points[0].x(), item.shape().points[1].x()),
                                'y2': max(item.shape().points[0].y(), item.shape().points[1].y())}
                           })
        data['Object'] = Object

        if save != "":
            with open(save, "w", encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent="\t")

    def loadJson(self, file):
        try:
            with open(file, "r", encoding="UTF-8") as f:
                data = json.load(f)
        except FileNotFoundError:
            message = QtWidgets.QMessageBox.critical(self, "File Not Found Error",
                                                     f"No such file or directory: {file}")
            if message:
                self.scanAllImages(self.lastOpenDir)
                return

        self.defaultSavePath = file
        filename = data['image_path']+data['image_filename']
        self.loadFile(filename)

        self.outputDir = data['image_path']

        shapeList = list()
        for object in data['Object']:
            label = object['object_name']
            shape = Shape(label=label)
            point1 = QtCore.QPoint(object['object_coor']['x1'], object['object_coor']['y1'])
            point2 = QtCore.QPoint(object['object_coor']['x2'], object['object_coor']['y2'])
            shape.addPoint(point1)
            shape.addPoint(point2)
            shapeList.append(shape)
        self.canvas.loadShapes(shapeList)
        for shape in shapeList:
            item = LabelListWidgetItem(shape.label, shape)
            self.polygon_list.addItem(item)

    def resizeEvent(self, event):
        if self.canvas and not self.image.isNull() and self.zoomMode != self.MANUAL_ZOOM:
            self.adjustScale()
        super(MainWindow, self).resizeEvent(event)

    def paintCanvas(self):  # loadfile, zoom value changed
        assert not self.image.isNull(), "cannot paint null image"
        self.canvas.scale = 0.01 * self.zoomWidget.value()  # zoomWidget.value is percentage
        self.canvas.adjustSize()
        self.canvas.update()

    def adjustScale(self, initial=False):
        value = self.scalers[self.FIT_WINDOW if initial else self.zoomMode]()
        value = int(100*value)  # convert to %
        self.zoomWidget.setValue(value)  # connect paintCanvas
        self.zoom_values[self.filename] = (self.zoomMode, value)

    def scrollRequest(self, delta, orientation):
        units = -delta * 0.1
        bar = self.scrollBars[orientation]
        value = bar.value() + bar.singleStep() * units
        self.setScroll(orientation, value)

    def setScroll(self, orientation, value):
        self.scrollBars[orientation].setValue(value)
        self.scroll_values[orientation][self.filename] = value

    def scaleFitWindow(self):
        e = 2.0  # 여유공간
        w1 = self.centralWidget().width() - e
        h1 = self.centralWidget().height() - e
        a1 = w1/h1
        w2 = self.canvas.pixmap.width() - 0.0
        h2 = self.canvas.pixmap.height() - 0.0
        a2 = w2/h2
        return w1/w2 if a2 >= a1 else h1/h2

    def scaleFitWidth(self):
        w = self.centralWidget().width() - 2.0
        return w / self.canvas.pixmap.width()

    def setNewColor(self, shape, r=None, g=None, b=None):
        if r is None:
            color = list(np.random.choice(range(256), size=3))
            while color in self.color:
                color = list(np.random.choice(range(256), size=3))
            self.color.append(color)
            r, g, b = color
        shape.line_color = QtGui.QColor(r, g, b, 128)
        shape.vertex_fill_color = QtGui.QColor(r, g, b, 255)
        shape.fill_color = QtGui.QColor(r, g, b, 128)
        shape.select_fill_color = QtGui.QColor(r, g, b, 155)

    def setLabelColor(self, label, shape):
        r = label.line_color.red()
        g = label.line_color.green()
        b = label.line_color.blue()
        shape.line_color = QtGui.QColor(r, g, b, 128)
        shape.vertex_fill_color = QtGui.QColor(r, g, b, 255)
        shape.fill_color = QtGui.QColor(r, g, b, 128)
        shape.select_fill_color = QtGui.QColor(r, g, b, 155)

    @staticmethod
    def load_image_file(filename):
        image_pil = PIL.Image.open(filename)

        # apply orientation to image according to exif
        image_pil = MainWindow.apply_exif_orientation(image_pil)

        with io.BytesIO() as f:
            format = "PNG"
            image_pil.save(f, format=format)
            f.seek(0)
            return f.read()

    @staticmethod
    def apply_exif_orientation(image):
        try:
            exif = image._getexif()
        except AttributeError:
            exif = None

        if exif is None:
            print("exif is none")
            return image

        exif = {
            PIL.ExifTags.TAGS[k]: v
            for k, v in exif.items()
            if k in PIL.ExifTags.TAGS
        }
        print(exif)
        orientation = exif.get("Orientation", None)

        if orientation == 1:
            # do nothing
            return image
        elif orientation == 2:
            # left-to-right mirror
            return PIL.ImageOps.mirror(image)
        elif orientation == 3:
            # rotate 180
            return image.transpose(PIL.Image.ROTATE_180)
        elif orientation == 4:
            # top-to-bottom mirror
            return PIL.ImageOps.flip(image)
        elif orientation == 5:
            # top-to-left mirror
            return PIL.ImageOps.mirror(image.transpose(PIL.Image.ROTATE_270))
        elif orientation == 6:
            # rotate 270
            return image.transpose(PIL.Image.ROTATE_270)
        elif orientation == 7:
            # top-to-right mirror
            return PIL.ImageOps.mirror(image.transpose(PIL.Image.ROTATE_90))
        elif orientation == 8:
            # rotate 90
            return image.transpose(PIL.Image.ROTATE_90)
        else:
            return image
    # def img_load(self, filename):
    #     image = QtGui.QImage(filename)
    #     pixmap = QtGui.QPixmap.fromImage(image)
    #     self.canvas.loadPixmap(pixmap)
    # self.label.setPixmap(QtGui.QPixmap.fromImage(image))
    # self.label.setPixmap(pixmap.scaled(self.label.width(), self.label.height(), QtCore.Qt.AspectRatioMode.KeepAspectRatio,
    #                                    QtCore.Qt.TransformationMode.SmoothTransformation))

    # def mousePressEvent(self, event):
    #     if event.button() == QtCore.Qt.MouseButton.LeftButton:
    #         self.past_x = event.x()
    #         self.past_y = event.y()
    #         self.click = 1
    #         self.update()
    #
    #     if event.button() == QtCore.Qt.MouseButton.LeftButton:
    #         self.click = 2
    #         self.update()
    #
    # def mouseRelaseEvent(self, event):
    #     self.present_x = event.x()
    #     self.present_y = event.y()

    # def paintEvent(self, event):
    #     if (self.past_x and self.present_x) is not None:
    #         painter = QtGui.QPainter(self.label.pixmap())
    #         pen = QtGui.QPen()
    #         pen.setWidth(3)
    #         pen.setColor(QtGui.QColor("green"))
    #         painter.setPen(pen)
    #         rect = QtCore.QRect(self.past_x, self.past_y, self.present_x, self.present_y)
    #         painter.drawRect(rect)
    #         # self.label.setPixmap(self.label.pixmap())
    #         painter.end()

    # pen = QtGui.QPen()
    # pen.setWidth(3)
    # pen.setColor(QtGui.QColor("green"))
    # self.canvas = self.label.pixmap()
    # painter = QtGui.QPainter(self.canvas)
    # painter.setPen(pen)
    # rect = QtCore.QRect(self.past_x, self.past_y, self.present_x, self.present_y)
    # painter.drawRect(rect)
    # painter.end()


    # def paintEvent(self, event):
    #     if not self.label.pixmap():
    #         return super(MainWindow, self).paintEvent(event)
    #     self.setMouseTracking(True)
    #     self.canvas = self.label.pixmap()
    #     painter = QtGui.QPainter(self.canvas)
    #     pen = QtGui.QPen()
    #     pen.setWidth(3)
    #     pen.setColor(QtGui.QColor("green"))
    #     painter.setPen(pen)
    #     rect = QtCore.QRect(self.past_x, self.past_y, self.present_x, self.present_y)
    #     painter.drawRect(rect)
    #     painter.end()
    #     self.label.setPixmap(self.canvas)

app = QtWidgets.QApplication(sys.argv)
window = MainWindow()
window.show()
app.exec()
