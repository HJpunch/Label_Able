from PyQt6 import QtGui, QtCore, QtWidgets

class LabelListWidgetItem(QtGui.QStandardItem):
    def __init__(self, text=None, shape=None):
        super(LabelListWidgetItem, self).__init__()
        self.setText(text or "")
        self.setShape(shape)

        self.setCheckable(True)
        self.setCheckState(QtCore.Qt.CheckState.Checked)
        self.setEditable(False)

    def clone(self):
        return LabelListWidgetItem(self.text(), self.shape())

    def setShape(self, shape):
        self.setData(shape, QtCore.Qt.ItemDataRole.UserRole)

    def shape(self):
        return self.data(QtCore.Qt.ItemDataRole.UserRole)  # return data for the UserRole


class StandardItemModel(QtGui.QStandardItemModel):
    itemDropped = QtCore.pyqtSignal()

    def removeRows(self, *args, **kwargs):
        result = super().removeRows(*args, **kwargs)  # bool type
        self.itemDropped.emit()
        return result

    def data(self, index, role):
        if role == QtCore.Qt.ItemDataRole.DecorationRole:
            shape = self.itemFromIndex(index).shape()
            return shape.line_color

        if role == QtCore.Qt.ItemDataRole.DisplayRole:
            shape = self.itemFromIndex(index).shape()
            return shape.label

        # if role == QtCore.Qt.ItemDataRole.CheckStateRole:
        #     state = self.itemFromIndex(index).checkState()
        #     return state


class LabelListWidget(QtWidgets.QListView):
    itemDoubleClicked = QtCore.pyqtSignal(LabelListWidgetItem)
    itemSelectionChanged = QtCore.pyqtSignal(list, list)

    def __init__(self):
        super().__init__()
        self._selectedItems = list()

        self.setWindowFlags(QtCore.Qt.WindowType.Window)
        self.setModel(StandardItemModel())
        self.model().setItemPrototype(LabelListWidgetItem())
        self.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setDragDropMode(QtWidgets.QAbstractItemView.DragDropMode.InternalMove)
        self.setDefaultDropAction(QtCore.Qt.DropAction.MoveAction)
        self.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.DoubleClicked)
        self.selectionModel().selectionChanged.connect(self.itemSelectionChangedEvent)

    @property
    def itemDropped(self):
        return self.model().itemDropped

    @property
    def itemChanged(self):
        return self.model().itemChanged

    def edit(self, *args):
        index = args[0]
        trigger = args[1]
        if trigger == QtWidgets.QAbstractItemView.EditTrigger.DoubleClicked:
            item = self.model().itemFromIndex(index)
            self.itemDoubleClicked.emit(item)
            return True

        else:
            return False

    def itemSelectionChangedEvent(self, selected, deselected):
        selected = [self.model().itemFromIndex(i) for i in selected.indexes()]
        deselected = [self.model().itemFromIndex(i) for i in deselected.indexes()]
        self.itemSelectionChanged.emit(selected, deselected)

    def selectedItems(self):
        return [self.model().itemFromIndex(i) for i in self.selectedIndexes()]

    def addItem(self, item):
        if not isinstance(item, LabelListWidgetItem):
            raise TypeError("item must be LabelListWidgetItem")
        self.model().setItem(self.model().rowCount(), 0, item)

    def removeItem(self, item):
        index = self.model().indexFromItem(item)
        self.model().removeRows(index.row(), 1)

    def selectItem(self, item):
        index = self.model().indexFromItem(item)
        self.selectionModel().select(index, QtCore.QItemSelectionModel.SelectionFlag.Select)

    def allItemList(self):
        itemList = list()
        for index in range(self.model().rowCount()):
            item = self.model().item(index)
            itemList.append(item)
        return itemList

    def itemFromShape(self, shape):
        for row in range(self.model().rowCount()):
            item = self.model().item(row, 0)
            if item.shape() == shape:
                return item
        raise ValueError(f"cannot find shape : {shape}")

    def clear(self):
        self.model().clear()


# class uniqLabelListWidgetItem(QtGui.QStandardItem):
#     def __init__(self, item=None):
#         super().__init__()
#         self.setText(item.text() or "")
#         self.setColor(item.shape().line_color)
#
#     def clone(self):
#         return LabelListWidgetItem(self.text(), self.color())
#
#     def setColor(self, shape):
#         self.setData(shape, QtCore.Qt.ItemDataRole.UserRole)
#
#     def color(self):
#         return self.data(QtCore.Qt.ItemDataRole.UserRole)  # return data for the UserRole
#
#
# class uniqStandardItemModel(QtGui.QStandardItemModel):
#     def data(self, index, role):
#         if role == QtCore.Qt.ItemDataRole.DecorationRole:
#             color = self.itemFromIndex(index).color()
#             return color
#
#         if role == QtCore.Qt.ItemDataRole.DisplayRole:
#             text = self.itemFromIndex(index).text()
#             return text

# class UniqLabelListWidget(LabelListWidget):
#     def __init__(self):
#         super().__init__()
#         for item in self.allItemList():
#             item.setCheckable(False)
#
#     def addItem(self, item):
#         if item in self.allItemList():
#             return
#         else:
#             super().addItem(item)

