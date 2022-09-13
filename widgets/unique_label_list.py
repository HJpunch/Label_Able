from PyQt6 import QtGui, QtCore, QtWidgets

class UniqLabelListWidgetItem(QtGui.QStandardItem):
    def __init__(self, text=None, color=None):
        super().__init__()
        self.setText(text or "")
        self.setColor(color)
        self.setEditable(False)

    def clone(self):
        return UniqLabelListWidgetItem(self.text(), self.color())

    def setColor(self, color):
        self.setData(color, QtCore.Qt.ItemDataRole.UserRole)

    def color(self):
        return self.data(QtCore.Qt.ItemDataRole.UserRole)  # return data for the UserRole


class StandardItemModel(QtGui.QStandardItemModel):
    def data(self, index, role):
        if role == QtCore.Qt.ItemDataRole.DecorationRole:
            color = self.itemFromIndex(index).color()
            return color

        if role == QtCore.Qt.ItemDataRole.DisplayRole:
            item = self.itemFromIndex(index)
            return item.text()


class UniqLabelListWidget(QtWidgets.QListView):
    editToExist = 0
    existColor = None
    editToNew = 0
    itemClicked = QtCore.pyqtSignal(UniqLabelListWidgetItem)

    def __init__(self):
        super().__init__()

        self.setWindowFlags(QtCore.Qt.WindowType.Window)
        self.setModel(StandardItemModel())
        self.model().setItemPrototype(UniqLabelListWidgetItem())

        self.clicked.connect(self.itemClickedEvent)

    def itemClickedEvent(self, index):
        self.itemClicked.emit(self.model().itemFromIndex(index))

    def addItem(self, item):
        self.editToExist = 0
        self.editToNew = 0
        # if not self.model().item(0):
        #     self.model().setItem(self.model().rowCount(), 0, item)
        #     return

        if item.text() in [label.text() for label in self.allItemList()]:
            return

        else:
            self.model().setItem(self.model().rowCount(), 0, item)

    def editItem(self, item):
        self.editToExist = 0
        self.editToNew = 0
        if item.text() in [label.text() for label in self.allItemList()]:
            self.editToExist = 1
            self.existColor = [uniq.color() for uniq in self.allItemList() if item.text() == uniq.text()][0]

        else:
            self.editToNew = 1

    def allItemList(self):
        itemList = list()
        for index in range(self.model().rowCount()):
            item = self.model().item(index)
            itemList.append(item)
        return itemList

    def clear(self):
        self.model().clear()