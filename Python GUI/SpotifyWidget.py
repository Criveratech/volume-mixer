import PySide2.QtGui
from PySide2.QtWidgets import *
from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2 import QtWidgets
from IconWidget import IconWidget
from Overlay import OverlayWidget

class SpotifyWidget(QWidget):
    overlayPenWidth=4
    unlikedColor = QColor("#FFFFFF")
    likedColor = QColor("#1ED760")
    def __init__(self, parent=None, *args, **kwargs):
        super(SpotifyWidget, self).__init__(*args, **kwargs,parent=parent)
        #self.setAttribute(Qt.WA_StyledBackground, True)
        #self.setStyleSheet("background-color: #ffffff;")

        self.overlay = OverlayWidget(self)
        self.overlay.penWidth = self.overlayPenWidth
        self.overlay.setCornerRadius(15)

        im = IconWidget(self)
        self.im = im
        self.im.penWidth = self.overlayPenWidth

    def setProgressStartPercent(self,percent):
        self.overlay.progressStartPercent = percent

    def setCornerRadius(self,cornerRadius):
        self.overlay.setCornerRadius(cornerRadius)
        self.im.setCornerRadius(cornerRadius)

    def update(self, event):
        super().update(event)
        
    def updateSong(self,song):
        self.overlay.setGeometry(self.rect())
        self.im.setGeometry(QRect(0,0,self.rect().height(),self.rect().height()))

        self.im.updateIcon(song["url"])

        if song["isLiked"]:
            self.im.setOutlineColor(self.likedColor)
        else:
            self.im.setOutlineColor(self.unlikedColor)

        self.overlay.updateProgress(song["trackLength"],song["trackPlayed"])
        self.overlay.setLiked(song["isLiked"])
        self.overlay.updateSongNameAndArtist(song["trackName"],song["artist"])
        self.overlay.visible = True

        #song["type"]
        #song["url"]
        #song["trackName"]
        #song["artist"]

    def milliseconds_to_minutes_seconds(milliseconds):
        seconds = int(milliseconds / 1000)
        minutes, seconds = divmod(seconds, 60)
        return f"{minutes} minutes and {seconds} seconds"

    def paintEvent(self,event):
        super().paintEvent(event)