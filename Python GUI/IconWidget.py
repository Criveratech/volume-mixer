from PySide2.QtWidgets import *
from PySide2.QtCore import *
from PySide2.QtGui import *
import requests
import threading

class IconWidget(QWidget):
    penWidth = 1
    corner_radius = 50
    scale=1
    def __init__(self, parent=None):
        super(IconWidget, self).__init__(parent=parent)
        #self.setAttribute(Qt.WA_StyledBackground, True)
        #self.setStyleSheet("background-color: #ffffff;")

    def setUrl(self,url):
        self.url = url
    def setScale(self,scale):
        self.scale = scale
    def setOutlineColor(self,color):
        self.outLineColor = color

    def setCornerRadius(self,radius):
        self.corner_radius = radius

    def updateIcon(self,urlOrBytes):
        h = (self.geometry().height()-(2*self.penWidth))*self.scale+2
        w = (self.geometry().width()-(2*self.penWidth))*self.scale+2

        #string = url, else = bytes
        if isinstance(urlOrBytes, str):
            self.getAndSetImageFromURL(urlOrBytes,h,w) 
        else:
            self.setImageFromBytes(urlOrBytes,h,w)

        self.update()

    def paintEvent(self,event):
        try:
            if not self.image:
                return
        except Exception:
            return
        
        painter = QPainter(self)
        centerX = self.geometry().width()/2-self.image.width()/2
        centerY = self.geometry().height()/2-self.image.height()/2
        painter.setRenderHint(QPainter.Antialiasing,True)
        painter.drawPixmap(centerX,centerY, self.image)
        self.drawOutline(painter)

    def drawOutline(self,painter):

        try:
            if not self.outLineColor:
                return
        except:
            return
        
        pen = QPen(self.outLineColor)   
        pen.setWidth(self.penWidth)
        painter.setPen(pen)
        
        rec = self.geometry().adjusted(self.penWidth/2, 0, -self.penWidth/2, -self.penWidth/2)
        newRec = QRect(rec.x(),rec.y()+self.penWidth/2,self.rect().height()-self.penWidth,self.rect().height()-self.penWidth)

        pen.setWidth(self.penWidth)
        painter.setPen(pen)
        painter.setRenderHint(QPainter.Antialiasing,True)
        painter.drawRoundedRect(newRec,self.corner_radius,self.corner_radius)

    def setImageFromBytes(self,bytes,width, height):
        img = QImage(bytes, 32, 32, QImage.Format_ARGB32)
        pixmap = QPixmap.fromImage(img)
        self.pixmapToIcon(pixmap, width, height,False)

    def getAndSetImageFromURL(self, imageURL, width, height):
        thread = threading.Thread(target=self.thread_function,args =(imageURL, width, height))
        thread.start()

    def thread_function(self,imageURL, width, height):
        request = requests.get(imageURL)
        self.requestToImage(request, width, height)

    def pixmapToIcon(self,pixmap, width, height,applyMask):
        
        # Scale the image to the desired size
        pixmap = pixmap.scaled(QSize(width, height), Qt.KeepAspectRatio, Qt.SmoothTransformation)

        # Apply the circular mask to the pixmap
        mask = QBitmap(pixmap.size())
        mask.fill(Qt.white)  # Start with a white mask
        painter = QPainter(mask)
        painter.setRenderHint(QPainter.Antialiasing,True)
        painter.setBrush(Qt.black)
        
        path = QPainterPath()
        path.addRoundedRect(0, 0, width, height,self.corner_radius,self.corner_radius)
        
        brush = QBrush(Qt.red)
        painter.fillPath(path, brush)
        painter.drawPath(path)

        # Set the masked pixmap to the QLabel
        self.image = pixmap
        if applyMask:
            self.image.setMask(mask)

        self.image = pixmap.scaled(QSize(width, height), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        #self.drawOutline(painter)
        painter.end()

    def requestToImage(self,request, width, height):
        if request.status_code == 200:
            pixmap = QPixmap()
            pixmap.loadFromData(request.content)
            self.pixmapToIcon(pixmap,width,height,True)

