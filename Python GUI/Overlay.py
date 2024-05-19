from PySide2.QtWidgets import *
from PySide2.QtCore import *
from PySide2.QtGui import *
import math

class OverlayWidget(QWidget):
    some_action_signal = Signal()
    isLiked = False
    songName = ""
    artist = ""
    corner_radius = 50
    percent=1
    clipWidth = 0
    visible = False

    #colors
    frameColor = QColor("#FFFFFF")
    progressColor = QColor("#1ED760")
    unlikedColor = QColor("#FFFFFF")
    likedColor = QColor("#1ED760")

    progressStartPercent = 0
    penWidth = 6

    def __init__(self, parent=None,rect=None):
        super(OverlayWidget, self).__init__(parent=parent)

    def setCornerRadius(self,radius):
        self.corner_radius = radius
        
    def setGeometry(self,geometry):
        super().setGeometry(geometry)

    def setLiked(self,liked):
        self.isLiked = liked

    def mousePressEvent(self,event):
        self.isLiked!=self.isLiked
        self.some_action_signal.emit()

    def scale(self,val, src, dst):
        return ((val - src[0]) / (src[1]-src[0])) * (dst[1]-dst[0]) + dst[0]

    def updateProgress(self,length,played):
        percent = played/length
        self.percent = 1-self.scale(percent,(0.0,1),(self.progressStartPercent/100,1))
        self.update()

    def updateSongNameAndArtist(self,name,artist):
        self.songName=name
        self.artist=artist

    def drawSongName(self,painter):

        if self.isLiked:
            pen = QPen(self.likedColor)
        else:
            pen = QPen(self.unlikedColor)
        pen.setWidth(self.penWidth)
        painter.setPen(pen)

        font = QFont("Helvetica [Cronyx]")  # Example font

        bbrect = self.geometry() #wrong for some reason, too big
        font.setPixelSize(bbrect.height()*0.3)
        painter.setFont(font)
        font_metrics = QFontMetrics(font)
        text_rect = font_metrics.boundingRect(self.songName)
        center_x = bbrect.width()*0.3
        center_y = self.height() // 2
        painter.drawText(center_x,center_y,self.songName)

    def drawArtistNames(self,painter):
        
        if self.isLiked:
            pen = QPen(self.likedColor)
        else:
            pen = QPen(self.unlikedColor)
        pen.setWidth(self.penWidth)
        painter.setPen(pen)

        font = QFont("Helvetica [Cronyx]")  # Example font
        font_metrics = QFontMetrics(font)
        bbrect = self.geometry()
        font.setPixelSize(bbrect.height()*0.2)
        painter.setFont(font)
        text_rect_artist = font_metrics.boundingRect(self.artist)

        center_x_artist =  bbrect.width()*0.3
        center_y_artist = self.height() // 1.3
        painter.drawText(center_x_artist,center_y_artist,self.artist)

    def drawProgressRect(self,painter):
        pen = QPen(self.progressColor)
        pen.setWidth(self.penWidth)
        painter.setPen(pen)
        
        painter.setClipping(True)
        rec = self.geometry().adjusted(self.penWidth/2, self.penWidth/2, -self.penWidth/2, -self.penWidth/2)
        rec2 = rec.adjusted(-self.penWidth/2, -self.penWidth/2, math.ceil(self.penWidth/2-rec.width()*self.percent), self.penWidth/2)
        painter.setClipRect(rec2,Qt.ReplaceClip)
        painter.drawRoundedRect(rec,self.corner_radius,self.corner_radius)
        painter.setClipping(False)

    def drawFrame(self,painter):
        
        pen = QPen(self.frameColor)
        pen.setWidth(self.penWidth)
        painter.setPen(pen)
        

        rec = self.rect().adjusted(self.penWidth/2, self.penWidth/2, -self.penWidth/2, -self.penWidth/2)
        painter.drawRoundedRect(rec,self.corner_radius,self.corner_radius)

    def paintEvent(self,event):
        if not self.visible:
            return
        else:
            super().paintEvent(event)
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)

            self.drawFrame(painter)
            self.drawProgressRect(painter)
            self.drawSongName(painter)
            self.drawArtistNames(painter)
            painter.end()