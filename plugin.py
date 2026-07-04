from Plugins.Plugin import PluginDescriptor
from Screens.Screen import Screen
from Components.Label import Label
from Components.ActionMap import ActionMap
from Components.Button import Button
from Screens.MessageBox import MessageBox
from Components.MenuList import MenuList
from Tools.BoundFunction import boundFunction
from GlobalActions import globalActionMap
try:
    from keymapparser import readKeymap
except:
    from Components.ActionMap import loadKeymap as readKeymap
from Components.Sources.StaticText import StaticText
from Components.config import (
    config, ConfigSelectionNumber, getConfigListEntry, ConfigSelection, 
    ConfigYesNo, ConfigInteger, ConfigSubsection, ConfigText, configfile, 
    NoSave
)
from Components.ConfigList import ConfigListScreen
from Tools.Directories import resolveFilename, SCOPE_PLUGINS
from enigma import eConsoleAppContainer, getDesktop, eListboxPythonMultiContent, gFont, RT_HALIGN_LEFT, RT_VALIGN_CENTER, RT_WRAP
from enigma import iPlayableService, eTimer, loadPNG
from Components.ServiceEventTracker import ServiceEventTracker
from Components.MultiContent import MultiContentEntryText, MultiContentEntryPixmapAlphaTest
from Tools.Directories import fileExists
try:
    from enigma import eAlsaOutput
    HAVE_EALSA = True
except ImportError:
    HAVE_EALSA = False
from Plugins.Extensions.IPAudio.Console2 import Console2
import os
import json
import subprocess
import signal
from datetime import datetime
from .skin import *
from sys import version_info
from collections import OrderedDict

PY3 = version_info[0] == 3

if PY3:
    unichr = chr
else:
    unichr = unichr

MAXDELAY = 200

config.plugins.IPAudio = ConfigSubsection()
config.plugins.IPAudio.currentService = ConfigText()
config.plugins.IPAudio.player = ConfigSelection(default="gst1.0-ipaudio", choices=[
                ("gst1.0-ipaudio", _("Gstreamer")),
                ("ff-ipaudio", _("FFmpeg")),
            ])
config.plugins.IPAudio.sync = ConfigSelection(default="alsasink", choices=[
                ("alsasink", _("alsasink")),
                ("osssink", _("osssink")),
                ("autoaudiosink", _("autoaudiosink")),
            ])
config.plugins.IPAudio.skin = ConfigSelection(default="orange", choices=[
    ("orange", _("Orange")),
    ("teal", _("Teal")),
    ("lime", _("Lime"))
])
config.plugins.IPAudio.update = ConfigYesNo(default=True)
config.plugins.IPAudio.mainmenu = ConfigYesNo(default=False)
config.plugins.IPAudio.keepaudio = ConfigYesNo(default=False)
config.plugins.IPAudio.volLevel = ConfigSelectionNumber(default=50, stepwidth=1, min=1, max=100, wraparound=True)
config.plugins.IPAudio.audioDelay = ConfigInteger(default=0, limits=(-10, 60))
config.plugins.IPAudio.tsDelay = ConfigInteger(default=5, limits=(0, 300))
config.plugins.IPAudio.delay = NoSave(ConfigInteger(default=5, limits=(0, 300)))
config.plugins.IPAudio.playlist = ConfigSelection(choices=[("1", _("Press OK"))], default="1")
config.plugins.IPAudio.running = ConfigYesNo(default=False)
config.plugins.IPAudio.lastidx = ConfigText()
config.plugins.IPAudio.lastplayed = NoSave(ConfigText())
config.plugins.IPAudio.lastAudioChannel = ConfigText(default="")
config.plugins.IPAudio.equalizer = ConfigSelection(default="off", choices=[
    ("off", _("Off")),
    ("bass_boost", _("Bass Boost")),
    ("treble_boost", _("Treble Boost")),
    ("vocal", _("Vocal Enhance")),
    ("rock", _("Rock")),
    ("pop", _("Pop")),
    ("classical", _("Classical")),
    ("jazz", _("Jazz")),
])
config.plugins.IPAudio.piconPath = ConfigSelection(default="/usr/lib/enigma2/python/Plugins/Extensions/IPAudio/picons/", choices=[
    ("/usr/share/enigma2/ipaudio/picon/", _("/usr/share/enigma2/ipaudio/picon/")),
    ("/media/hdd/ipaudio/ipaudio/picon/", _("/media/hdd/ipaudio/picon/")),
    ("/media/usb/ipaudio/ipudio/picon/", _("/media/usb/ipaudio/picon/")),
    ("/media/mmc/ipaudio/picon/", _("/media/mmc/ipaudio/picon/")),
    ("/media/sdcard/ipaudio/picon/", _("/media/sdcard/ipaaudio/picon/")),
    ("/media/sda1/ipaudio/picon/", _("/media/sda1/ipaudio/picon/")),
    ("/etc/enigma2/ipaudio/picon/", _("/etc/enigma2/ipaudio/picon/")),
    ("/usr/lib/enigma2/python/Plugins/Extensions/IPAudio/picons/", _("Plugin Folder"))
])
config.plugins.IPAudio.settingsPath = ConfigSelection(default="/etc/enigma2/ipaudio/", choices=[
    ("/etc/enigma2/ipaudio/", _("/etc/enigma2/ipaudio/")),
    ("/media/hdd/ipaudio/", _("/media/hdd/ipaudio/")),
    ("/media/usb/ipaudio/", _("/media/usb/ipaudio/")),
    ("/media/mmc/ipaudio/", _("/media/mmc/ipaudio/")),
    ("/media/sdcard/ipaudio/", _("/media/sdcard/ipaudio/")),
    ("/media/sda1/ipaudio/", _("/media/sda1/ipaudio/")),
    ("/usr/lib/enigma2/python/Plugins/Extensions/IPAudio/settings/", _("Plugin Folder"))
])

def validateConfigValues():
    try:
        if config.plugins.IPAudio.tsDelay.value is None:
            config.plugins.IPAudio.tsDelay.value = 5
        else:
            config.plugins.IPAudio.tsDelay.value = int(config.plugins.IPAudio.tsDelay.value)
        config.plugins.IPAudio.tsDelay.save()
    
    except (ValueError, TypeError):
        config.plugins.IPAudio.tsDelay.value = 5
        config.plugins.IPAudio.tsDelay.save()
    
    try:
        if config.plugins.IPAudio.audioDelay.value is None:
            config.plugins.IPAudio.audioDelay.value = 0
        else:
            config.plugins.IPAudio.audioDelay.value = int(config.plugins.IPAudio.audioDelay.value)
        config.plugins.IPAudio.audioDelay.save()
    
    except (ValueError, TypeError):
        config.plugins.IPAudio.audioDelay.value = 0
        config.plugins.IPAudio.audioDelay.save()
    
    try:
        if config.plugins.IPAudio.volLevel.value is None:
            config.plugins.IPAudio.volLevel.value = 50
        else:
            config.plugins.IPAudio.volLevel.value = int(config.plugins.IPAudio.volLevel.value)
        config.plugins.IPAudio.volLevel.save()
    
    except (ValueError, TypeError):
        config.plugins.IPAudio.volLevel.value = 50
        config.plugins.IPAudio.volLevel.save()

validateConfigValues()

def cprint(text):
    try:
        if PY3:
            print('\033[31m' + text + '\033[m')
        else:
            print('\033[31m' + text + '\033[m')
    except:
        print(text)

def trace_error():
    import sys
    import traceback
    try:
        traceback.print_exc(file=sys.stdout)
        if PY3:
            traceback.print_exc(file=open('/tmp/IPAudio.log', 'a', encoding='utf-8'))
        else:
            traceback.print_exc(file=open('/tmp/IPAudio.log', 'a'))
    except:
        pass

def getPlaylistDir():
    path = config.plugins.IPAudio.settingsPath.value
    if not os.path.exists(path):
        try:
            os.makedirs(path)
        except:
            pass
    return path

def getPlaylistFiles():
    import glob
    
    playlist_dir = getPlaylistDir()
    
    if not os.path.exists(playlist_dir):
        try:
            os.makedirs(playlist_dir)
        except:
            pass
    
    playlist_files = glob.glob(playlist_dir + 'ipaudio_*.json')
    playlists = []
    for filepath in sorted(playlist_files):
        filename = os.path.basename(filepath)
        category = filename.replace('ipaudio_', '').replace('.json', '')
        category = category.capitalize()
        playlists.append({'name': category, 'file': filepath})
    
    return playlists

def getPlaylist(category_file=None):
    if category_file is None:
        category_file = os.path.join(config.plugins.IPAudio.settingsPath.value, 'ipaudio.json')
    
    if fileExists(category_file):
        try:
            if PY3:
                with open(category_file, 'r', encoding='utf-8') as f:
                    return json.loads(f.read())
            else:
                with open(category_file, 'r') as f:
                    return json.loads(f.read())
        except (ValueError, Exception) as e:
            cprint("[IPAudio] Error loading playlist: {}".format(str(e)))
            trace_error()
    return None

def getversioninfo():
    import os
    currversion = "1.0"
    versionfile = "/usr/lib/enigma2/python/Plugins/Extensions/IPAudio/version"
    
    if os.path.exists(versionfile):
        try:
            if PY3:
                with open(versionfile, 'r', encoding='utf-8') as fp:
                    for line in fp.readlines():
                        if 'version=' in line:
                            currversion = line.split('=')[1].strip()
                            break
            else:
                with open(versionfile, 'r') as fp:
                    for line in fp.readlines():
                        if 'version=' in line:
                            currversion = line.split('=')[1].strip()
                            break
        except:
            pass
    
    return currversion

Ver = getversioninfo()

def getPiconPath(serviceName):
    picon_paths = [
        config.plugins.IPAudio.piconPath.value,
        '/usr/lib/enigma2/python/Plugins/Extensions/IPAudio/picons/'
    ]
    
    clean_name = serviceName.lower().replace(' ', '_').replace('+', 'plus')
    clean_name = ''.join(c for c in clean_name if c.isalnum() or c == '_')
    
    for path in picon_paths:
        if os.path.exists(path):
            picon_file = os.path.join(path, clean_name + '.png')
            if os.path.exists(picon_file):
                return picon_file
            
            try:
                for filename in os.listdir(path):
                    if clean_name in filename.lower() and filename.endswith('.png'):
                        return os.path.join(path, filename)
            except:
                pass
    
    default_picon = '/usr/lib/enigma2/python/Plugins/Extensions/IPAudio/default_picon.png'
    if os.path.exists(default_picon):
        return default_picon
    
    return None

def getVideoDelayFile():
    return os.path.join(config.plugins.IPAudio.settingsPath.value, 'video_delay_channels.json')

def loadVideoDelayData():
    videodelayfile = getVideoDelayFile()
    settings_dir = config.plugins.IPAudio.settingsPath.value
    
    if not os.path.exists(settings_dir):
        try:
            os.makedirs(settings_dir)
        except:
            pass
    
    if fileExists(videodelayfile):
        try:
            if PY3:
                with open(videodelayfile, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                with open(videodelayfile, 'r') as f:
                    return json.load(f)
        except:
            trace_error()
    return {}

def saveVideoDelayData(data):
    videodelayfile = getVideoDelayFile()
    settings_dir = config.plugins.IPAudio.settingsPath.value
    
    try:
        if not os.path.exists(settings_dir):
            os.makedirs(settings_dir)
        if PY3:
            with open(videodelayfile, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4)
        else:
            with open(videodelayfile, 'w') as f:
                json.dump(data, f, indent=4)
        return True
    except:
        trace_error()
    return False

def getVideoDelayForChannel(service_ref, fallback=None):
    if not service_ref:
        return fallback if fallback is not None else 5
    
    ref_str = service_ref.toString()
    data = loadVideoDelayData()
    
    if ref_str in data:
        delay_value = data[ref_str]
        if delay_value is not None and isinstance(delay_value, (int, float)):
            cprint("[IPAudio] Found saved video delay for channel: {} = {}".format(ref_str, delay_value))
            return int(delay_value)
    
    if fallback is not None:
        cprint("[IPAudio] No saved delay for channel, using fallback: {}".format(fallback))
        return fallback
    
    return 5

def saveVideoDelayForChannel(service_ref, delay_value):
    if not service_ref:
        return False
    
    ref_str = service_ref.toString()
    data = loadVideoDelayData()
    data[ref_str] = delay_value
    
    if saveVideoDelayData(data):
        cprint("[IPAudio] Saved video delay for channel: {} = {}".format(ref_str, delay_value))
        return True
    
    return False

def getAudioBitrate(url):
    try:
        cmd = [
            'ffprobe',
            '-v', 'error',
            '-select_streams', 'a:0',
            '-show_entries', 'stream=bit_rate',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            url
        ]
        
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=5
        )
        
        if result.returncode == 0:
            bitrate_bps = result.stdout.decode('utf-8').strip()
            if bitrate_bps and bitrate_bps != 'N/A':
                bitrate_kbps = int(bitrate_bps) // 1000
                return bitrate_kbps
        
        cmd_format = [
            'ffprobe',
            '-v', 'error',
            '-show_entries', 'format=bit_rate',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            url
        ]
        
        result = subprocess.run(
            cmd_format,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=5
        )
        
        if result.returncode == 0:
            bitrate_bps = result.stdout.decode('utf-8').strip()
            if bitrate_bps and bitrate_bps != 'N/A':
                bitrate_kbps = int(bitrate_bps) // 1000
                return bitrate_kbps
        
    except Exception as e:
        cprint("[IPAudio] Error getting bitrate: {}".format(str(e)))
    
    return None

def isMutable():
    if fileExists('/proc/stb/info/boxtype') and open('/proc/stb/info/boxtype').read().strip() in ('sf8008', 'sf8008m', 'viper4kv20', 'beyonwizv2', 'ustym4kpro', 'gbtrio4k', 'spider-x',):
        return True
    else:
        return False

def getDesktopSize():
    s = getDesktop(0).size()
    return (s.width(), s.height())

def isHD():
    desktopSize = getDesktopSize()
    return desktopSize[0] == 1280

class IPAudioSetup(Screen, ConfigListScreen):
    def __init__(self, session):
        Screen.__init__(self, session)
        self.currentSkin = config.plugins.IPAudio.skin.value
        
        if isHD():
            if config.plugins.IPAudio.skin.value == 'orange':
                self.skin = SKIN_IPAudioSetup_ORANGE_HD
            elif config.plugins.IPAudio.skin.value == 'teal':
                self.skin = SKIN_IPAudioSetup_TEAL_HD
            elif config.plugins.IPAudio.skin.value == 'lime':
                self.skin = SKIN_IPAudioSetup_LIME_HD
            else:
                self.skin = SKIN_IPAudioSetup_ORANGE_HD
        else:
            if config.plugins.IPAudio.skin.value == 'orange':
                self.skin = SKIN_IPAudioSetup_ORANGE_FHD
            elif config.plugins.IPAudio.skin.value == 'teal':
                self.skin = SKIN_IPAudioSetup_TEAL_FHD
            elif config.plugins.IPAudio.skin.value == 'lime':
                self.skin = SKIN_IPAudioSetup_LIME_FHD
            else:
                self.skin = SKIN_IPAudioSetup_ORANGE_FHD
        
        self.skinName = "IPAudioSetup"
        self.onChangedEntry = []
        self.list = []
        ConfigListScreen.__init__(self, self.list, session=session, on_change=self.changedEntry)
        self["actions"] = ActionMap(["SetupActions"],
            {
                "cancel": self.keyCancel,
                "save": self.apply,
                "ok": self.apply,
            }, -2)
        self["key_green"] = StaticText(_("Save"))
        self["key_red"] = StaticText(_("Cancel"))
        self.configChanged = False
        self.createSetup()

    def createSetup(self):
        self.list = [getConfigListEntry(_("Player"), config.plugins.IPAudio.player)]
        if config.plugins.IPAudio.player.value == "gst1.0-ipaudio":
            self.list.append(getConfigListEntry(_("Sync Audio using"), config.plugins.IPAudio.sync))
            self.list.append(getConfigListEntry(_("Audio Equalizer"), config.plugins.IPAudio.equalizer))
        self.list.append(getConfigListEntry(_("External links volume level"), config.plugins.IPAudio.volLevel))
        self.list.append(getConfigListEntry(_("Keep original channel audio"), config.plugins.IPAudio.keepaudio))
        self.list.append(getConfigListEntry(_("Video Delay"), config.plugins.IPAudio.tsDelay))
        self.list.append(getConfigListEntry(_("Audio Delay"), config.plugins.IPAudio.audioDelay))
        self.list.append(getConfigListEntry(_("Picons Folder"), config.plugins.IPAudio.piconPath))
        self.list.append(getConfigListEntry(_("Settings Folder"), config.plugins.IPAudio.settingsPath))
        self.list.append(getConfigListEntry(_("Remove/Reset Playlist"), config.plugins.IPAudio.playlist))
        self.list.append(getConfigListEntry(_("Enable/Disable online update"), config.plugins.IPAudio.update))
        self.list.append(getConfigListEntry(_("Show IPAudio in main menu"), config.plugins.IPAudio.mainmenu))
        self.list.append(getConfigListEntry(_("Select Your IPAudio Skin"), config.plugins.IPAudio.skin))
        self["config"].list = self.list
        self["config"].setList(self.list)

    def apply(self):
        current = self["config"].getCurrent()
        if current[1] == config.plugins.IPAudio.playlist:
            self.session.open(IPAudioPlaylist)
        else:
            old_picon_path = config.plugins.IPAudio.piconPath.value
            old_settings_path = config.plugins.IPAudio.settingsPath.value
            
            for x in self["config"].list:
                if len(x) > 1:
                    x[1].save()
            configfile.save()
            
            new_settings_path = config.plugins.IPAudio.settingsPath.value
            new_picon_path = config.plugins.IPAudio.piconPath.value
            
            if not os.path.exists(new_settings_path):
                try:
                    os.makedirs(new_settings_path)
                    self.session.open(MessageBox, _("Settings folder created: {}".format(new_settings_path)), MessageBox.TYPE_INFO, timeout=3)
                except:
                    self.session.open(MessageBox, _("Failed to create settings folder: {}".format(new_settings_path)), MessageBox.TYPE_ERROR, timeout=5)
            
            if not os.path.exists(new_picon_path):
                self.session.open(MessageBox, _("Picon folder does not exist: {}\nPlease create it manually.".format(new_picon_path)), MessageBox.TYPE_WARNING, timeout=5)
            
            if self.currentSkin != config.plugins.IPAudio.skin.value:
                self.session.open(MessageBox, _("Skin changed! Please restart IPAudio plugin for changes to take effect."), MessageBox.TYPE_INFO, timeout=5)
            
            if old_settings_path != new_settings_path:
                self.session.open(MessageBox, _("Settings folder changed! Existing playlists and delays in old location will not be moved automatically."), MessageBox.TYPE_INFO, timeout=8)
            
            self.close(False)

    def keyCancel(self):
        for x in self["config"].list:
            if len(x) > 1:
                x[1].cancel()
        self.close(False)

    def changedEntry(self):
        for x in self.onChangedEntry:
            x()
        current = self["config"].getCurrent()
        if current[1] == config.plugins.IPAudio.player:
            self.createSetup()

class IPAudioScreen(Screen):
    def __init__(self, session):
        Screen.__init__(self, session)
        self.session = session
        
        if isHD():
            if config.plugins.IPAudio.skin.value == 'orange':
                self.skin = SKIN_IPAudioScreen_ORANGE_HD
            elif config.plugins.IPAudio.skin.value == 'teal':
                self.skin = SKIN_IPAudioScreen_TEAL_HD
            elif config.plugins.IPAudio.skin.value == 'lime':
                self.skin = SKIN_IPAudioScreen_LIME_HD
            else:
                self.skin = SKIN_IPAudioScreen_ORANGE_HD
        else:
            if config.plugins.IPAudio.skin.value == 'orange':
                self.skin = SKIN_IPAudioScreen_ORANGE_FHD
            elif config.plugins.IPAudio.skin.value == 'teal':
                self.skin = SKIN_IPAudioScreen_TEAL_FHD
            elif config.plugins.IPAudio.skin.value == 'lime':
                self.skin = SKIN_IPAudioScreen_LIME_FHD
            else:
                self.skin = SKIN_IPAudioScreen_ORANGE_FHD
        
        self.choices = list(self.getHosts())
        self.plIndex = 0
        self['title'] = Label()
        self['title'].setText('IPAudio v{}'.format(Ver))
        self['server'] = Label()
        self['sync'] = Label()

        current_service = self.session.nav.getCurrentlyPlayingServiceReference()
        current_delay = int(config.plugins.IPAudio.tsDelay.value)
        
        loaded_delay = getVideoDelayForChannel(current_service, fallback=current_delay)
        if loaded_delay is None:
            loaded_delay = 5
        
        config.plugins.IPAudio.tsDelay.value = loaded_delay
        self['sync'].setText('Video Delay: {}s'.format(config.plugins.IPAudio.tsDelay.value))
        
        self['audio_delay'] = Label()
        self['audio_delay'].setText('Audio Delay: {}s'.format(config.plugins.IPAudio.audioDelay.value))
        self['network_status'] = Label()
        self['network_status'].setText('')
        
        self['countdown'] = Label()
        self['countdown'].setText('')
        
        self["list"] = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
        
        if isHD():
            self["list"].l.setItemHeight(40)
            self["list"].l.setFont(0, gFont('Regular', 20))
        else:
            self["list"].l.setItemHeight(50)
            self["list"].l.setFont(0, gFont('Regular', 28))
        
        self["key_red"] = Button(_("Exit"))
        self["key_green"] = Button(_("Reset Audio"))
        self["key_yellow"] = Button(_("Help"))
        self["key_blue"] = Button(_("Info"))
        self["key_menu"] = Button(_("Menu"))
        self["IPAudioAction"] = ActionMap(["IPAudioActions", "ColorActions"],
            {
                "ok": self.ok,
                "ok_long": boundFunction(self.ok, long=True),
                "cancel": self.exit,
                "menu": self.openConfig,
                "red": self.exit,
                "green": self.resetAudio,
                "yellow": self.showHelp,
                "blue": self.showInfo,
                "right": self.right,
                "left": self.left,
                "pause": self.pause,
                "pauseAudio": self.pauseAudioProcess,
                "delayUP": self.delayUP,
                "delayDown": self.delayDown,
                "audioDelayDown": self.audioDelayDown,
                "audioDelayReset": self.audioDelayReset,
                "audioDelayUp": self.audioDelayUp,
                "clearVideoDelay": self.clearVideoDelay,
            }, -1)
        
        self.alsa = None
        self.audioPaused = False
        self.audio_process = None
        self.radioList = []
        self.guide = dict()

        self.currentDelaySeconds = 0
        self.targetDelaySeconds = 0
        self.countdownValue = 0
        self.currentBitrate = None
        self.bitrateCheckTimer = eTimer()
        try:
            self.bitrateCheckTimer.callback.append(self.checkAudioBitrate)
        except:
            self.bitrateCheckTimer_conn = self.bitrateCheckTimer.timeout.connect(self.checkAudioBitrate)
        
        if HAVE_EALSA:
            self.alsa = eAlsaOutput.getInstance()
        
        self.timeShiftTimer = eTimer()
        self.guideTimer = eTimer()
        self.statusTimer = eTimer()
        self.countdownTimer = eTimer()
        
        try:
            self.timeShiftTimer.callback.append(self.unpauseService)
            self.guideTimer.callback.append(self.getGuide)
            self.statusTimer.callback.append(self.checkNetworkStatus)
            self.countdownTimer.callback.append(self.updateCountdown)
        except:
            self.timeShiftTimer_conn = self.timeShiftTimer.timeout.connect(self.unpauseService)
            self.guideTimer_conn = self.guideTimer.timeout.connect(self.getGuide)
            self.statusTimer_conn = self.statusTimer.timeout.connect(self.checkNetworkStatus)
            self.countdownTimer_conn = self.countdownTimer.timeout.connect(self.updateCountdown)
        
        self.lastservice = self.session.nav.getCurrentlyPlayingServiceReference()
        
        if config.plugins.IPAudio.update.value:
            self.checkupdates()
        
        self.onLayoutFinish.append(self.getGuide)
        self.onShown.append(self.onWindowShow)

    def updateCountdown(self):
        if self.countdownValue > 0:
            self['countdown'].setText('TimeShift: {}s'.format(self.countdownValue))
            self.countdownValue -= 1
            self.countdownTimer.start(1000, True)
        else:
            self['countdown'].setText('')
            self.countdownTimer.stop()

    def startCountdown(self, seconds):
        if seconds > 0:
            self.countdownValue = int(seconds)
            self.countdownTimer.start(100, True)
            self.updateCountdown()

    def showInfo(self):
        self.session.open(IPAudioInfo)

    def showHelp(self):
        self.session.open(IPAudioHelp)

    def checkNetworkStatus(self):
        if self.audio_process:
            if self.audio_process.poll() is None:
                if self.currentBitrate is not None:
                    network_text = unichr(9679) + ' Playing {}kb/s'.format(self.currentBitrate)
                    if PY3:
                        self['network_status'].setText(network_text)
                    else:
                        self['network_status'].setText(network_text.encode('utf-8'))
                else:
                    network_text = unichr(9679) + ' Playing'
                    if PY3:
                        self['network_status'].setText(network_text)
                    else:
                        self['network_status'].setText(network_text.encode('utf-8'))
            else:
                network_text = unichr(10007) + ' Stopped'
                if PY3:
                    self['network_status'].setText(network_text)
                else:
                    self['network_status'].setText(network_text.encode('utf-8'))
                self.audio_process = None
                self.currentBitrate = None
        else:
            self['network_status'].setText('')
            self.currentBitrate = None

    def checkAudioBitrate(self):
        if hasattr(self, 'url') and self.url and config.plugins.IPAudio.running.value:
            cprint("[IPAudio] Checking bitrate for: {}".format(self.url))
            
            bitrate = getAudioBitrate(self.url)
            
            if bitrate:
                self.currentBitrate = bitrate
                cprint("[IPAudio] Detected bitrate: {} kb/s".format(bitrate))
                if self.audio_process and self.audio_process.poll() is None:
                    network_text = unichr(9679) + ' Playing {}kb/s'.format(self.currentBitrate)
                    if PY3:
                        self['network_status'].setText(network_text)
                    else:
                        self['network_status'].setText(network_text.encode('utf-8'))
            else:
                cprint("[IPAudio] Could not detect bitrate")
                self.currentBitrate = None
        
        self.bitrateCheckTimer.stop()

    def getTimeshift(self):
        service = self.session.nav.getCurrentService()
        return service and service.timeshift()

    def pauseAudioProcess(self):
        if config.plugins.IPAudio.running.value and IPAudioHandler.container.running():
            pid = IPAudioHandler.container.getPID()
            if not self.audioPaused:
                cmd = "kill -STOP {}".format(pid)
                self.audioPaused = True
            else:
                cmd = "kill -CONT {}".format(pid)
                self.audioPaused = False
            eConsoleAppContainer().execute(cmd)

    def pause(self):
        if config.plugins.IPAudio.running.value:
            ts = self.getTimeshift()
            
            if ts is None:
                return
            
            self.targetDelaySeconds = int(config.plugins.IPAudio.tsDelay.value)
            
            if not ts.isTimeshiftEnabled():
                cprint("[IPAudio] Starting TimeShift with {}s delay".format(self.targetDelaySeconds))
                
                ts.startTimeshift()
                ts.activateTimeshift()
                
                delay_ms = int(self.targetDelaySeconds * 1000)
                self.timeShiftTimer.start(delay_ms, False)
                
                self.startCountdown(self.targetDelaySeconds)
                self.currentDelaySeconds = self.targetDelaySeconds
                
            elif ts.isTimeshiftEnabled() and not self.timeShiftTimer.isActive():
                delay_difference = self.targetDelaySeconds - self.currentDelaySeconds
                
                if abs(delay_difference) < 0.5:
                    cprint("[IPAudio] Already at target delay {}s".format(self.targetDelaySeconds))
                    return
                
                if delay_difference > 0:
                    cprint("[IPAudio] Increasing delay by {}s (from {}s to {}s)".format(
                        delay_difference, self.currentDelaySeconds, self.targetDelaySeconds))
                    
                    service = self.session.nav.getCurrentService()
                    pauseable = service.pause()
                    if pauseable:
                        pauseable.pause()
                    
                    additional_delay_ms = int(delay_difference * 1000)
                    self.timeShiftTimer.start(additional_delay_ms, False)
                    
                    self.startCountdown(delay_difference)
                    self.currentDelaySeconds = self.targetDelaySeconds
                    
                else:
                    cprint("[IPAudio] Decreasing delay to {}s (was {}s)".format(
                        self.targetDelaySeconds, self.currentDelaySeconds))
                    
                    ts.stopTimeshift()
                    ts.startTimeshift()
                    ts.activateTimeshift()
                    
                    delay_ms = int(self.targetDelaySeconds * 1000)
                    self.timeShiftTimer.start(delay_ms, False)
                    
                    self.startCountdown(self.targetDelaySeconds)
                    self.currentDelaySeconds = self.targetDelaySeconds

    def unpauseService(self):
        self.timeShiftTimer.stop()
        service = self.session.nav.getCurrentService()
        pauseable = service.pause()
        if pauseable:
            pauseable.unpause()

    def delayUP(self):
        current_value = int(config.plugins.IPAudio.tsDelay.value)
        
        if current_value < 300:
            config.plugins.IPAudio.tsDelay.value = current_value + 1
            config.plugins.IPAudio.tsDelay.save()
            
            self['sync'].setText('Video Delay: {}s'.format(config.plugins.IPAudio.tsDelay.value))
            
            current_service = self.session.nav.getCurrentlyPlayingServiceReference()
            saveVideoDelayForChannel(current_service, config.plugins.IPAudio.tsDelay.value)

    def delayDown(self):
        current_value = int(config.plugins.IPAudio.tsDelay.value)
        
        if current_value > 0:
            config.plugins.IPAudio.tsDelay.value = current_value - 1
            config.plugins.IPAudio.tsDelay.save()
            
            self['sync'].setText('Video Delay: {}s'.format(config.plugins.IPAudio.tsDelay.value))
            
            current_service = self.session.nav.getCurrentlyPlayingServiceReference()
            saveVideoDelayForChannel(current_service, config.plugins.IPAudio.tsDelay.value)

    def getHosts(self):
        hosts = resolveFilename(SCOPE_PLUGINS, "Extensions/IPAudio/hosts.json")
        self.hosts = None
        
        if fileExists(hosts):
            hosts = open(hosts, 'r').read()
            self.hosts = json.loads(hosts, object_pairs_hook=OrderedDict)
            for host in self.hosts:
                yield host
        
        custom_playlists = getPlaylistFiles()
        for playlist in custom_playlists:
            yield playlist['name']

    def onWindowShow(self):
        self.onShown.remove(self.onWindowShow)
        self.guideTimer.start(30000)
        
        current_service = self.session.nav.getCurrentlyPlayingServiceReference()
        current_delay = int(config.plugins.IPAudio.tsDelay.value)
        
        loaded_delay = getVideoDelayForChannel(current_service, fallback=current_delay)
        
        config.plugins.IPAudio.tsDelay.value = loaded_delay
        self['sync'].setText('Video Delay: {}s'.format(config.plugins.IPAudio.tsDelay.value))
        
        restored = False
        
        if config.plugins.IPAudio.lastAudioChannel.value:
            last_url = config.plugins.IPAudio.lastAudioChannel.value
            cprint("[IPAudio] Attempting to restore last audio channel: {}".format(last_url))
            
            if config.plugins.IPAudio.lastidx.value:
                try:
                    lastplaylist, lastchannel = map(int, config.plugins.IPAudio.lastidx.value.split(','))
                    self.plIndex = lastplaylist
                    self.changePlaylist()
                    
                    if len(self.radioList) > lastchannel:
                        if self.radioList[lastchannel][1] == last_url:
                            self['list'].moveToIndex(lastchannel)
                            cprint("[IPAudio] Restored to playlist {} channel {}".format(lastplaylist, lastchannel))
                            restored = True
                        else:
                            cprint("[IPAudio] Index mismatch, searching for URL in current playlist")
                            for idx, channel in enumerate(self.radioList):
                                if channel[1] == last_url:
                                    self['list'].moveToIndex(idx)
                                    cprint("[IPAudio] Found channel at index {}".format(idx))
                                    restored = True
                                    break
                except Exception as e:
                    cprint("[IPAudio] Error restoring from lastidx: {}".format(str(e)))
            
            if not restored:
                cprint("[IPAudio] Searching all playlists for last audio channel")
                found = False
                
                for playlist_idx, playlist_name in enumerate(self.choices):
                    self.plIndex = playlist_idx
                    self.changePlaylist()
                    
                    for channel_idx, channel in enumerate(self.radioList):
                        if channel[1] == last_url:
                            self['list'].moveToIndex(channel_idx)
                            cprint("[IPAudio] Found in playlist '{}' at index {}".format(playlist_name, channel_idx))
                            
                            config.plugins.IPAudio.lastidx.value = '{},{}'.format(playlist_idx, channel_idx)
                            config.plugins.IPAudio.lastidx.save()
                            
                            found = True
                            restored = True
                            break
                    
                    if found:
                        break
                
                if not restored:
                    cprint("[IPAudio] Could not find last audio channel, using first available")
        
        if not restored:
            if config.plugins.IPAudio.lastidx.value:
                try:
                    lastplaylist, lastchannel = map(int, config.plugins.IPAudio.lastidx.value.split(','))
                    self.plIndex = lastplaylist
                    self.changePlaylist()
                    self['list'].moveToIndex(lastchannel)
                    cprint("[IPAudio] Using lastidx fallback: playlist {} channel {}".format(lastplaylist, lastchannel))
                except:
                    self.setPlaylist()
            else:
                self.setPlaylist()

    def clearVideoDelay(self):
        current_service = self.session.nav.getCurrentlyPlayingServiceReference()
        if current_service:
            ref_str = current_service.toString()
            data = loadVideoDelayData()
            
            if ref_str in data:
                del data[ref_str]
                saveVideoDelayData(data)
                cprint("[IPAudio] Cleared saved delay for channel: {}".format(ref_str))
                self.session.open(MessageBox, _("Video delay cleared for this channel"), MessageBox.TYPE_INFO, timeout=3)
            else:
                self.session.open(MessageBox, _("No saved delay for this channel"), MessageBox.TYPE_INFO, timeout=3)

    def checkupdates(self):
        url = "https://raw.githubusercontent.com/popking159/ipaudioo/main/installer-ipaudio.sh"
        self.callUrl(url, self.checkVer)

    def checkVer(self, data):
        try:
            if PY3 and isinstance(data, bytes):
                data = data.decode('utf-8')
            elif not PY3:
                data = data.encode('utf-8')
            
            if data:
                lines = data.split('\n')
                self.newversion = None
                self.newdescription = ""
                
                for line in lines:
                    line = line.strip()
                    if line.startswith('version='):
                        self.newversion = line.split('=')[1].strip('"').strip("'")
                    elif line.startswith('description='):
                        self.newdescription = line.split('=')[1].strip('"').strip("'")
                
                if self.newversion:
                    cprint("[IPAudio] Current version: {}, New version: {}".format(Ver, self.newversion))
                    
                    try:
                        current = float(Ver)
                        new = float(self.newversion)
                        
                        if new > current:
                            msg = "New version {} is available.\n\n{}\n\nDo you want to install it now?".format(
                                self.newversion, 
                                self.newdescription
                            )
                            self.session.openWithCallback(
                                self.installupdate, 
                                MessageBox, 
                                msg, 
                                MessageBox.TYPE_YESNO
                            )
                    except ValueError:
                        cprint("[IPAudio] Could not compare versions")
        except Exception as e:
            cprint("[IPAudio] Error checking version: {}".format(str(e)))
            trace_error()

    def installupdate(self, answer=False):
        if answer:
            url = "https://raw.githubusercontent.com/popking159/ipaudioo/main/installer-ipaudio.sh"
            cmdlist = []
            cmdlist.append('wget -q --no-check-certificate {} -O - | bash'.format(url))
            self.session.open(
                Console2, 
                title="Update IPAudio", 
                cmdlist=cmdlist, 
                closeOnSuccess=False
            )

    def callUrl(self, url, callback):
        try:
            from twisted.web.client import getPage
            getPage(str.encode(url), headers={b'Content-Type': b'application/x-www-form-urlencoded'}).addCallback(callback).addErrback(self.addErrback)
        except:
            pass

    def getAnisUrls(self):
        url = "https://raw.githubusercontent.com/popking159/ipaudio/refs/heads/main/ipaudio_anis.json"
        self.callUrl(url, self.parseAnisData)

    def parseAnisData(self, data):
        try:
            if PY3 and isinstance(data, bytes):
                data = data.decode('utf-8')
            
            playlist_data = json.loads(data)
            list = []
            
            if 'playlist' in playlist_data:
                for channel in playlist_data['playlist']:
                    try:
                        list.append([str(channel['channel']), str(channel['url'])])
                    except KeyError:
                        pass
            
            if len(list) > 0:
                self["list"].l.setList(self.iniMenu(list))
                self["list"].show()
                self.radioList = list
            else:
                self["list"].hide()
                self.radioList = []
                self['server'].setText('Anis Sport - Playlist is empty')
        except Exception as e:
            cprint("[IPAudio] Error parsing Anis data: {}".format(str(e)))
            trace_error()
            self["list"].hide()
            self.radioList = []
            self['server'].setText('Error loading Anis Sport')

    def addErrback(self, error=None):
        pass

    def right(self):
        self.plIndex += 1
        self.changePlaylist()

    def left(self):
        self.plIndex -= 1
        self.changePlaylist()

    def changePlaylist(self):
        if self.plIndex > len(self.choices) - 1:
            self.plIndex = 0
        if self.plIndex < 0:
            self.plIndex = len(self.choices) - 1
        
        self.radioList = []
        self.setPlaylist()

    def setPlaylist(self):
        current = self.choices[self.plIndex]
        
        if current in self.hosts:
            if current in ["Anis Sport"]:
                self.getAnisUrls()
                self['server'].setText(str(current))
            else:
                list = []
                for cmd in self.hosts[current]['cmds']:
                    list.append([cmd.split('|')[0], cmd.split('|')[1]])
                list = self.checkINGuide(list)
                
                if len(list) > 0:
                    self["list"].l.setList(self.iniMenu(list))
                    self["list"].show()
                    self.radioList = list
                    self['server'].setText(str(current))
                else:
                    self["list"].hide()
                    self.radioList = []
                    self['server'].setText('Playlist is empty')
        else:
            category_lower = current.lower()
            playlist_dir = getPlaylistDir()
            playlist_file = playlist_dir + 'ipaudio_{}.json'.format(category_lower)
            
            if fileExists(playlist_file):
                playlist = getPlaylist(playlist_file)
                if playlist:
                    list = []
                    for channel in playlist['playlist']:
                        try:
                            list.append([str(channel['channel']), str(channel['url'])])
                        except KeyError:
                            pass
                    
                    if len(list) > 0:
                        self["list"].l.setList(self.iniMenu(list))
                        self["list"].show()
                        self.radioList = list
                        self['server'].setText(current)
                    else:
                        self["list"].hide()
                        self.radioList = []
                        self['server'].setText('{} - Playlist is empty'.format(current))
                else:
                    self["list"].hide()
                    self.radioList = []
                    self['server'].setText('Cannot load playlist')
            else:
                self["list"].hide()
                self.radioList = []
                self['server'].setText('Playlist file not found')

    def checkINGuide(self, entries):
        for idx, entry in enumerate(entries):
            if entry[0] in self.guide:
                if self.guide[entry[0]]['check']:
                    nowIntimestamp = datetime.now().strftime('%s')
                    entryProgEnding = self.guide[entry[0]]['end']
                    if int(entryProgEnding) >= int(nowIntimestamp):
                        entries[idx] = (self.guide[entry[0]]['prog'], entry[1])
        return entries

    def getGuide(self):
        url = 'http://ipkinstall.ath.cx/ipaudio/epg.json'
        self.callUrl(url, self.parseGuide)

    def parseGuide(self, data):
        if PY3 and isinstance(data, bytes):
            data = data.decode('utf-8')
        elif not PY3:
            data = data.encode('utf-8')
        self.guide = json.loads(data)
        if self.guide != {}:
            self.setPlaylist()

    def iniMenu(self, sList):
        res = []
        gList = []
        
        for elem in sList:
            picon_path = getPiconPath(elem[0])
            
            if isHD():
                res.append(MultiContentEntryText(
                    pos=(0, 0), 
                    size=(0, 0), 
                    font=0, 
                    flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER | RT_WRAP, 
                    text='', 
                    border_width=3
                ))
                
                if picon_path:
                    pixmap = loadPNG(picon_path)
                    if pixmap:
                        res.append(MultiContentEntryPixmapAlphaTest(
                            pos=(10, 1), 
                            size=(100, 56), 
                            png=pixmap
                        ))
                        res.append(MultiContentEntryText(
                            pos=(120, 4), 
                            size=(440, 50), 
                            font=0, 
                            backcolor_sel=None, 
                            flags=RT_VALIGN_CENTER | RT_HALIGN_LEFT, 
                            text=str(elem[0])
                        ))
                    else:
                        res.append(MultiContentEntryText(
                            pos=(5, 4), 
                            size=(560, 50), 
                            font=0, 
                            backcolor_sel=None, 
                            flags=RT_VALIGN_CENTER | RT_HALIGN_LEFT, 
                            text=str(elem[0])
                        ))
                else:
                    res.append(MultiContentEntryText(
                        pos=(5, 4), 
                        size=(560, 50), 
                        font=0, 
                        backcolor_sel=None, 
                        flags=RT_VALIGN_CENTER | RT_HALIGN_LEFT, 
                        text=str(elem[0])
                    ))
            else:
                res.append(MultiContentEntryText(
                    pos=(0, 0), 
                    size=(0, 0), 
                    font=0, 
                    flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER | RT_WRAP, 
                    text='', 
                    border_width=3
                ))
                
                if picon_path:
                    pixmap = loadPNG(picon_path)
                    if pixmap:
                        res.append(MultiContentEntryPixmapAlphaTest(
                            pos=(10, 1), 
                            size=(110, 48), 
                            png=pixmap
                        ))
                        res.append(MultiContentEntryText(
                            pos=(130, 4), 
                            size=(700, 42), 
                            font=0, 
                            backcolor_sel=None, 
                            flags=RT_VALIGN_CENTER | RT_HALIGN_LEFT, 
                            text=str(elem[0])
                        ))
                    else:
                        res.append(MultiContentEntryText(
                            pos=(5, 4), 
                            size=(830, 42), 
                            font=0, 
                            backcolor_sel=None, 
                            flags=RT_VALIGN_CENTER | RT_HALIGN_LEFT, 
                            text=str(elem[0])
                        ))
                else:
                    res.append(MultiContentEntryText(
                        pos=(5, 4), 
                        size=(830, 42), 
                        font=0, 
                        backcolor_sel=None, 
                        flags=RT_VALIGN_CENTER | RT_HALIGN_LEFT, 
                        text=str(elem[0])
                    ))
            
            gList.append(res)
            res = []
        
        return gList

    def ok(self, long=False):
        if not hasattr(self, 'radioList') or len(self.radioList) == 0:
            self.session.open(MessageBox, _("Playlist is empty! Please add channels first."), MessageBox.TYPE_INFO, timeout=5)
            return
        
        index = self['list'].getSelectionIndex()
        if index is None or index < 0 or index >= len(self.radioList):
            self.session.open(MessageBox, _("Please select a channel first."), MessageBox.TYPE_INFO, timeout=5)
            return
        
        if config.plugins.IPAudio.player.value == "gst1.0-ipaudio":
            player_check = '/usr/bin/gst-launch-1.0'
        else:
            player_check = '/usr/bin/ffmpeg'
        
        if fileExists(player_check):
            currentAudioTrack = 0
            if long:
                service = self.session.nav.getCurrentService()
                if not service.streamed():
                    currentAudioTrack = service.audioTracks().getCurrentTrack()
                self.url = 'http://127.0.0.1:8001/{}'.format(self.lastservice.toString())
                config.plugins.IPAudio.lastplayed.value = "e2_service"
            else:
                try:
                    self.url = self.radioList[index][1]
                    config.plugins.IPAudio.lastplayed.value = self.url
                    config.plugins.IPAudio.lastidx.value = '{},{}'.format(self.plIndex, index)
                    config.plugins.IPAudio.lastidx.save()
                    config.plugins.IPAudio.lastAudioChannel.value = self.url
                    config.plugins.IPAudio.lastAudioChannel.save()
                    cprint("[IPAudio] Saved last audio channel: {}".format(self.url))
                except (IndexError, KeyError) as e:
                    cprint("[IPAudio] Error accessing radioList: {}".format(str(e)))
                    self.session.open(MessageBox, _("Error selecting channel."), MessageBox.TYPE_ERROR, timeout=5)
                    return
            
            if config.plugins.IPAudio.player.value == "gst1.0-ipaudio":
                eq_filter = self.getEqualizerFilter()
                
                volume = float(config.plugins.IPAudio.volLevel.value) / 0.5
                
                sink = config.plugins.IPAudio.sync.value
                cmd = 'gst-launch-1.0 -e uridecodebin uri="{}" ! audioconvert ! audioresample ! '.format(self.url)
                
                cmd += 'volume volume={} ! '.format(volume)
                
                if eq_filter:
                    cmd += '{} ! '.format(eq_filter)
                
                delay_ms = int(config.plugins.IPAudio.audioDelay.value) * 1000
                if delay_ms != 0:
                    delay_ns = abs(delay_ms) * 1000000
                    if delay_ms > 0:
                        cmd += 'audiobuffersplit output-buffer-duration={} ! '.format(delay_ns)
                    else:
                        cmd += 'queue max-size-buffers=1 max-size-time=1000000 ! '
                
                cmd += '{} sync=false'.format(sink)
                
                cprint("[IPAudio] GStreamer command: {}".format(cmd))
                cprint("[IPAudio] Volume level: {} = {}x".format(config.plugins.IPAudio.volLevel.value, volume))
                
            else:
                delay_sec = int(config.plugins.IPAudio.audioDelay.value)
                
                volume = float(config.plugins.IPAudio.volLevel.value) / 0.5
                
                if delay_sec > 0:
                    delay_ms = delay_sec * 1000
                    cmd = 'ffmpeg -i "{}" -af "adelay={}|{},volume={}" -vn -f alsa default'.format(
                        self.url, delay_ms, delay_ms, volume)
                elif delay_sec < 0:
                    trim_sec = abs(delay_sec)
                    cmd = 'ffmpeg -ss {} -i "{}" -af "volume={}" -vn -f alsa default'.format(
                        trim_sec, self.url, volume)
                else:
                    cmd = 'ffmpeg -i "{}" -af "volume={}" -vn -f alsa default'.format(self.url, volume)
                
                if currentAudioTrack > 0:
                    cmd = cmd.replace('-i', '-i').replace('-vn', '-map 0:a:{} -vn'.format(currentAudioTrack))
                
                cprint("[IPAudio] FFmpeg command: {}".format(cmd))
                cprint("[IPAudio] Volume level: {} = {}x".format(config.plugins.IPAudio.volLevel.value, volume))

            self.runCmd(cmd)
            self.currentBitrate = None
            self.bitrateCheckTimer.start(2000, True)
        else:
            self.session.open(MessageBox, _("Cannot play url, player is missing !!"), MessageBox.TYPE_ERROR, timeout=5)

    def audioReStart(self):
        cprint("[IPAudio] audioReStart called")
        
        if self.audio_process:
            try:
                self.audio_process.kill()
                self.audio_process.wait(timeout=1)
                self.audio_process = None
            except:
                pass
        
        os.system("killall -9 gst-launch-1.0 ffmpeg 2>/dev/null")
        
        ts = self.getTimeshift()
        if ts and ts.isTimeshiftEnabled():
            ts.stopTimeshift()
        
        if self.timeShiftTimer.isActive():
            self.timeShiftTimer.stop()
        
        if fileExists('/dev/dvb/adapter0/audio10') and not isMutable():
            try:
                os.rename('/dev/dvb/adapter0/audio10', '/dev/dvb/adapter0/audio0')
            except:
                pass
            
            self.session.nav.stopService()
            self.restoreTimer = eTimer()
            try:
                self.restoreTimer.callback.append(self.restoreService)
            except:
                self.restoreTimer_conn = self.restoreTimer.timeout.connect(self.restoreService)
            self.restoreTimer.start(100, True)
        elif config.plugins.IPAudio.running.value and isMutable():
            if IPAudioHandler.container.running():
                IPAudioHandler.container.kill()
        
        config.plugins.IPAudio.running.value = False
        config.plugins.IPAudio.running.save()

    def resetAudio(self):
        cprint("[IPAudio] resetAudio called")
        
        if self.statusTimer.isActive():
            self.statusTimer.stop()
        if self.bitrateCheckTimer.isActive():
            self.bitrateCheckTimer.stop()
        
        self.currentBitrate = None
        
        if self.audio_process:
            try:
                cprint("[IPAudio] Terminating process PID: {}".format(self.audio_process.pid))
                self.audio_process.terminate()
                try:
                    self.audio_process.wait(timeout=1)
                    cprint("[IPAudio] Process terminated gracefully")
                except subprocess.TimeoutExpired:
                    cprint("[IPAudio] Process not responding, force killing")
                    self.audio_process.kill()
                    self.audio_process.wait(timeout=1)
                    cprint("[IPAudio] Process force killed")
                self.audio_process = None
            except Exception as e:
                cprint("[IPAudio] Error killing process: {}".format(str(e)))
                try:
                    os.system("killall -9 gst-launch-1.0 ffmpeg 2>/dev/null")
                except:
                    pass
                self.audio_process = None
        else:
            cprint("[IPAudio] No process tracked, killing all gst-launch and ffmpeg")
            os.system("killall -9 gst-launch-1.0 ffmpeg 2>/dev/null")
        
        if IPAudioHandler.container.running():
            IPAudioHandler.container.kill()
        
        self['network_status'].setText('')
        
        if not self.alsa:
            if fileExists('/dev/dvb/adapter0/audio10') and not isMutable():
                try:
                    os.rename('/dev/dvb/adapter0/audio10', '/dev/dvb/adapter0/audio0')
                    cprint("[IPAudio] Audio device restored")
                except:
                    pass
                
                self.session.nav.stopService()
                self.restoreTimer = eTimer()
                try:
                    self.restoreTimer.callback.append(self.restoreService)
                except:
                    self.restoreTimer_conn = self.restoreTimer.timeout.connect(self.restoreService)
                self.restoreTimer.start(100, True)
            elif isMutable():
                self.session.nav.stopService()
                self.restoreTimer = eTimer()
                try:
                    self.restoreTimer.callback.append(self.restoreService)
                except:
                    self.restoreTimer_conn = self.restoreTimer.timeout.connect(self.restoreService)
                self.restoreTimer.start(100, True)
        
        config.plugins.IPAudio.running.value = False
        config.plugins.IPAudio.running.save()

    def restoreService(self):
        cprint("[IPAudio] Restoring service")
        self.session.nav.playService(self.lastservice)

    def runCmd(self, cmd):
        cprint("[IPAudio] runCmd called with: {}".format(cmd))
        
        if self.audio_process:
            try:
                self.audio_process.terminate()
                try:
                    self.audio_process.wait(timeout=1)
                except:
                    self.audio_process.kill()
            except:
                pass
            self.audio_process = None
        
        if IPAudioHandler.container.running():
            IPAudioHandler.container.kill()
        
        if self.alsa:
            self.alsa.stop()
            self.alsa.close()
        else:
            if not config.plugins.IPAudio.keepaudio.value:
                if fileExists('/dev/dvb/adapter0/audio0') and not isMutable():
                    self.session.nav.stopService()
                    try:
                        os.rename('/dev/dvb/adapter0/audio0', '/dev/dvb/adapter0/audio10')
                    except:
                        pass
                    self.session.nav.playService(self.lastservice)
        
        try:
            cprint("[IPAudio] Executing subprocess...")
            self.audio_process = subprocess.Popen(
                cmd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            cprint("[IPAudio] Process started with PID: {}".format(self.audio_process.pid))
        except Exception as e:
            cprint("[IPAudio] ERROR starting process: {}".format(str(e)))
            trace_error()
            self.audio_process = None
        
        config.plugins.IPAudio.running.value = True
        config.plugins.IPAudio.running.save()
        if not self.statusTimer.isActive():
            self.statusTimer.start(2000)

    def audioDelayUp(self):
        current_value = int(config.plugins.IPAudio.audioDelay.value)
        
        if current_value < 60:
            config.plugins.IPAudio.audioDelay.value = current_value + 1
            config.plugins.IPAudio.audioDelay.save()
            self['audio_delay'].setText('Audio Delay: {}s'.format(config.plugins.IPAudio.audioDelay.value))
            
            if config.plugins.IPAudio.running.value:
                self.restartAudioWithDelay()

    def audioDelayDown(self):
        current_value = int(config.plugins.IPAudio.audioDelay.value)
        
        if current_value > -10:
            config.plugins.IPAudio.audioDelay.value = current_value - 1
            config.plugins.IPAudio.audioDelay.save()
            self['audio_delay'].setText('Audio Delay: {}s'.format(config.plugins.IPAudio.audioDelay.value))
            
            if config.plugins.IPAudio.running.value:
                self.restartAudioWithDelay()

    def audioDelayReset(self):
        config.plugins.IPAudio.audioDelay.value = 0
        config.plugins.IPAudio.audioDelay.save()
        self['audio_delay'].setText('Audio Delay: 0s')
        
        if config.plugins.IPAudio.running.value:
            self.restartAudioWithDelay()

    def applyAudioDelay(self):
        if hasattr(self, 'url') and self.url:
            current_url = self.url
            
            if self.audio_process:
                try:
                    self.audio_process.terminate()
                    self.audio_process.wait(timeout=1)
                except:
                    try:
                        self.audio_process.kill()
                    except:
                        pass
                self.audio_process = None
            
            self.delayRestartTimer = eTimer()
            try:
                self.delayRestartTimer.callback.append(lambda: self.restartAudioWithDelay(current_url))
            except:
                self.delayRestartTimer_conn = self.delayRestartTimer.timeout.connect(lambda: self.restartAudioWithDelay(current_url))
            self.delayRestartTimer.start(100, True)

    def restartAudioWithDelay(self):
        if hasattr(self, 'url') and self.url:
            cprint("[IPAudio] Restarting audio with new delay: {}ms".format(config.plugins.IPAudio.audioDelay.value))
            
            if self.audio_process:
                try:
                    self.audio_process.terminate()
                    self.audio_process.wait(timeout=1)
                except:
                    pass
            
            if IPAudioHandler.container.running():
                IPAudioHandler.container.kill()
            
            delay_ms = int(config.plugins.IPAudio.audioDelay.value)
            
            if config.plugins.IPAudio.player.value == "gst1.0-ipaudio":
                sink = config.plugins.IPAudio.sync.value
                cmd = 'gst-launch-1.0 -e uridecodebin uri="{}" ! audioconvert ! audioresample ! '.format(self.url)
                
                if delay_ms != 0:
                    delay_ns = abs(delay_ms) * 1000000
                    if delay_ms > 0:
                        cmd += 'audiobuffersplit output-buffer-duration={} ! '.format(delay_ns)
                    else:
                        cmd += 'queue max-size-buffers=1 max-size-time=1000000 ! '
                
                cmd += '{} sync=false'.format(sink)
                
                if hasattr(self, 'plIndex') and self.plIndex < len(self.choices):
                    if self.choices[self.plIndex] not in self.hosts:
                        volume = float(config.plugins.IPAudio.volLevel.value) / 0.5
                        cmd = cmd.replace('audioresample !', 'audioresample ! volume volume={} !'.format(volume))
            else:
                if delay_ms > 0:
                    cmd = 'ffmpeg -i "{}" -af "adelay={}|{}" -vn -f alsa default'.format(self.url, delay_ms, delay_ms)
                elif delay_ms < 0:
                    trim_sec = abs(delay_ms) / 1000.0
                    cmd = 'ffmpeg -ss {} -i "{}" -vn -f alsa default'.format(trim_sec, self.url)
                else:
                    cmd = 'ffmpeg -i "{}" -vn -f alsa default'.format(self.url)
            
            self.runCmd(cmd)

    def openConfig(self):
        self.session.openWithCallback(self.configClosed, IPAudioSetup)

    def configClosed(self, ret=None):
        pass

    def getEqualizerFilter(self):
        eq = config.plugins.IPAudio.equalizer.value
        
        if eq == "off":
            return None
        elif eq == "bass_boost":
            return "equalizer-3bands band0=-6.0 band1=-3.0 band2=6.0"
        elif eq == "treble_boost":
            return "equalizer-3bands band0=6.0 band1=-3.0 band2=-6.0"
        elif eq == "vocal":
            return "equalizer-3bands band0=-3.0 band1=6.0 band2=-3.0"
        elif eq == "rock":
            return "equalizer-3bands band0=5.0 band1=3.0 band2=-2.0"
        elif eq == "pop":
            return "equalizer-3bands band0=-2.0 band1=5.0 band2=3.0"
        elif eq == "classical":
            return "equalizer-3bands band0=4.0 band1=0.0 band2=-4.0"
        elif eq == "jazz":
            return "equalizer-3bands band0=3.0 band1=2.0 band2=4.0"
        
        return None

    def exit(self, ret=False):
        if self.guideTimer.isActive():
            self.guideTimer.stop()
        
        if self.statusTimer.isActive():
            self.statusTimer.stop()
        
        if self.bitrateCheckTimer.isActive():
            self.bitrateCheckTimer.stop()
        
        if ret and not self.timeShiftTimer.isActive():
            self.close()
        else:
            self.close()

class IPAudioPlaylist(IPAudioScreen):
    def __init__(self, session):
        IPAudioScreen.__init__(self, session)
        
        if isHD():
            if config.plugins.IPAudio.skin.value == 'orange':
                self.skin = SKIN_IPAudioPlaylist_ORANGE_HD
            elif config.plugins.IPAudio.skin.value == 'teal':
                self.skin = SKIN_IPAudioPlaylist_TEAL_HD
            elif config.plugins.IPAudio.skin.value == 'lime':
                self.skin = SKIN_IPAudioPlaylist_LIME_HD
            else:
                self.skin = SKIN_IPAudioPlaylist_ORANGE_HD
        else:
            if config.plugins.IPAudio.skin.value == 'orange':
                self.skin = SKIN_IPAudioPlaylist_ORANGE_FHD
            elif config.plugins.IPAudio.skin.value == 'teal':
                self.skin = SKIN_IPAudioPlaylist_TEAL_FHD
            elif config.plugins.IPAudio.skin.value == 'lime':
                self.skin = SKIN_IPAudioPlaylist_LIME_FHD
            else:
                self.skin = SKIN_IPAudioPlaylist_ORANGE_FHD
        
        self["key_green"] = Button(_("Remove Link"))
        self["key_red"] = Button(_("Reset Playlist"))
        self["IPAudioAction"] = ActionMap(["IPAudioActions"],
        {
            "cancel": self.exit,
            "green": self.keyGreen,
            "red": self.keyRed,
        }, -1)
        self.onLayoutFinish = []
        self.onShown = []
        self.loadPlaylist()

    def loadPlaylist(self):
        playlist = getPlaylist()
        if playlist:
            list = []
            for channel in playlist['playlist']:
                try:
                    list.append((str(channel['channel']), str(channel['url'])))
                except KeyError:
                    pass
            if len(list) > 0:
                self["list"].l.setList(self.iniMenu(list))
                self["server"].setText('Custom Playlist')
            else:
                self["list"].hide()
                self["server"].setText('Playlist is empty')
        else:
            self["list"].hide()
            self["server"].setText('Cannot load playlist')

    def keyRed(self):
        playlist = getPlaylist()
        if playlist:
            playlist['playlist'] = []
            with open("/etc/enigma2/ipaudio.json", 'w')as f:
                json.dump(playlist, f, indent=4)
            self.loadPlaylist()

    def keyGreen(self):
        playlist = getPlaylist()
        if playlist:
            if len(playlist['playlist']) > 0:
                index = self['list'].getSelectionIndex()
                currentPlaylist = playlist["playlist"]
                del currentPlaylist[index]
                playlist['playlist'] = currentPlaylist
                with open("/etc/enigma2/ipaudio.json", 'w')as f:
                    json.dump(playlist, f, indent=4)
                self.loadPlaylist()

    def exit(self):
        self.close()

class IPAudioInfo(Screen):
    def __init__(self, session):
        Screen.__init__(self, session)
        
        if isHD():
            if config.plugins.IPAudio.skin.value == 'orange':
                self.skin = SKIN_IPAudioInfo_ORANGE_HD
            elif config.plugins.IPAudio.skin.value == 'teal':
                self.skin = SKIN_IPAudioInfo_TEAL_HD
            elif config.plugins.IPAudio.skin.value == 'lime':
                self.skin = SKIN_IPAudioInfo_LIME_HD
            else:
                self.skin = SKIN_IPAudioInfo_ORANGE_HD
        else:
            if config.plugins.IPAudio.skin.value == 'orange':
                self.skin = SKIN_IPAudioInfo_ORANGE_FHD
            elif config.plugins.IPAudio.skin.value == 'teal':
                self.skin = SKIN_IPAudioInfo_TEAL_FHD
            elif config.plugins.IPAudio.skin.value == 'lime':
                self.skin = SKIN_IPAudioInfo_LIME_FHD
            else:
                self.skin = SKIN_IPAudioInfo_ORANGE_FHD
        
        self.skinName = "IPAudioInfo"
        
        self["info_text"] = Label()
        self["key_red"] = Button(_("Close"))
        
        self["actions"] = ActionMap(["ColorActions", "OkCancelActions"],
            {
                "cancel": self.close,
                "red": self.close,
                "ok": self.close,
            }, -1)
        
        self.onLayoutFinish.append(self.showInfo)
    
    def showInfo(self):
        info = """
IPAudio v{}

Original Developer
ZIKO

Maintainer
popking159

Enjoy FREE Enigma2 world!


Press OK or RED to close
        """.format(Ver)
        
        self["info_text"].setText(info.strip())

class IPAudioHelp(Screen):
    def __init__(self, session):
        Screen.__init__(self, session)
        
        if isHD():
            if config.plugins.IPAudio.skin.value == 'orange':
                self.skin = SKIN_IPAudioHelp_ORANGE_HD
            elif config.plugins.IPAudio.skin.value == 'teal':
                self.skin = SKIN_IPAudioHelp_TEAL_HD
            elif config.plugins.IPAudio.skin.value == 'lime':
                self.skin = SKIN_IPAudioHelp_LIME_HD
            else:
                self.skin = SKIN_IPAudioHelp_ORANGE_HD
        else:
            if config.plugins.IPAudio.skin.value == 'orange':
                self.skin = SKIN_IPAudioHelp_ORANGE_FHD
            elif config.plugins.IPAudio.skin.value == 'teal':
                self.skin = SKIN_IPAudioHelp_TEAL_FHD
            elif config.plugins.IPAudio.skin.value == 'lime':
                self.skin = SKIN_IPAudioHelp_LIME_FHD
            else:
                self.skin = SKIN_IPAudioHelp_ORANGE_FHD
        
        self.skinName = "IPAudioHelp"
        
        from Components.Sources.List import List
        self.help_lines = []
        self["help_text"] = List(self.help_lines)
        self["key_red"] = Button(_("Close"))
        
        self["actions"] = ActionMap(["ColorActions", "OkCancelActions", "DirectionActions"],
            {
                "cancel": self.close,
                "red": self.close,
                "ok": self.close,
                "up": self.scrollUp,
                "down": self.scrollDown,
            }, -1)
        
        self.onLayoutFinish.append(self.showHelp)
    
    def showHelp(self):
        help_lines = [
            "BASIC CONTROLS:",
            "OK: Play selected channel",
            "LEFT/RIGHT: Switch between categories",
            "UP/DOWN: Navigate channel list",
            "EXIT: Close plugin (audio continues)",
            "",
            "AUDIO CONTROLS:",
            "GREEN: Reset/Stop audio",
            "7: Decrease Audio delay (-0.5s)",
            "9: Increase Audio delay (+0.5s)",
            "8: Reset Audio delay",
            "  - Sync audio with video",
            "  - Range: -10s to +10s",
            "",
            "VIDEO SYNC:",
            "PAUSE: Activate TimeShift delay",
            "CH+: Increase Video delay (+0.5s)",
            "CH-: Decrease Video delay (-0.5s)",
            "  - Sync live TV with audio stream",
            "  - Range: 0 to +50s",
            "",
            "SETTINGS (MENU):",
            "Change skin color (Orange/Teal/Lime)",
            "Select player (GStreamer/FFmpeg)",
            "Configure audio output",
            "Enable/disable updates",
            "Adjust volume level",
            "",
            "WEB INTERFACE:",
            "Access: http://box-ip:8080/ipaudio",
            "Manage playlists",
            "Create categories",
            "Drag-and-drop channels",
            "Add/edit/delete channels",
            "",
            "BUTTONS:",
            "RED: Exit plugin",
            "GREEN: Reset audio",
            "YELLOW: Show this help",
            "BLUE: About/Info",
            "",
            "PLAYLIST MANAGEMENT:",
            "Create unlimited categories",
            "Each category has separate JSON file",
            "Files in: /etc/enigma2/ipaudio/",
            "Format: ipaudio_<name>.json",
            "",
            "TIPS:",
            "Use audio delay for stream sync",
            "Use TimeShift for live TV sync",
            "Playlists auto-reload on change",
            "Web interface updates in real-time",
            "",
            "Press UP/DOWN to scroll",
            "Press RED or EXIT to close",
        ]
        
        self.help_lines = [(line,) for line in help_lines]
        self["help_text"].setList(self.help_lines)
    
    def scrollUp(self):
        self["help_text"].up()
    
    def scrollDown(self):
        self["help_text"].down()

class IPAudioHandler(Screen):
    container = eConsoleAppContainer()
    
    def __init__(self, session):
        Screen.__init__(self, session)
        self.session = session
        
        ServiceEventTracker(screen=self, eventmap={
            iPlayableService.evEnd: self.evEnd,
            iPlayableService.evStopped: self.evEnd,
            iPlayableService.evStart: self.evServiceChanged,
        })
    
    def stopIPAudio(self):
        cprint("[IPAudio] stopIPAudio called")
        if self.container.running():
            self.container.kill()
    
    def evServiceChanged(self):
        cprint("[IPAudio] Service changed - stopping external audio and restoring original")
        
        if config.plugins.IPAudio.running.value:
            cprint("[IPAudio] Channel changed - restoring original audio/video")
            
            if self.container.running():
                self.container.kill()
            
            os.system("killall -9 gst-launch-1.0 ffmpeg 2>/dev/null")
            
            if fileExists("/dev/dvb/adapter0/audio10"):
                try:
                    os.rename("/dev/dvb/adapter0/audio10", "/dev/dvb/adapter0/audio0")
                    cprint("[IPAudio] Audio device restored")
                except:
                    pass
            
            current_service = self.session.nav.getCurrentlyPlayingServiceReference()
            if current_service:
                cprint("[IPAudio] Restarting service to restore audio/video")
                self.session.nav.stopService()
                
                from enigma import eTimer
                self.restoreTimer = eTimer()
                try:
                    self.restoreTimer.callback.append(lambda: self.restoreService(current_service))
                except:
                    self.restoreTimer_conn = self.restoreTimer.timeout.connect(lambda: self.restoreService(current_service))
                self.restoreTimer.start(100, True)
            
            config.plugins.IPAudio.running.value = False
            config.plugins.IPAudio.running.save()
            
            if HAVE_EALSA:
                try:
                    alsa = eAlsaOutput.getInstance()
                    alsa.setMute(False)
                    cprint("[IPAudio] ALSA unmuted")
                except:
                    pass
    
    def restoreService(self, service_ref):
        cprint("[IPAudio] Restoring service: {}".format(service_ref.toString()))
        self.session.nav.playService(service_ref)
    
    def evEnd(self):
        cprint("[IPAudio] Service ended")
        
        if config.plugins.IPAudio.running.value:
            if not config.plugins.IPAudio.keepaudio.value:
                cprint("[IPAudio] Cleaning up audio on service end")
                self.stopIPAudio()
                os.system("killall -9 gst-launch-1.0 ffmpeg 2>/dev/null")
                
                if fileExists("/dev/dvb/adapter0/audio10"):
                    try:
                        os.rename("/dev/dvb/adapter0/audio10", "/dev/dvb/adapter0/audio0")
                    except:
                        pass
                
                config.plugins.IPAudio.running.value = False
                config.plugins.IPAudio.running.save()

class IPAudioLauncher():
    def __init__(self, session):
        self.session = session

    def gotSession(self):
        keymap = resolveFilename(SCOPE_PLUGINS, "Extensions/IPAudio/keymap.xml")
        readKeymap(keymap)
        globalActionMap.actions['IPAudioSelection'] = self.ShowHide

    def ShowHide(self):
        if not isinstance(self.session.current_dialog, IPAudioScreen):
            self.session.open(IPAudioScreen)

def sessionstart(reason, session=None, **kwargs):
    if reason == 0:
        IPAudioHandler(session)
        IPAudioLauncher(session).gotSession()
        
        try:
            from Plugins.Extensions.IPAudio.webif import startWebInterface
            from twisted.internet import reactor
            
            reactor.callLater(2, startWebInterface)
        except Exception as e:
            print("[IPAudio] Could not start web interface: {}".format(e))
            import traceback
            traceback.print_exc()

def main(session, **kwargs):
    session.open(IPAudioScreen)

def showInmenu(menuid, **kwargs):
    if menuid == "mainmenu":
        return [("IPAudio", main, "IPAudio", 1)]
    else:
        return []

def Plugins(**kwargs):
    Descriptors = []
    Descriptors.append(PluginDescriptor(where=[PluginDescriptor.WHERE_SESSIONSTART], fnc=sessionstart))
    if config.plugins.IPAudio.mainmenu.value:
        Descriptors.append(PluginDescriptor(where=[PluginDescriptor.WHERE_MENU], fnc=showInmenu))
    Descriptors.append(PluginDescriptor(name="IPAudio", description="Listen to your favorite commentators", icon="logo.png", where=PluginDescriptor.WHERE_PLUGINMENU, fnc=main))
    return Descriptors