# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'Start.ui'
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
                               QMainWindow, QMenuBar, QPushButton, QSizePolicy,
                               QSpacerItem, QStatusBar, QVBoxLayout, QWidget, QGraphicsDropShadowEffect)

class Ui_StartWindow(object):
    def setupUi(self, StartWindow):
        if not StartWindow.objectName():
            StartWindow.setObjectName(u"StartWindow")
        StartWindow.resize(200, 200)
        self.centralwidget = QWidget(StartWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.verticalLayout_2 = QVBoxLayout(self.centralwidget)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.titleLable = QLabel(self.centralwidget)
        self.titleLable.setObjectName(u"titleLable")
        self.titleLable.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.verticalLayout.addWidget(self.titleLable)

        self.InputLayout = QHBoxLayout()
        self.InputLayout.setObjectName(u"InputLayout")
        self.label = QLabel(self.centralwidget)
        self.label.setObjectName(u"label")

        self.InputLayout.addWidget(self.label)

        self.InputEdit = QLineEdit(self.centralwidget)
        self.InputEdit.setObjectName(u"InputEdit")

        self.InputLayout.addWidget(self.InputEdit)


        self.verticalLayout.addLayout(self.InputLayout)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer_2)

        self.noButton = QPushButton(self.centralwidget)
        self.noButton.setObjectName(u"noButton")

        self.horizontalLayout.addWidget(self.noButton)

        self.okButton = QPushButton(self.centralwidget)
        self.okButton.setObjectName(u"okButton")

        self.horizontalLayout.addWidget(self.okButton)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)


        self.verticalLayout.addLayout(self.horizontalLayout)


        self.verticalLayout_2.addLayout(self.verticalLayout)

        StartWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(StartWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 200, 33))
        StartWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(StartWindow)
        self.statusbar.setObjectName(u"statusbar")
        StartWindow.setStatusBar(self.statusbar)

        self.retranslateUi(StartWindow)

        QMetaObject.connectSlotsByName(StartWindow)

        # 添加阴影
        self.shadow = QGraphicsDropShadowEffect(self.centralwidget)
        self.shadow.setBlurRadius(15)
        self.shadow.setXOffset(0)
        self.shadow.setYOffset(0)
        self.shadow.setColor(QColor(0, 0, 0, 120))
        self.centralwidget.setGraphicsEffect(self.shadow)

        StartWindow.setWindowOpacity(0.90)

    # setupUi

    def retranslateUi(self, StartWindow):
        StartWindow.setWindowTitle(QCoreApplication.translate("StartWindow", u"MainWindow", None))
        self.titleLable.setText(QCoreApplication.translate("StartWindow", u"\u80fd\u56de\u5fc6\u8d77\u4f60\u7684\u540d\u5b57\u5417\uff1f", None))
        self.label.setText(QCoreApplication.translate("StartWindow", u"Dr.", None))
        self.InputEdit.setText("")
        self.InputEdit.setPlaceholderText(QCoreApplication.translate("StartWindow", u"\u6211\u7684\u540d\u5b57\u662f...", None))
        self.noButton.setText(QCoreApplication.translate("StartWindow", u"\u7761\u89c9", None))
        self.okButton.setText(QCoreApplication.translate("StartWindow", u"\u786e\u8ba4", None))
    # retranslateUi

