import comtypes
from pycaw.pycaw import AudioSession
from pycaw.constants import CLSID_MMDeviceEnumerator
from pycaw.pycaw import AudioUtilities, IMMDeviceEnumerator, EDataFlow, ERole
from pycaw.pycaw import IAudioSessionControl2, IAudioSessionManager2

class MyAudioUtilities(AudioUtilities):
    mixer_output = None
    @staticmethod
    def GetSpeaker(id=None):
        device_enumerator = comtypes.CoCreateInstance(
            CLSID_MMDeviceEnumerator,
            IMMDeviceEnumerator,
            comtypes.CLSCTX_INPROC_SERVER)
        if id is not None:
            speakers = device_enumerator.GetDevice(id)
        else:
            speakers = device_enumerator.GetDefaultAudioEndpoint(EDataFlow.eRender.value, ERole.eMultimedia.value)
        return speakers

    @staticmethod
    def GetAudioSessionManager(test=None):
        speakers = MyAudioUtilities.GetSpeaker(test)
        if speakers is None:
            return None
        # win7+ only
        o = speakers.Activate(
            IAudioSessionManager2._iid_, comtypes.CLSCTX_ALL, None)
        mgr = o.QueryInterface(IAudioSessionManager2)
        return mgr

    @staticmethod
    def GetAllSessions(test=None):
        audio_sessions = []
        mgr = MyAudioUtilities.GetAudioSessionManager(test)
        if mgr is None:
            return audio_sessions
        sessionEnumerator = mgr.GetSessionEnumerator()
        count = sessionEnumerator.GetCount()
        for i in range(count):
            ctl = sessionEnumerator.GetSession(i)
            if ctl is None:
                continue
            ctl2 = ctl.QueryInterface(IAudioSessionControl2)
            if ctl2 is not None:
                audio_session = AudioSession(ctl2)
                audio_sessions.append(audio_session)
        return audio_sessions

    @staticmethod
    def getCombinedAudioSessions():
        if not MyAudioUtilities.mixer_output:
            devicelist = AudioUtilities.GetAllDevices()
            for device in devicelist:
                if "AudioDevice: VoiceMeeter Aux Input (VB-Audio VoiceMeeter AUX VAIO)" == str(device):
                    MyAudioUtilities.mixer_output = device
        return MyAudioUtilities.GetAllSessions()+MyAudioUtilities.GetAllSessions(MyAudioUtilities.mixer_output.id)