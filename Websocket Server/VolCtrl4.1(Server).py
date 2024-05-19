import asyncio
import websockets
import json
import time

import test
import psutil

from configparser import ConfigParser
from pathlib import Path
import os

from AudioUtilities import MyAudioUtilities

import spotipy

from ctypes import Array, byref, c_char, memset, sizeof
from ctypes import c_int, c_void_p, POINTER
from ctypes.wintypes import *
from enum import Enum
import ctypes
import base64


config = ConfigParser()
config.read(os.path.join(Path(__file__).parent.parent.resolve(),'config.ini'))
enableSpotifyPlugin = config.getboolean('General', 'enableSpotifyPlugin')
bindIp = config.get('WsServer', 'bindIp')
bindPort = config.get('WsServer', 'bindPort')
#blacklistLocation = config.get('WsServer', 'blacklistLocation')
blacklist = config.get('WsServer', 'blacklist').lower().split("\n")
print(blacklist)


BI_RGB = 0
DIB_RGB_COLORS = 0

class ICONINFO(ctypes.Structure):
    _fields_ = [
        ("fIcon", BOOL),
        ("xHotspot", DWORD),
        ("yHotspot", DWORD),
        ("hbmMask", HBITMAP),
        ("hbmColor", HBITMAP)
    ]

class RGBQUAD(ctypes.Structure):
    _fields_ = [
        ("rgbBlue", BYTE),
        ("rgbGreen", BYTE),
        ("rgbRed", BYTE),
        ("rgbReserved", BYTE),
    ]

class BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [
        ("biSize", DWORD),
        ("biWidth", LONG),
        ("biHeight", LONG),
        ("biPlanes", WORD),
        ("biBitCount", WORD),
        ("biCompression", DWORD),
        ("biSizeImage", DWORD),
        ("biXPelsPerMeter", LONG),
        ("biYPelsPerMeter", LONG),
        ("biClrUsed", DWORD),
        ("biClrImportant", DWORD)
    ]

class BITMAPINFO(ctypes.Structure):
    _fields_ = [
        ("bmiHeader", BITMAPINFOHEADER),
        ("bmiColors", RGBQUAD * 1),
    ]


shell32 = ctypes.WinDLL("shell32", use_last_error=True)
user32 = ctypes.WinDLL("user32", use_last_error=True)
gdi32 = ctypes.WinDLL("gdi32", use_last_error=True)

gdi32.CreateCompatibleDC.argtypes = [HDC]
gdi32.CreateCompatibleDC.restype = HDC
gdi32.GetDIBits.argtypes = [
    HDC, HBITMAP, UINT, UINT, LPVOID, c_void_p, UINT
]
gdi32.GetDIBits.restype = c_int
gdi32.DeleteObject.argtypes = [HGDIOBJ]
gdi32.DeleteObject.restype = BOOL
shell32.ExtractIconExW.argtypes = [
    LPCWSTR, c_int, POINTER(HICON), POINTER(HICON), UINT
]
shell32.ExtractIconExW.restype = UINT
user32.GetIconInfo.argtypes = [HICON, POINTER(ICONINFO)]
user32.GetIconInfo.restype = BOOL
user32.DestroyIcon.argtypes = [HICON]
user32.DestroyIcon.restype = BOOL


class IconSize(Enum):
    SMALL = 1
    LARGE = 2

    @staticmethod
    def to_wh(size: "IconSize") -> tuple[int, int]:
        """
        Return the actual (width, height) values for the specified icon size.
        """
        size_table = {
            IconSize.SMALL: (16, 16),
            IconSize.LARGE: (32, 32)
        }
        return size_table[size]

def extract_icon(filename: str, size: IconSize) -> Array[c_char]:
    """
    Extract the icon from the specified `filename`, which might be
    either an executable or an `.ico` file.
    """
    dc: HDC = gdi32.CreateCompatibleDC(0)
    if dc == 0:
        raise ctypes.WinError()

    hicon: HICON = HICON()
    extracted_icons: UINT = shell32.ExtractIconExW(
        filename,
        0,
        byref(hicon) if size == IconSize.LARGE else None,
        byref(hicon) if size == IconSize.SMALL else None,
        1
    )
    if extracted_icons != 1:
        raise ctypes.WinError()
    def cleanup() -> None:
        if icon_info.hbmColor != 0:
            gdi32.DeleteObject(icon_info.hbmColor)
        if icon_info.hbmMask != 0:
            gdi32.DeleteObject(icon_info.hbmMask)
        user32.DestroyIcon(hicon)

    icon_info: ICONINFO = ICONINFO(0, 0, 0, 0, 0)
    if not user32.GetIconInfo(hicon, byref(icon_info)):
        cleanup()
        raise ctypes.WinError()

    w, h = IconSize.to_wh(size)
    bmi: BITMAPINFO = BITMAPINFO()
    memset(byref(bmi), 0, sizeof(bmi))
    bmi.bmiHeader.biSize = sizeof(BITMAPINFOHEADER)
    bmi.bmiHeader.biWidth = w
    bmi.bmiHeader.biHeight = -h
    bmi.bmiHeader.biPlanes = 1
    bmi.bmiHeader.biBitCount = 32
    bmi.bmiHeader.biCompression = BI_RGB
    bmi.bmiHeader.biSizeImage = w * h * 4
    bits = ctypes.create_string_buffer(bmi.bmiHeader.biSizeImage)
    copied_lines = gdi32.GetDIBits(
        dc, icon_info.hbmColor, 0, h, bits, byref(bmi), DIB_RGB_COLORS
    )
    if copied_lines == 0:
        cleanup()
        raise ctypes.WinError()

    cleanup()
    return bits



if enableSpotifyPlugin:
    from spotipy.oauth2 import SpotifyClientCredentials
    from spotipy.oauth2 import SpotifyOAuth
    client_credentials_manager=SpotifyClientCredentials()
    SPOTIPY_CLIENT_ID = client_credentials_manager.client_id
    SPOTIPY_CLIENT_SECRET = client_credentials_manager.client_secret
    SPOTIPY_REDIRECT_URI = "http://localhost:8080/callback"
    SCOPE = 'user-read-currently-playing user-library-modify user-library-read'

    spotify = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=SPOTIPY_CLIENT_ID,
    client_secret=SPOTIPY_CLIENT_SECRET,
    redirect_uri=SPOTIPY_REDIRECT_URI,
    scope=SCOPE))


connection = None
volumeMixer = []
globalSessions = None
#blacklist = None
lastReceivedClient = None
lastReceivedClientTime= None
lastTrack = None
isLiked = False
def initMixer():
    global volumeMixer
    global globalSessions
    #global blacklist
    globalSessions = MyAudioUtilities.getCombinedAudioSessions()
    for session in globalSessions:
        if session.Process:
            proc = {}
            proc["name"] = session.Process.name()
            proc["volume"] = round(session.SimpleAudioVolume.GetMasterVolume(), 3)
            proc["interface"] = session.SimpleAudioVolume
            proc["pid"] = session.Process.pid
            try:
                blacklist.index(session.Process.name().lower())
            except:
                volumeMixer.append(proc)

    seenTitles = []
    newMixer = []
    for proc in volumeMixer:
        if proc["name"] not in seenTitles:
            seenTitles.append(proc["name"])
            newMixer.append(proc)

    volumeMixer = newMixer

def updateMixer():
    global volumeMixer
    global globalSessions
    global blacklist

    globalSessions = MyAudioUtilities.getCombinedAudioSessions()

    removed = False
    added = False
    changed = False

    # check for removed entries
    for process in volumeMixer:
        present = False
        for session in globalSessions:
            if session.Process:
                if process["name"] == session.Process.name():
                    present = True
        if not present:
            volumeMixer.remove(process)
            removed = True

    # check for not present entries
    for session in globalSessions:
        if session.Process:
            proc = {"name": session.Process.name(),
                    "volume": round(session.SimpleAudioVolume.GetMasterVolume(), 3),
                    "interface": session.SimpleAudioVolume,
                    "pid":session.Process.pid
                    }
            try:
                blacklist.index(session.Process.name().lower())
            except:
                present = False
                for processIndex in range(len(volumeMixer)):
                    if volumeMixer[processIndex]["name"] == session.Process.name():

                        #check if the volume changed on windows side (or in this version anywhere. triggers updates to all clients)
                        #the update method filters the last client out if its sent an update in the past second
                        if volumeMixer[processIndex]["volume"]!=proc["volume"]:
                            changed = True

                        volumeMixer[processIndex] = proc;
                        present = True
                if not present:
                    volumeMixer.append(proc)
                    added = True

    if removed or added or changed:
        return True
    else:
        return False
    

# Define a list to store connected clients
connected_clients = []

async def handle_client(websocket, path):
    updateMixer()
    # Add the client to the list of connected clients
    connected_clients.append(websocket)
    print("added",websocket)
    global volumeMixer
    global connection
    global globalSessions
    global lastReceivedClient
    global lastReceivedClientTime
    try:
        while True:
            # Continuously listen for data from the client
            text = await websocket.recv()
            try:
                received = json.loads(text)
                if received["type"] == "volume":
                    updateVolume(websocket,received)
                elif received["type"] == "likeSong":
                    if enableSpotifyPlugin:
                        toggleCurrentlyPlayingLikedStatus(received)
            except Exception as e:
                print("exception on:",text, "("+str(e)+")")
                print()


    except websockets.exceptions.ConnectionClosed:
        # Remove the client from the list of connected clients if the connection is closed
        connected_clients.remove(websocket)

def toggleCurrentlyPlayingLikedStatus(received):
    try:
        current_track = spotify.current_user_playing_track()
        if current_track is None:
            print("No track is currently playing.")
        else:
            track_name = current_track['item']['name']
            artists = ", ".join([artist['name'] for artist in current_track['item']['artists']])
            print(f"Currently playing: {track_name} by {artists}")
            track_id = current_track['item']['id']
            
            track_saved = spotify.current_user_saved_tracks_contains(tracks=[track_id])[0]
            if track_saved:
                spotify.current_user_saved_tracks_delete(tracks=[track_id])
                print("Removed currently playing track from your library.")
            else:
                spotify.current_user_saved_tracks_add(tracks=[track_id])
                print("Added currently playing track to your library.")

    except Exception as e:
        print(f"Error occurred: {e}")

def updateVolume(websocket,newProcess):
    global lastReceivedClient
    global lastReceivedClientTime
    #this method is only executed when receiving volume updates
    #therefore these variables should always hold the last client and time
    lastReceivedClient = websocket
    lastReceivedClientTime=round(time.time() * 1000)

    # go through all sessions
    found = False
    for session in globalSessions:
        if session.Process:
            if session.Process.name() == newProcess["name"]:
                session.SimpleAudioVolume.SetMasterVolume((newProcess["volume"]), None)
                found = True

    if not found:
        print("couldnt find"+"received" + json.dumps(newProcess) + " in:")
        for session in globalSessions:
            if session.Process:
                print(session.Process.name())

# Send data updates to connected clients every second
async def send_data_updates():
    global lastReceivedClient
    global lastReceivedClientTime
    global lastTrack
    global isLiked
    while True:
        await asyncio.sleep(2)  # Delay for 1 second
        current_track = None
        if enableSpotifyPlugin:
            try:
                current_track = spotify.current_user_playing_track()
            except:
                continue
        
            track_info = None
            if current_track is not None and 'item' in current_track:
                track_info = current_track['item']

            if current_track != lastTrack and current_track is not None and 'item' in current_track:
                lastTrack = current_track
                try:
                    if (spotify.current_user_saved_tracks_contains(tracks=[track_info['id']])[0]):
                        isLiked = True
                    else:
                        isLiked = False
                except:
                    continue

        
            for client in connected_clients:
                if current_track is not None:
                    cover_art_url = track_info['album']['images'][0]['url']

                    song = {}
                    song["type"]="songUpdate"
                    song["url"] = cover_art_url
                    song["trackName"] = track_info['name']
                    song["artist"] = ", ".join([artist['name'] for artist in track_info['artists']])
                    song["trackLength"] = track_info['duration_ms']
                    song["trackPlayed"] = current_track['progress_ms']
                    song["isLiked"] = isLiked

                    await client.send(json.dumps(song))
            
        global volumeMixer
        global connection
        # Send data updates back to the connected clients
        for client in connected_clients:

            #skip the update sending for the one it last came from
            #to prevent rebuilding the list on clientside while still changing volume
            if client == lastReceivedClient:
                if round(time.time() * 1000)-lastReceivedClientTime<1000:
                    continue
            try:
                client.sentBefore
            except:
                client.sentBefore = False
                
            if not updateMixer() and client.sentBefore:
                continue
            
            processDictNew = []
            for process in volumeMixer:
                listProcess = {}
                listProcess["name"] = process["name"]
                listProcess["volume"] = process["volume"]
                listProcess["id"] = len(processDictNew) + 1
                listProcess["muted"] = 0
                
                icon_size = IconSize.LARGE
                w, h = IconSize.to_wh(icon_size)
                #saveImage(psutil.Process(session.Process.pid).exe(),session.Process.name()+".png")
                #session.Process.pid
                try:
                    bytess = extract_icon(psutil.Process(process["pid"]).exe(), icon_size)
                    byts = bytes(bytess)
                    listProcess["iconBytes"] = base64.b64encode(byts).decode('utf-8')
                except:
                    print(process["name"])
                    listProcess["iconBytes"] = ""

                processDictNew.append(listProcess)
            
                update = {}
                update["type"]="mixerUpdate"
                update["procs"]=processDictNew
            client.sentBefore = True
            await client.send(json.dumps(update))

async def run_server():
    # global blacklist
    # try:
    #     blacklist = open(blacklistLocation, "r").read().lower()
    # except Exception as e:
    #     print(str(e))

    initMixer()
        
    # Start the WebSocket server

    async with websockets.serve(handle_client, bindIp, bindPort):
        print("WebSocket server started")
        asyncio.create_task(send_data_updates())  # Start the task to send data updates
        await asyncio.Future()  # Keep the server running

asyncio.run(run_server())