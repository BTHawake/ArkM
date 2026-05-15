# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'ArkM.ui'
##
## Created by: Qt User Interface Compiler version 6.9.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QHBoxLayout, QLabel, QLineEdit,
    QListWidget, QListWidgetItem, QMainWindow, QMenuBar,
    QPushButton, QSizePolicy, QSlider, QStatusBar,
    QTextBrowser, QVBoxLayout, QWidget)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(800, 600)
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.horizontalLayout = QHBoxLayout(self.centralwidget)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.pendingDownloadLayout = QVBoxLayout()
        self.pendingDownloadLayout.setObjectName(u"pendingDownloadLayout")
        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.downloadSearchInput = QLineEdit(self.centralwidget)
        self.downloadSearchInput.setObjectName(u"downloadSearchInput")

        self.horizontalLayout_2.addWidget(self.downloadSearchInput)

        self.downloadSearchButton = QPushButton(self.centralwidget)
        self.downloadSearchButton.setObjectName(u"downloadSearchButton")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.downloadSearchButton.sizePolicy().hasHeightForWidth())
        self.downloadSearchButton.setSizePolicy(sizePolicy)

        self.horizontalLayout_2.addWidget(self.downloadSearchButton)


        self.pendingDownloadLayout.addLayout(self.horizontalLayout_2)

        self.label = QLabel(self.centralwidget)
        self.label.setObjectName(u"label")

        self.pendingDownloadLayout.addWidget(self.label)

        self.downloadlistWidget = QListWidget(self.centralwidget)
        self.downloadlistWidget.setObjectName(u"downloadlistWidget")

        self.pendingDownloadLayout.addWidget(self.downloadlistWidget)

        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.downloadButton = QPushButton(self.centralwidget)
        self.downloadButton.setObjectName(u"downloadButton")

        self.horizontalLayout_3.addWidget(self.downloadButton)

        self.downloadRefreshButton = QPushButton(self.centralwidget)
        self.downloadRefreshButton.setObjectName(u"downloadRefreshButton")

        self.horizontalLayout_3.addWidget(self.downloadRefreshButton)


        self.pendingDownloadLayout.addLayout(self.horizontalLayout_3)


        self.horizontalLayout.addLayout(self.pendingDownloadLayout)

        self.verticalLayout_2 = QVBoxLayout()
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_6 = QVBoxLayout()
        self.verticalLayout_6.setObjectName(u"verticalLayout_6")
        self.albumImage = QLabel(self.centralwidget)
        self.albumImage.setObjectName(u"albumImage")

        self.verticalLayout_6.addWidget(self.albumImage)

        self.downloadBrowser = QTextBrowser(self.centralwidget)
        self.downloadBrowser.setObjectName(u"downloadBrowser")

        self.verticalLayout_6.addWidget(self.downloadBrowser)

        self.verticalLayout_6.setStretch(0, 9)
        self.verticalLayout_6.setStretch(1, 1)

        self.verticalLayout_2.addLayout(self.verticalLayout_6)

        self.verticalLayout_3 = QVBoxLayout()
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.horizontalLayout_8 = QHBoxLayout()
        self.horizontalLayout_8.setObjectName(u"horizontalLayout_8")
        self.label_3 = QLabel(self.centralwidget)
        self.label_3.setObjectName(u"label_3")

        self.horizontalLayout_8.addWidget(self.label_3)

        self.progressSlider = QSlider(self.centralwidget)
        self.progressSlider.setObjectName(u"progressSlider")
        self.progressSlider.setOrientation(Qt.Orientation.Horizontal)

        self.horizontalLayout_8.addWidget(self.progressSlider)


        self.verticalLayout_3.addLayout(self.horizontalLayout_8)

        self.horizontalLayout_6 = QHBoxLayout()
        self.horizontalLayout_6.setObjectName(u"horizontalLayout_6")
        self.playButton = QPushButton(self.centralwidget)
        self.playButton.setObjectName(u"playButton")

        self.horizontalLayout_6.addWidget(self.playButton)

        self.pauseButton = QPushButton(self.centralwidget)
        self.pauseButton.setObjectName(u"pauseButton")

        self.horizontalLayout_6.addWidget(self.pauseButton)


        self.verticalLayout_3.addLayout(self.horizontalLayout_6)

        self.horizontalLayout_7 = QHBoxLayout()
        self.horizontalLayout_7.setObjectName(u"horizontalLayout_7")
        self.label_4 = QLabel(self.centralwidget)
        self.label_4.setObjectName(u"label_4")

        self.horizontalLayout_7.addWidget(self.label_4)

        self.volumeSlider = QSlider(self.centralwidget)
        self.volumeSlider.setObjectName(u"volumeSlider")
        self.volumeSlider.setOrientation(Qt.Orientation.Horizontal)

        self.horizontalLayout_7.addWidget(self.volumeSlider)

        self.stopButton = QPushButton(self.centralwidget)
        self.stopButton.setObjectName(u"stopButton")

        self.horizontalLayout_7.addWidget(self.stopButton)


        self.verticalLayout_3.addLayout(self.horizontalLayout_7)


        self.verticalLayout_2.addLayout(self.verticalLayout_3)


        self.horizontalLayout.addLayout(self.verticalLayout_2)

        self.verticalLayout_4 = QVBoxLayout()
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.musicSearchInput = QLineEdit(self.centralwidget)
        self.musicSearchInput.setObjectName(u"musicSearchInput")

        self.horizontalLayout_4.addWidget(self.musicSearchInput)

        self.musicSearchButton = QPushButton(self.centralwidget)
        self.musicSearchButton.setObjectName(u"musicSearchButton")

        self.horizontalLayout_4.addWidget(self.musicSearchButton)


        self.verticalLayout_4.addLayout(self.horizontalLayout_4)

        self.label_2 = QLabel(self.centralwidget)
        self.label_2.setObjectName(u"label_2")

        self.verticalLayout_4.addWidget(self.label_2)

        self.musicListWidget = QListWidget(self.centralwidget)
        self.musicListWidget.setObjectName(u"musicListWidget")

        self.verticalLayout_4.addWidget(self.musicListWidget)

        self.horizontalLayout_5 = QHBoxLayout()
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.deletButton = QPushButton(self.centralwidget)
        self.deletButton.setObjectName(u"deletButton")

        self.horizontalLayout_5.addWidget(self.deletButton)

        self.musicRefreshButton = QPushButton(self.centralwidget)
        self.musicRefreshButton.setObjectName(u"musicRefreshButton")

        self.horizontalLayout_5.addWidget(self.musicRefreshButton)


        self.verticalLayout_4.addLayout(self.horizontalLayout_5)


        self.horizontalLayout.addLayout(self.verticalLayout_4)

        self.verticalLayout_5 = QVBoxLayout()
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.logBrowser = QTextBrowser(self.centralwidget)
        self.logBrowser.setObjectName(u"logBrowser")

        self.verticalLayout_5.addWidget(self.logBrowser)

        self.clearLogButton = QPushButton(self.centralwidget)
        self.clearLogButton.setObjectName(u"clearLogButton")

        self.verticalLayout_5.addWidget(self.clearLogButton)


        self.horizontalLayout.addLayout(self.verticalLayout_5)

        self.horizontalLayout.setStretch(0, 1)
        self.horizontalLayout.setStretch(1, 2)
        self.horizontalLayout.setStretch(2, 1)
        self.horizontalLayout.setStretch(3, 1)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 800, 33))
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)

        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"MainWindow", None))
        self.downloadSearchButton.setText(QCoreApplication.translate("MainWindow", u"\u56de\u8f66\u641c\u7d22", None))
        self.label.setText(QCoreApplication.translate("MainWindow", u"\u5f85\u4e0b\u8f7d\u5217\u8868:", None))
        self.downloadButton.setText(QCoreApplication.translate("MainWindow", u"\u4e0b\u8f7d", None))
        self.downloadRefreshButton.setText(QCoreApplication.translate("MainWindow", u"\u5237\u65b0", None))
        self.albumImage.setText(QCoreApplication.translate("MainWindow", u"\u56fe\u7247\u5f85\u52a0\u8f7d", None))
        self.label_3.setText(QCoreApplication.translate("MainWindow", u"\u64ad\u653e:00:00/00:00", None))
        self.playButton.setText(QCoreApplication.translate("MainWindow", u"\u64ad\u653e", None))
        self.pauseButton.setText(QCoreApplication.translate("MainWindow", u"\u6682\u505c", None))
        self.label_4.setText(QCoreApplication.translate("MainWindow", u"\u97f3\u91cf", None))
        self.stopButton.setText(QCoreApplication.translate("MainWindow", u"\u7ec8\u6b62", None))
        self.musicSearchButton.setText(QCoreApplication.translate("MainWindow", u"\u56de\u8f66\u641c\u7d22", None))
        self.label_2.setText(QCoreApplication.translate("MainWindow", u"\u5df2\u4e0b\u8f7d\u5217\u8868:", None))
        self.deletButton.setText(QCoreApplication.translate("MainWindow", u"\u5220\u9664", None))
        self.musicRefreshButton.setText(QCoreApplication.translate("MainWindow", u"\u5237\u65b0", None))
        self.clearLogButton.setText(QCoreApplication.translate("MainWindow", u"\u6e05\u7a7a\u65e5\u5fd7", None))
    # retranslateUi

