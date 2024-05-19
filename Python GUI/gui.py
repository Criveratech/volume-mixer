import os
from pathlib import Path
import json
import sys
import base64
from configparser import ConfigParser

from PySide2.QtWidgets import *
from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWebSockets import QWebSocket

from SpotifyWidget import SpotifyWidget
from Slider import SliderWithText

print(os.path.join(Path(__file__).parent.parent.resolve(),'config.ini'))
config = ConfigParser()
config.read(os.path.join(Path(__file__).parent.parent.resolve(),'config.ini'))
enableSpotifyPlugin = config.getboolean('General', 'enableSpotifyPlugin')
turnScreenOffWithoutConnection = config.getboolean('PyGui', 'turnScreenOffWithoutConnection')
wssUrl = config.get('PyGui', 'wssUrl') 
windowWidth = config.getint('PyGui', 'windowWidth')
windowHeight = config.getint('PyGui', 'windowHeight')
autoFullscreen = config.get('PyGui', 'autoFullscreen')
hideCursor = config.get('PyGui', 'hideCursor')

#1ED760 spotify like green

def muteColor(color):
    #disabled for now
    h, s, l, a = color.getHslF()
    muted_s = s * 0.5
    muted_color = QColor.fromHslF(h, muted_s, l, a)
    return color#muted_color
       

class VolumeController(QWidget):
    websocket = None
    layout = None
    sliders = []
    def __init__(self, websocketUrl="", *args, **kwargs):
        super(VolumeController, self).__init__(*args, **kwargs)

        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(5, 5, 5, 5)
        self.setLayout(self.layout)
        
        self.websocket = QWebSocket()
        self.websocket.open(websocketUrl)

        self.websocket.connected.connect(self.on_connected)
        self.websocket.disconnected.connect(self.on_disconnected)
        self.websocket.textMessageReceived.connect(self.on_message_received)

        
        #
        if enableSpotifyPlugin:
            self.spotifyWidget = SpotifyWidget(self)
            self.layout.addWidget(self.spotifyWidget)
            self.spotifyWidget.overlay.some_action_signal.connect(self.on_button_click)
            self.spotifyWidget.setFixedHeight(self.geometry().height()/6.4)
            self.spotifyWidget.setCornerRadius(15)
            self.spotifyWidget.setProgressStartPercent(15)
        

    def on_button_click(self): 
        self.websocket.sendTextMessage('{"type":"likeSong"}')
        
    def on_connected(self):
        print("Connected to WebSocket")
        if turnScreenOffWithoutConnection:
            os.system("vcgencmd display_power 1")

    def on_disconnected(self):
        print("Disconnected from WebSocket")
        if turnScreenOffWithoutConnection:
            os.system("vcgencmd display_power 0")
        self.websocket.close()
        #restart connection
        self.websocket.open(wssUrl)

    def on_message_received(self, message):
        update = json.loads(message)
        if update["type"] =="songUpdate":
            if enableSpotifyPlugin:
                self.spotifyWidget.updateSong(update)
            
        elif update["type"] =="mixerUpdate":
            procs = update["procs"]
            for slider in self.sliders:
                slider.deleteLater()
                
            self.sliders.clear()

            for proc in procs: 
                slider = SliderWithText(Qt.Horizontal,proc["name"],proc["volume"]*1000,self.websocket)
                slider.volumeColor = QColor("#339A33")
                slider.setIconScale(0.5)
                slider.setStyleSheet("QSlider::groove:horizontal {border: none;background: none;}")
                slider.setFixedHeight(self.geometry().height()/10)
                if proc["iconBytes"] != "":
                    received_bytes = base64.b64decode(proc["iconBytes"])
                    slider.drawIcon(received_bytes)

                self.layout.addWidget(slider)
                self.sliders.append(slider)

#start off with the display off, it will be turned on if the connection is successful
#in on_connected
#these calls result in errors when used in windows (they can be ignored though)
if turnScreenOffWithoutConnection:
    os.system("vcgencmd display_power 0")

# Create the application
app = QApplication([])
# Create the main window widget and layout
window = VolumeController(wssUrl)
window.resize(windowWidth,windowHeight)
window.setAttribute(Qt.WA_StyledBackground, True)
window.setStyleSheet("background-color: #222222;")



#i developed this in windows so i needed my cursor and didnt want fullscreen
# if sys.platform.startswith('win'):
#     window.show()
# #pi zero with a 5" touchscreen
# elif sys.platform.startswith('linux'):
if hideCursor:
    window.setCursor(Qt.BlankCursor)
if autoFullscreen:
    window.showFullScreen()


# Start the event loop
app.exec_()

#vcgencmd display_power 0/1 to turn off on the display, touch will still work, need to keep that in mind