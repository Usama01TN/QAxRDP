# coding=utf-8
"""
Plugin preview: shows what Qt Designer gets from each QAxRDP plugin (icon, texts, a design mode instance and the
default XML) and launches Qt Designer with the plugins registered.
"""
from ManyQt.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QListWidget, QListWidgetItem, QLabel, \
    QPlainTextEdit, QPushButton, QFrame, QMessageBox
from ManyQt.QtCore import Qt, QSize, pyqtSlot
from ManyQt.QtGui import QFont
from os.path import dirname
from sys import path

if dirname(__file__) not in path:
    path.append(dirname(__file__))

try:
    from .widgetinfo import WIDGETS, GROUP, INCLUDE_FILE
    from .designer import launchDesigner, pluginDirectory, selectApi
except:
    from widgetinfo import WIDGETS, GROUP, INCLUDE_FILE
    from designer import launchDesigner, pluginDirectory, selectApi


class MainWindow(QMainWindow):
    """
    MainWindow class.
    """

    def __init__(self, *args, **kwargs):
        """
        :param args: any
        :param kwargs: any
        """
        super(MainWindow, self).__init__(*args, **kwargs)
        self.setWindowTitle(self.tr(u'QAxRDP Qt Designer plugins'))
        self.resize(1000, 640)
        self.__m_preview = None  # type: QWidget | None
        # Widget list, as in Designer's widget box.
        self.widgetList = QListWidget()  # type: QListWidget
        self.widgetList.setIconSize(QSize(32, 32))
        self.widgetList.setFixedWidth(220)
        for info in WIDGETS:
            QListWidgetItem(info.icon(), info.displayName, self.widgetList)
        # Details.
        self.titleLabel = QLabel()  # type: QLabel
        self.titleLabel.setTextFormat(Qt.RichText)
        self.toolTipLabel = QLabel()  # type: QLabel
        self.toolTipLabel.setWordWrap(True)
        self.previewFrame = QFrame()  # type: QFrame
        self.previewFrame.setFrameShape(QFrame.StyledPanel)
        self.previewFrame.setMinimumHeight(140)
        self.previewLayout = QVBoxLayout(self.previewFrame)  # type: QVBoxLayout
        self.xmlView = QPlainTextEdit()  # type: QPlainTextEdit
        self.xmlView.setReadOnly(True)
        mono = QFont('Monospace')  # type: QFont
        mono.setStyleHint(QFont.TypeWriter)
        self.xmlView.setFont(mono)
        launch = QPushButton(self.tr(u'Launch Qt Designer'))  # type: QPushButton
        launch.clicked.connect(self.onLaunchDesigner)
        details = QWidget()  # type: QWidget
        detailsLayout = QVBoxLayout(details)  # type: QVBoxLayout
        detailsLayout.addWidget(self.titleLabel)
        detailsLayout.addWidget(self.toolTipLabel)
        detailsLayout.addWidget(self.previewFrame, 2)
        detailsLayout.addWidget(QLabel(self.tr(u'Default XML (domXml):')))
        detailsLayout.addWidget(self.xmlView, 1)
        detailsLayout.addWidget(launch, 0, Qt.AlignRight)
        wdg = QWidget()  # type: QWidget
        layout = QHBoxLayout(wdg)  # type: QHBoxLayout
        layout.addWidget(self.widgetList)
        layout.addWidget(details, 1)
        self.setCentralWidget(wdg)
        self.statusBar().showMessage(self.tr(u'Plugin directory: {}').format(pluginDirectory()))
        self.widgetList.currentRowChanged.connect(self.onCurrentChanged)
        self.widgetList.setCurrentRow(0)

    @pyqtSlot(int)
    def onCurrentChanged(self, row):
        """
        :param row: int
        :return:
        """
        if not 0 <= row < len(WIDGETS):
            return
        info = WIDGETS[row]  # type: WidgetInfo
        self.titleLabel.setText('<b>{}</b> &nbsp; {} &nbsp; <i>group</i> {} &nbsp; <i>from</i> {} <i>import</i> {}'
                                .format(info.displayName, info.name(), GROUP, INCLUDE_FILE, info.name()))
        self.toolTipLabel.setText('{}<br><br>{}'.format(info.toolTip, info.whatsThis))
        self.xmlView.setPlainText(info.domXml())
        if self.__m_preview is not None:
            self.previewLayout.removeWidget(self.__m_preview)
            self.__m_preview.deleteLater()
        self.__m_preview = info.create()  # type: QWidget
        if info.width < 300:
            self.__m_preview.setFixedSize(max(info.width, 24), max(info.height, 24))
            self.previewLayout.addWidget(self.__m_preview, 0, Qt.AlignCenter)
        else:
            self.__m_preview.setMinimumSize(160, min(info.height, 120))
            self.previewLayout.addWidget(self.__m_preview, 1)

    @pyqtSlot()
    def onLaunchDesigner(self):
        """
        :return:
        """
        try:
            launchDesigner(api=selectApi())
        except RuntimeError as e:
            QMessageBox.information(self, self.windowTitle(), '{}'.format(e))
