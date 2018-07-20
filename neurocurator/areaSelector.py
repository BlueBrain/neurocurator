#!/usr/bin/python3

__author__ = "Christian O'Reilly"

import os.path
import pickle
from warnings import warn

import numpy as np
from PyQt5.QtCore import (pyqtSignal, pyqtSlot, QRect, QTimer, QSize, QObject,
                          QThread, Qt)
from PyQt5.QtGui import QPalette, QPixmap, QImage, QKeySequence
from PyQt5.QtWidgets import (QRubberBand, QLabel, QMenu, QMenuBar, QAction,
                             QVBoxLayout, QScrollArea, QSizePolicy,
                             QHBoxLayout, QPushButton, QWidget, QDialog)
from wand.image import Image


class SplashDlg(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.SplashScreen | Qt.WindowStaysOnTopHint)
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Please wait while rendering PDF pages...", self))
        self.setLayout(layout)


class RenderingThread(QThread):

    def __init__(self, parent=None):
        super().__init__(parent)
        self._parent = parent
        self.renderingFinished     = False

    def run(self):
        self._parent.pages = []
        with Image(filename=self._parent.fileName, resolution=self._parent.resolution) as pdf:
            pages = len(pdf.sequence)
            for i in range(pages):
                with Image(width=pdf.width, height=pdf.height) as im:
                    im.composite(pdf.sequence[i], top=0, left=0)
                    self._parent.pages.append(im.make_blob('png'))



class PDFAreaSelector(QObject):

    areaSelected = pyqtSignal()

    def exec_(self):
        self.open()

    def __init__(self, fileName, parent=None):
        super().__init__(parent)

        self.fileName = fileName
        self.resolution = 150
        self.pages = []
        self.currentPageInd = 0

    def open(self, interactive=True):
        self.isInteractive = interactive
        if self.hasBeenCached():
            self.loadCachedRendering()
            if not self.pages is None:
                # Loading cached version succeeded
                if interactive:
                    self.selectDlg = PDFAreaSelectorDlg(self)
                    self.selectDlg.exec_()
                return

        self.waitWidget = SplashDlg()
        self.waitWidget.show()

        self.renderThread = RenderingThread(self)
        self.renderThread.start()
        self.renderThread.finished.connect(self.pdfRendered)


    @pyqtSlot()
    def pdfRendered(self):
        
        self.waitWidget.close()
        if self.isInteractive:
            self.selectDlg = PDFAreaSelectorDlg(self)
            self.selectDlg.exec_()
        self.cacheRendering()        


    def cacheRendering(self):
        fileName = self.fileName + "_cachedRendering"
        try:
            with open(fileName, 'wb') as f:
                pickle.dump(self.pages, f)
        except:
            warn("Failed to cach the rendering of the PDF paper.")
            pass


    def loadCachedRendering(self):
        fileName = self.fileName + "_cachedRendering"
        try:
            with open(fileName, 'rb') as f:
                self.pages = pickle.load(f)
        except:
            warn("Failed to load the cached rendering of the PDF paper.")
            self.pages = None



    def hasBeenCached(self):
        return os.path.isfile(self.fileName + "_cachedRendering") 











    

class PDFAreaSelectorDlg(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)

        self._parent = parent

        self.setWindowTitle("Area selection")
        self.scaleFactor = 1
        self.setModal(True)

        self.controlBarWgt         = QWidget(self)
        self.nextPageBtn         = QPushButton("Next page (Ctrl+right arrow)")
        self.previousPageBtn     = QPushButton("Previous page (Ctrl+left arrow)")
        self.noPageTxt             = QLabel("1")
        self.noPageTxt.setStyleSheet("border: 1px solid grey")
        self.noPageTxt.setFixedWidth(40)

        self.controlBarWgt.setLayout(QHBoxLayout())

        self.nextPageBtn.clicked.connect(self.nextPage)
        self.previousPageBtn.clicked.connect(self.previousPage)

        self.controlBarWgt.layout().addWidget(self.previousPageBtn)
        self.controlBarWgt.layout().addWidget(self.noPageTxt)
        self.controlBarWgt.layout().addWidget(self.nextPageBtn)

        self.imageLabel = ImageWidget()
        self.imageLabel.setBackgroundRole(QPalette.Base)
        self.imageLabel.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.imageLabel.setScaledContents(True)

        self.scrollArea = QScrollArea()
        self.scrollArea.setBackgroundRole(QPalette.Dark)
        self.scrollArea.setWidget(self.imageLabel)

        self.createActions()
        self.createMenus()

        self.setLayout(QVBoxLayout())
        self.layout().addWidget(self.menuBar)
        self.layout().addWidget(self.controlBarWgt)
        self.layout().addWidget(self.scrollArea)

        self.imageLabel.areaSelected.connect(self.resendSelectedEvent)

        self.loadImage()

    @pyqtSlot(float, float, float, float, QPixmap)
    def resendSelectedEvent(self, x, y, width, height, image):
        self._parent.x = x
        self._parent.y = y
        self._parent.width = width
        self._parent.height = height
        self._parent.image = image

        self._parent.areaSelected.emit()
        self.close()


    def loadImage(self):
        image = QImage.fromData(self._parent.pages[self._parent.currentPageInd],"PNG")

        self.imageLabel.setPixmap(QPixmap.fromImage(image))
        self.fitToWindowAct.setEnabled(True)
        self.updateActions()

        if not self.fitToWindowAct.isChecked():
            self.imageLabel.adjustSize()

        self.setWindowFilePath(self._parent.fileName)
        return True


    def zoomIn(self):
        self.scaleImage(1.25)


    def zoomOut(self):
        self.scaleImage(0.8)


    def normalSize(self):
        self.imageLabel.adjustSize()
        self.scaleFactor = 1.0

    def fitToWindow(self):
        fitToWindow = self.fitToWindowAct.isChecked()
        self.scrollArea.setWidgetResizable(fitToWindow)
        if not fitToWindow :
            self.normalSize()
        self.updateActions()



    def createActions(self):

        self.exitAct = QAction("E&xit", self)
        self.exitAct.setShortcut("Ctrl+Q")
        self.exitAct.triggered.connect(self.close)

        self.zoomInAct = QAction("Zoom &In (25%)", self)
        self.zoomInAct.setShortcut("Ctrl++")
        self.zoomInAct.setEnabled(False)
        self.zoomInAct.triggered.connect(self.zoomIn)

        self.zoomOutAct = QAction("Zoom &Out (25%)", self)
        self.zoomOutAct.setShortcut("Ctrl+-")
        self.zoomOutAct.setEnabled(False)
        self.zoomOutAct.triggered.connect(self.zoomOut)

        self.normalSizeAct = QAction("&Normal Size", self)
        self.normalSizeAct.setShortcut("Ctrl+S")
        self.normalSizeAct.setEnabled(False)
        self.normalSizeAct.triggered.connect(self.normalSize)

        self.fitToWindowAct = QAction("&Fit to Window", self)
        self.fitToWindowAct.setEnabled(False)
        self.fitToWindowAct.setCheckable(True)
        self.fitToWindowAct.setShortcut("Ctrl+F")
        self.fitToWindowAct.triggered.connect(self.fitToWindow)



        self.nextPageAct = QAction("&Next page", self)
        self.nextPageAct.setEnabled(True)
        self.nextPageAct.setShortcut(QKeySequence(Qt.CTRL + Qt.Key_Right))
        self.nextPageAct.triggered.connect(self.nextPage)


        self.previousPageAct = QAction("&Previous page", self)
        self.previousPageAct.setEnabled(True)
        self.previousPageAct.setShortcut(QKeySequence(Qt.CTRL + Qt.Key_Left))
        self.previousPageAct.triggered.connect(self.previousPage)



    def createMenus(self):

        self.menuBar = QMenuBar(self)

        self.fileMenu = QMenu("&File", self)
        self.fileMenu.addAction(self.exitAct)

        self.viewMenu = QMenu("&View", self)
        self.viewMenu.addAction(self.zoomInAct)
        self.viewMenu.addAction(self.zoomOutAct)
        self.viewMenu.addAction(self.normalSizeAct)
        self.viewMenu.addSeparator()
        self.viewMenu.addAction(self.fitToWindowAct)
        self.viewMenu.addSeparator()
        self.viewMenu.addAction(self.nextPageAct)
        self.viewMenu.addAction(self.previousPageAct)

        self.menuBar.addMenu(self.fileMenu)
        self.menuBar.addMenu(self.viewMenu)



    def updateActions(self):

        self.zoomInAct.setEnabled(not self.fitToWindowAct.isChecked())
        self.zoomOutAct.setEnabled(not self.fitToWindowAct.isChecked())
        self.normalSizeAct.setEnabled(not self.fitToWindowAct.isChecked())



    def scaleImage(self, factor):
        assert(self.imageLabel.pixmap())
        self.scaleFactor *= factor
        self.imageLabel.resize(self.scaleFactor * self.imageLabel.pixmap().size())

        self.adjustScrollBar(self.scrollArea.horizontalScrollBar(), factor)
        self.adjustScrollBar(self.scrollArea.verticalScrollBar(), factor)

        self.zoomInAct.setEnabled(self.scaleFactor < 3.0)
        self.zoomOutAct.setEnabled(self.scaleFactor > 0.333)


    def adjustScrollBar(self, scrollBar, factor):
        scrollBar.setValue(int(factor * scrollBar.value()
                                + ((factor - 1) * scrollBar.pageStep()/2)))



    def nextPage(self):
        if self._parent.currentPageInd < len(self._parent.pages)-1:
            self._parent.currentPageInd += 1
            self.loadImage()
            self.noPageTxt.setText(str(self._parent.currentPageInd+1))

    def previousPage(self):
        if self._parent.currentPageInd > 0:
            self._parent.currentPageInd -= 1
            self.loadImage()
            self.noPageTxt.setText(str(self._parent.currentPageInd+1))






class ImageWidget(QLabel):

    areaSelected = pyqtSignal(float, float, float, float, QPixmap)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.rubberBand  = None
        self.origin         = None

    def mousePressEvent(self, event):
        self.origin = event.pos()
        if self.rubberBand is None:
            self.rubberBand = QRubberBand(QRubberBand.Rectangle, self)
        self.rubberBand.setGeometry(QRect(self.origin, QSize()))
        self.rubberBand.show()

    def mouseMoveEvent(self, event):
        self.rubberBand.setGeometry(QRect(self.origin, event.pos()).normalized())


    def mouseReleaseEvent(self, event):
        self.rubberBand.hide()
        zoreRect = QRect(self.origin, event.pos()).normalized()
        pixmapSize = self.pixmap().size()
        pixX1 = zoreRect.x()
        pixX2 = zoreRect.x() + zoreRect.width()
        pixY1 = zoreRect.y()
        pixY2 = zoreRect.y() + zoreRect.height()
        width  = pixmapSize.width()
        height = pixmapSize.height()

        x1 = pixX1/width 
        x1 = x1 if x1 >= 0.0 else 0.0
        x1 = x1 if x1 <= 1.0 else 1.0
        y1 = pixY1/height 
        y1 = y1 if y1 >= 0.0 else 0.0
        y1 = y1 if y1 <= 1.0 else 1.0
        x2 = pixX2/width 
        x2 = x2 if x2 >= 0.0 else 0.0
        x2 = x2 if x2 <= 1.0 else 1.0
        y2 = pixY2/height 
        y2 = y2 if y2 >= 0.0 else 0.0
        y2 = y2 if y2 <= 1.0 else 1.0

        rect = QRect(min(pixX1, pixX2), min(pixY1, pixY2), abs(pixX1- pixX2), abs(pixY1- pixY2))
        selectedImg = self.pixmap().copy(rect)
        
        self.areaSelected.emit(min(x1, x2), min(y1, y2), np.abs(x1-x2), np.abs(y1-y2), selectedImg)
    









def loadImage(fileName, pageNo, x, y, width, height):

    areaSelector = PDFAreaSelector(fileName)
    areaSelector.open(interactive=False)
    i = 0
    timer = QTimer()
    while len(areaSelector.pages) == 0 and i < 120:
        i += 1
        timer.start(500)
        
    image = QImage.fromData(areaSelector.pages[pageNo-1],"PNG")
    pixmap = QPixmap.fromImage(image)

    pixmapSize = pixmap.size()
    widthImg  = pixmapSize.width()
    heightImg = pixmapSize.height()

    rect = QRect(x*widthImg, y*heightImg, width*widthImg, height*heightImg)
    return pixmap.copy(rect)
    







