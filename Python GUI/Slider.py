from PySide2.QtWidgets import *
from PySide2.QtCore import *
from PySide2.QtGui import *
from IconWidget import IconWidget
#subclass of qslider for that bar look and added functionality
class SliderWithText(QSlider):
    font = QFont("Helvetica [Cronyx]")  # Example font
    textColor = QColor("#F5F5DC")
    iconScale = 1
    def __init__(self, orientation,text,value,websocket):
        super().__init__(orientation)
        self.websocket = websocket
        self.active=True
        self.setRange(0,1000)
        self.setValue(value)
        self.text=text
        self.font_metrics = QFontMetrics(self.font)

        
        
    def setIconScale(self,scale):
        self.iconScale = scale

    def mousePressEvent(self, event):
        self.mouseMoveEvent(event)
        return

    def drawIcon(self,bytes):
        self.im = IconWidget(self)
        self.im.penWidth = 6
        self.im.setGeometry(QRect(0,0,self.rect().height(),self.rect().height()))
        self.im.scale = self.iconScale
        self.im.updateIcon(bytes)
        self.bytes = bytes

    def drawIconAtPos(self,bytes,xPos):
        self.im.setGeometry(QRect(xPos,0,self.rect().height(),self.rect().height()))
        self.im.updateIcon(bytes)

    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)
        mouse_position = event.pos().x()
        slider_range = self.maximum() - self.minimum()
        pixel_range = self.width() - self.style().sliderPositionFromValue(self.maximum(),
                                                                          self.minimum(),
                                                                          self.maximum(),
                                                                          self.width())
        value = self.minimum() + ((mouse_position / pixel_range) * slider_range)
        value = max(0, min(value, 1000))
        self.setValue(int(value))
        self.websocket.sendTextMessage('{"type":"volume","name":"'+self.text+'","volume":'+str(self.value()/1000)+'}')
        return
    
    def mouseReleaseEvent(self, event):
        return

    #painter.setCompositionMode(QPainter.CompositionMode_DestinationOut) works weird for overlap colour? prolly using it wrong
    def paintEvent(self, event):
        super().paintEvent(event) 
    
        painter = QPainter(self)
        painter.setPen(self.textColor)
            

        bbrect = self.geometry()
        volumeRect = QRect(0,0,self.value()/1000*self.width()+1,bbrect.height())
        painter.fillRect(volumeRect, self.volumeColor)#QColor("#1ED760"))
        
        if self.im:
            self.im.lower()

        font = self.font
        font.setPixelSize(bbrect.height()*0.4)
        painter.setFont(self.font)
        font_metrics = QFontMetrics(font)
        
        textBB = font_metrics.tightBoundingRect(self.text)

        textOriginX = (bbrect.width()-textBB.width()*2)/2
        textOriginY = (bbrect.height()+textBB.height()*2)/2

        p = QPoint(textOriginX,textOriginY)
        pR = QRect(textOriginX,textOriginY,textBB.width()*2,-textBB.height()*2)
        painter.drawText(pR,Qt.AlignCenter,self.text)

        painter.drawRect(QRect(bbrect.x(),bbrect.y(),bbrect.width()-1,bbrect.height()-1))

        painter.drawRect(0,0,self.geometry().width()-1,self.geometry().height()-1)

    def setText(self, text):
        self.text = text
        self.update()


    def slider_value_changed(self, value):
        # Update the text on the slider handle
        self.slider.setText(str(value))