from PyQt6 import QtWidgets, QtGui, QtCore

class LabelDialog(QtWidgets.QDialog):
    def __init__(self, parent=None, uniqLabelList=None):
        super().__init__(parent)

        self.setWindowTitle("Set label name")

        QBtn = QtWidgets.QDialogButtonBox.StandardButton.Ok | QtWidgets.QDialogButtonBox.StandardButton.Cancel

        self.buttonbox = QtWidgets.QDialogButtonBox(QBtn)
        self.buttonbox.accepted.connect(self.saveLabel)
        self.buttonbox.rejected.connect(self.reject)

        self.layout = QtWidgets.QVBoxLayout()
        self.nameLayout = QtWidgets.QHBoxLayout()
        self.labelList = QtWidgets.QListWidget()
        label = [label.text() for label in uniqLabelList.allItemList() if uniqLabelList.model().item(0)]
        if label:
            self.labelList.addItems(label)
        self.labelList.itemClicked.connect(self.selectLabel)

        self.setName = QtWidgets.QLineEdit()
        self.setName.setPlaceholderText("Enter label name")

        self.nameLayout.addWidget(self.setName)
        self.nameLayout.addWidget(self.buttonbox)

        self.layout.addLayout(self.nameLayout)
        self.layout.addWidget(self.labelList)
        self.setLayout(self.layout)

    def saveLabel(self):
        if len(self.setName.text()) == 0:
            return
        self.accept()

    def selectLabel(self, selected):
        label = selected.text()
        self.setName.setText(label)
        self.saveLabel()
