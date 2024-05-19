from PySide2.QtWidgets import *
from PySide2.QtCore import *
from PySide2.QtGui import *
import requests
import threading

class ImageWidget(QWidget):
    penWidth = 1
    isLiked = False
    corner_radius = 50
    unlikedColor = QColor("#FFFFFF")
    likedColor = QColor("#1ED760")

    def __init__(self, parent=None,url=None):
        super(ImageWidget, self).__init__(parent=parent)
        self.image_label = QLabel(self)
        self.url = url
        # if url:
        #     self.getAndSetImageFromURL(url,self.geometry().height()-2*self.penWidth,self.geometry().height()-2*self.penWidth)  

    def setLiked(self,liked):
        self.isLiked = liked

    def setLikedColor(self,color):
        self.likedColor = color
    def setUnlikedColor(self,color):
        self.unlikedColor = color

    def updateCover(self,url):
        h = self.geometry().height()-(2*self.penWidth)
        w = self.geometry().width()-(2*self.penWidth)
        self.getAndSetImageFromURL(url,h,w) 
        self.update()

    def paintEvent(self,event):
        try:
            if not self.image:
                return
        except Exception:
            return
        painter = QPainter(self)
        rect = self.contentsRect()
        target_rect = QRect(self.geometry().x(), self.geometry().y()+self.penWidth, self.image.width(), self.image.height())
        #target_rect.moveCenter(rect.center())
        painter.drawPixmap(self.geometry().x()+self.penWidth,self.geometry().y()+self.penWidth, self.image)
        self.drawLikedCircle(painter)

    def drawLikedCircle(self,painter):

        if self.isLiked:
            pen = QPen(self.likedColor)
        else:
           pen = QPen(self.unlikedColor)
        pen.setWidth(self.penWidth)
        painter.setPen(pen)
        
        rec = self.geometry().adjusted(self.penWidth/2, 0, -self.penWidth/2, -self.penWidth/2)
        newRec = QRect(rec.x(),rec.y()+self.penWidth/2,self.rect().height()-self.penWidth,self.rect().height()-self.penWidth)

        pen.setWidth(self.penWidth)
        painter.setPen(pen)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.drawRoundedRect(newRec,self.corner_radius,self.corner_radius)

    def setImageFromBytes(self,bytes):
        h = self.geometry().height()-(2*self.penWidth)
        w = self.geometry().width()-(2*self.penWidth)

    def getAndSetImageFromURL(self, imageURL, width, height):
        thread = threading.Thread(target=self.thread_function,args =(imageURL, width, height))
        thread.start()

    def thread_function(self,imageURL, width, height):
        request = requests.get(imageURL)
        self.updateThing(request, width, height)

    def updateThing(self,request, width, height):
        if request.status_code == 200:
            pixmap = QPixmap()
            pixmap.loadFromData(request.content)

            # Scale the image to the desired size
            pixmap = pixmap.scaled(QSize(width, height), Qt.KeepAspectRatio, Qt.SmoothTransformation)

            # Apply the circular mask to the pixmap
            mask = QBitmap(pixmap.size())
            mask.fill(Qt.white)  # Start with a white mask
            painter = QPainter(mask)
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setBrush(Qt.black)
            
            path = QPainterPath()
            path.addRoundedRect(0, self.geometry().y(), width, height,self.corner_radius,self.corner_radius)
            
            brush = QBrush(Qt.red)
            painter.fillPath(path, brush)
            painter.drawPath(path)

            #painter.drawRoundedRect(self.penWidth/2, 0, width, height,self.corner_radius,self.corner_radius)

            # Set the masked pixmap to the QLabel
            self.image = pixmap
            self.image.setMask(mask)

            self.drawLikedCircle(painter)
            painter.end()
            #self.image.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)       
    
#.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)   

