#!/usr/bin/python3
# -*- coding: utf-8 -*-
#############################################################################
from PyQt5.QtCore import (QPoint, Qt, QUrl, QProcess, QFile, QDir, QSettings, 
                          QStandardPaths, QRect)
from PyQt5.QtGui import QIcon, QDesktopServices
from PyQt5.QtWidgets import (QAction, QApplication, QMainWindow, QMessageBox, 
                             QMenu, QInputDialog, QLineEdit, QFileDialog, 
                             QFormLayout, QSlider, QPushButton, QDialog, QWidget)

import mpv
import os
import sys
from requests import get, post, request
import time
from datetime import datetime
import locale
from subprocess import check_output, STDOUT, CalledProcessError
import editor_intern

mytv = "tv-symbolic"
mybrowser = "video-television"
ratio = 1.777777778

class Tagesprogramm():
    def __init__(self):
        self.titleList = []
                  
        self.dictList = {'ard': 71, 'zdf': 37, 'arte': 58, 'zdf neo': 659, 'zdf info': 276, 'wdr': 46, 'ndr': 47, \
                    'mdr': 48, 'hr': 49, 'swr': 10142, 'br': 51, 'rbb': 52, '3sat': 56, 'kika': 57, \
                    'phoenix': 194, 'tagesschau': 100, 'one': 146, 'rtl': 38, 'sat 1': 39, 'pro 7': 40, \
                    'sport 1': 64, 'servus tv': 660, 'welt': 175, 'orf 1': 54, 'orf 2': 55, 'orf 3': 56, 'alpha': 104}

        headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:10.0) Gecko/20100101 Firefox/10.0',
            'Accept': '*/*',
            'Accept-Language': 'de-DE,en;q=0.5',
            'Content-Type': 'text/plain;charset=UTF-8',
            'Connection': 'keep-alive',
        }


        self.response = get('http://mobile.hoerzu.de/programbystation', headers = headers)
        self.response_json = self.response.json()

    def getURL(self, id):
        for i in self.response_json:
            if i['id'] == id:
                pr = i['broadcasts']
                for a in pr:
                    title = a.get('title')
                    st = a.get('startTime')
                    start = time.strftime("%-H:%M", time.localtime(st))
                    self.titleList.append(f"{start} {title}")
                    
    def getProgramm(self, channel):
        if channel.lower() in self.dictList:
            ch = channel.lower()
            self.getURL(self.dictList.get(ch))

            t = '\n'.join(self.titleList)
            return t
        else:
            return None


class URLGrabber():
    def __init__(self):
        self.channels = ["ard", "zdf", "mdr", "phoenix", "rbb", "br", "hr", "sr", "swr", 
                        "ndr", "dw", "wdr", "arte", "3sat", "kika", "orf", "sf"]
        self.chList = []
        self.urlList = []
        self.menuList = []

    def getURL(self, name):
        headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:10.0) Gecko/20100101 Firefox/10.0',
            'Accept': '*/*',
            'Accept-Language': 'de-DE,en;q=0.5',
            'Content-Type': 'text/plain;charset=UTF-8',
            'Connection': 'keep-alive',
        }
        
        
        data = {"queries":[{"fields":["title","topic"],"query":"livestream"},{"fields":["channel"],"query":"" + name + ""}]}
        response = post('https://mediathekviewweb.de/api/query', headers=headers, json=data)
        response_json = response.json()
        count = int(response_json['result']['queryInfo']['resultCount'])
        for x in range(count):
            title = response_json['result']['results'][x]['title']
            url = response_json['result']['results'][x]['url_video']
            if ".m3u8" in url and "3Sat" in title:
                self.chList.append(title.replace(".", " ").replace(' Livestream', ''))
                self.urlList.append(url)
            if ".m3u8" in url and "KiKA" in title:
                title = "kika"
                self.chList.append(title)
                self.urlList.append(url)
            if ".m3u8" in url and name.upper() in title:
                self.chList.append(title.replace(".", " ").replace(' Livestream', ''))
                self.urlList.append(url)
                
    def grab_urls(self):
        for ch in self.channels:
            self.getURL(ch)
            
        for x in range(len(self.urlList)):
            self.menuList.append(f'{self.chList[x]},{self.urlList[x]}')
        return self.menuList

class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        
        # lists
        self.file_list = []
        for entry in os.scandir(os.path.dirname(sys.argv[0])):
            if entry.is_file():
                if entry.name.endswith(".txt") and not entry.name == "mychannels.txt":
                    self.file_list.append(entry.name)
        self.file_list.sort(key=str.lower)
        flist = '\n'.join(self.file_list)
        print(f'gefundene Listen:\n{flist}')
        
        check = self.check_libmpv("libmpv")
        if not check:
            print("libmpv nicht gefunden\n")
            self.msgbox("libmpv nicht gefunden\nBenutze 'sudo apt-get install libmpv1'")
            sys.exit()
        else:
            print("libmpv gefunden")
        
        self.setAttribute(Qt.WA_NoSystemBackground, True)
        self.setStyleSheet("QMainWindow {background-color: 'black';}")
        self.osd_font_size = 28
        self.colorDialog = None
        self.settings = QSettings("TVPlayer2", "settings")
        self.own_list = []
        self.own_key = 0
        self.default_key = 0
        self.default_list = []
        self.urlList = []
        self.channel_list = []
        self.link = ""
        self.menulist = []
        self.recording_enabled = False
        self.is_recording = False
        self.recname = ""
        self.timeout = "60"
        self.tout = 60
        self.outfile = "/tmp/TV.mp4"
        self.myARD = ""
        self.channelname = ""
        self.mychannels = []
        self.channels_menu = QMenu()
        
        self.pid = None

        self.processR = QProcess()
        self.processR.started.connect(self.getPIDR)
        self.processR.finished.connect(self.timer_finished)
        self.processR.isRunning = False
        
        self.processW = QProcess()
        self.processW.started.connect(self.getPIDW)
        self.processW.finished.connect(self.recfinished)
        self.processW.isRunning = False
                         
        self.container = QWidget(self)
        self.setCentralWidget(self.container)
        self.container.setAttribute(Qt.WA_DontCreateNativeAncestors)
        self.container.setAttribute(Qt.WA_NativeWindow)
        self.container.setContextMenuPolicy(Qt.CustomContextMenu);
        self.container.customContextMenuRequested[QPoint].connect(self.contextMenuRequested)
        self.setAcceptDrops(True)
        
        self.mediaPlayer = mpv.MPV(log_handler=self.logger,
                           input_cursor=False,
                           osd_font_size=self.osd_font_size,
                           cursor_autohide=2000, 
                           cursor_autohide_fs_only=True,
                           osd_color='#d3d7cf',
                           osd_blur=2,
                           osd_bold=True,
                           wid=str(int(self.container.winId())), 
                           config=False, 
                           profile="libmpv",
                           vo="x11") 

                         
        self.mediaPlayer.set_loglevel('fatal')
        self.mediaPlayer.cursor_autohide = 2000       
        self.own_file = "mychannels.txt"
        print(self.own_file)
        if os.path.isfile(self.own_file):
            self.mychannels = open(self.own_file).read()
            ### remove empty lines
            self.mychannels = os.linesep.join([s for s in self.mychannels.splitlines() if s])
            with open(self.own_file, 'w') as f:
                f.write(self.mychannels)

        self.fullscreen = False

        self.setMinimumSize(320, 180)
        self.setGeometry(100, 100, 480, round(480 / ratio))

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)

        self.setWindowTitle("TV Player & Recorder")
        self.setWindowIcon(QIcon.fromTheme("multimedia-video-player"))

        self.myinfo = """<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><!--StartFragment--><span style=" font-size:xx-large; font-weight:600;">TVPlayer2</span></p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">©2020<br /><a href="https://github.com/Axel-Erfurt"><span style=" color:#0000ff;">Axel Schneider</span></a></p>
<h3 style=" margin-top:14px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><span style=" font-size:large; font-weight:600;">Tastaturkürzel:</span></h3>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">q = Beenden<br />f = toggle Fullscreen</p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">u = Url aus dem Clipboard abspielen</p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">Mausrad = Größe ändern</p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">↑ = lauter</p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">↓ = leiser</p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">m = Ton an/aus</p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">h = Mauszeiger an / aus</p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">r = Aufnahme mit Timer</p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">w = Aufnahme ohne Timer<br />s = Aufnahme beenden</p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">--------------------------------------</p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">a = ARD</p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">z = ZDF</p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">t = ARD Tagesschau</p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">1 bis 0 = eigene Sender (1 bis 10)</p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">→ = Sender +</p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">+ = eigener Sender +</p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">← = Sender -</p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">- = eigener Sender -</p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">p = Tagesprogramm des laufenden Senders</p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">j = was gerade im Fersehen läuft (mehrere Sender)</p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">d = was danach im Fersehen läuft (mehrere Sender)
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">e = was gerade läuft (aktueller Sender)"""
        print("Willkommen beim TV Player & Recorder")
        if self.is_tool("ffmpeg"):
            print("ffmpeg gefunden\nAufnahme möglich")
            self.recording_enabled = True
        else:
            self.msgbox("ffmpeg nicht gefunden\nkeine Aufnahme möglich")
            
        self.show()
        self.readSettings()            
        mg = URLGrabber()
        print("hole aktuelle Stream URLs")
        self.pList = mg.grab_urls()
            
        self.createMenu()
        
        
    def check_libmpv(self, mlib):
        cmd =  f'ldconfig -p | grep {mlib}'
        
        try:
            result = check_output(cmd, stderr=STDOUT, shell=True).decode("utf-8")
        except CalledProcessError:
            return False
            
        if not mlib in result:
            return False
        else:
            return True
            
    def check_mpv(self, mlib):
        cmd =  f'pip3 list | grep {mlib}'
        
        try:
            result = check_output(cmd, stderr=STDOUT, shell=True).decode("utf-8")
            
            if not mlib in result:
                return False
            else:
                return True
            
        except CalledProcessError as exc:
            result = exc.output
            return False
        
    def logger(self, loglevel, component, message):
        print('[{}] {}: {}'.format(loglevel, component, message), file=sys.stderr)
        
    def editOwnChannels(self):
        mfile = f"{os.path.dirname(sys.argv[0])}/mychannels.txt"
        #QDesktopServices.openUrl(QUrl(mfile))
        self.list_editor = editor_intern.Viewer()
        self.list_editor.show()
        
    def addToOwnChannels(self):
        k = "Name"
        dlg = QInputDialog()
        myname, ok = dlg.getText(self, 'Dialog', 'Namen eingeben', QLineEdit.Normal, k, Qt.Dialog)
        if ok:
            if os.path.isfile(self.own_file):
                with open(self.own_file, 'a') as f:
                    f.write(f"\n{myname},{self.link}")
                    self.channelname = myname
            else:
                self.msgbox(f"{self.own_file} existiert nicht!")
            
    def readSettings(self):
        print("lese Konfigurationsdatei ...")
        if self.settings.contains("geometry"):
            self.setGeometry(self.settings.value("geometry", QRect(26, 26, 200, 200)))
        else:
            self.setGeometry(100, 100, 480, 480 / ratio)
        if self.settings.contains("lastUrl") and self.settings.contains("lastName"):
            self.link = self.settings.value("lastUrl")
            self.channelname = self.settings.value("lastName")
            self.mediaPlayer.play(self.link)
            print(f"aktueller Sender: {self.channelname}\nURL: {self.link}")
            self.getEPG()
        else:
            if len(self.own_list) > 0:
                self.play_own(0)
                self.getEPG()
            else:
                self.playARD()
                self.getEPG()
        if self.settings.contains("volume"):
            vol = self.settings.value("volume")
            print("setze Lautstärke auf", vol)
            self.mediaPlayer.volume = (int(vol))
        self.mediaPlayer.show_text("Stream URLs werden aktualisiert", duration="3000", level=None) 
        
    def writeSettings(self):
        print("schreibe Konfigurationsdatei ...")
        self.settings.setValue("geometry", self.geometry())
        self.settings.setValue("lastUrl", self.link)
        self.settings.setValue("lastName", self.channelname)
        self.settings.setValue("volume", self.mediaPlayer.volume)
        self.settings.sync()
        
    def mouseDoubleClickEvent(self, event):
        self.handleFullscreen()
        event.accept()
            
    def getBufferStatus(self):
        print(self.mediaPlayer.bufferStatus())

    def createMenu(self):
        self.chMenu = self.channels_menu.addMenu("ARD / ZDF / ORF")
        self.chMenu.setIcon(QIcon.fromTheme(mytv))
        for playlist in self.pList:
            name = playlist.partition(",")[0]
            url = playlist.partition(",")[2]
            self.urlList.append(url)
            self.default_list.append(f'{name},{url}')
            self.channel_list.append(name)
            a = QAction(name, self, triggered=self.playTV)
            a.setIcon(QIcon.fromTheme(mybrowser))
            a.setData(url)
            self.chMenu.addAction(a)
            if "high" in url:
                a = QAction(f"{name} SD", self, triggered=self.playTV)
                a.setIcon(QIcon.fromTheme(mybrowser))
                a.setData(url.replace("high", "low"))
                self.default_list.append(f'{name} SD,{url.replace("high", "low")}')
                self.channel_list.append(f'{name} SD')
                self.chMenu.addAction(a)
                
                a = QAction(f"{name} HD", self, triggered=self.playTV)
                a.setIcon(QIcon.fromTheme(mybrowser))
                a.setData(url.replace("high", "veryhigh"))
                self.default_list.append(f'{name} HD,{url.replace("high", "veryhigh")}')
                self.channel_list.append(f'{name} HD')
                self.chMenu.addAction(a)

        myMenu = self.channels_menu.addMenu("eigene Sender")
        myMenu.setIcon(QIcon.fromTheme(mytv))
        if len(self.mychannels) > 0:
            for ch in self.mychannels.splitlines():
                name = ch.partition(",")[0]
                url = ch.partition(",")[2]
                self.own_list.append(f"{name},{url}")
                a = QAction(name, self, triggered=self.playTV)
                a.setIcon(QIcon.fromTheme(mybrowser))
                a.setData(url)
                myMenu.addAction(a)
        
        ### andere Listen
        for x in range(len(self.file_list)):
            newMenu = self.channels_menu.addMenu(os.path.splitext(os.path.basename(self.file_list[x]))[0])
            newMenu.setIcon(QIcon.fromTheme(mytv))
            channelList = open(self.file_list[x], 'r').read().splitlines()
            for ch in channelList:
                name = ch.partition(",")[0]
                url = ch.partition(",")[2]
                self.channel_list.append(f"{name},{url}")
                self.own_list.append(f"{name},{url}")
                a = QAction(name, self, triggered=self.playTV)
                a.setIcon(QIcon.fromTheme(mybrowser))
                a.setData(url)
                newMenu.addAction(a)            


        print("Stream URLs geholt!")
        self.mediaPlayer.show_text("Stream URLs aktualisiert", duration="4000", level=None) 
        self.getEPG()
        #############################
        
        if self.recording_enabled:
            self.channels_menu.addSection("Aufnahme")
    
            self.tv_record = QAction(QIcon.fromTheme("media-record"), "Aufnahme mit Timer (r)", triggered = self.record_with_timer)
            self.channels_menu.addAction(self.tv_record)

            self.tv_record2 = QAction(QIcon.fromTheme("media-record"), "Aufnahme ohne Timer (w)", triggered = self.record_without_timer)
            self.channels_menu.addAction(self.tv_record2)

            self.tv_record_stop = QAction(QIcon.fromTheme("media-playback-stop"), "Aufnahme beenden (s)", triggered = self.stop_recording)
            self.channels_menu.addAction(self.tv_record_stop)
    
            self.channels_menu.addSeparator()

        self.pmenu = self.channels_menu.addMenu("Fernsehprogramm")
        self.pmenu.setIcon(QIcon.fromTheme(mytv))

        self.tvpr_action = QAction(QIcon.fromTheme(mybrowser), "TV Programm des Tages", triggered = self.tv_programm_tag, shortcut = "p")
        self.pmenu.addAction(self.tvpr_action)
        
        self.now_action = QAction(QIcon.fromTheme(mybrowser), "TV Programm jetzt", triggered = self.tv_programm_now, shortcut = "j")
        self.pmenu.addAction(self.now_action)
        
        self.later_action = QAction(QIcon.fromTheme(mybrowser), "TV Programm danach", triggered = self.tv_programm_later, shortcut = "d")
        self.pmenu.addAction(self.later_action)

        self.about_action = QAction(QIcon.fromTheme("help-about"), "Info (i)", triggered = self.handleAbout, shortcut = "i")
        self.channels_menu.addAction(self.about_action)

        self.channels_menu.addSeparator()

        self.url_action = QAction(QIcon.fromTheme("browser"), "URL vom Clipboard spielen (u)", triggered = self.playURL)
        self.channels_menu.addAction(self.url_action)
        
        self.channels_menu.addSection("Einstellungen")

        self.color_action = QAction(QIcon.fromTheme("preferences-color"), "Bildeinstellungen (c)", triggered = self.showColorDialog)
        self.channels_menu.addAction(self.color_action)

        self.channels_menu.addSeparator()

        self.channels_menu.addSeparator()

        self.channels_menu.addSection("Sender bearbeiten / hinzufügen")        
        self.addChannelAction = QAction(QIcon.fromTheme("add"), "aktuellen Sender hinzufügen", triggered = self.addToOwnChannels)
        self.channels_menu.addAction(self.addChannelAction)
        
        self.editChannelAction = QAction(QIcon.fromTheme("text-editor"), "eigene Sender bearbeiten", triggered = self.editOwnChannels)
        self.channels_menu.addAction(self.editChannelAction)
        
        self.channels_menu.addSeparator()
        
        self.quit_action = QAction(QIcon.fromTheme("application-exit"), "Beenden (q)", triggered = self.handleQuit)
        self.channels_menu.addAction(self.quit_action)
        
    def showTime(self):
        t = str(datetime.now())[11:16]
        self.mediaPlayer.show_text(t, duration="4000", level=None) 
        
    def tv_programm_now(self):
        self.mediaPlayer.osd_font_size = self.osd_font_size
        channels = ['Das Erste', 'ZDF', 'ZDFinfo', 'ZDFneo', 'MDR', 'Phoenix', 'RBB', 'BR', 'HR', 'SWR', 'NDR', 'WDR', 'Arte', '3sat', 'ARD alpha', 'Sport 1', 'ORF 1', 'ORF 2', 'ORF 3', 'ORF Sport', 'tagesschau24', 'One ,']

        url = "https://www.hoerzu.de/text/tv-programm/jetzt.php"
        programm = []

        pr = (request(method='GET', url = url).text.partition(".</H3>")[2]
                    .partition("nach oben")[0][1:].replace("* ", "").replace("* ", "").replace(" .", ""))

        for ch in channels:
            x = int(pr.find(ch))
            line = pr[x:].partition("</a>")[0].replace(">", "").partition("<br/")[0]
            if not line == "":
                programm.append(line.replace(" ,", ":", 1).replace(" ,", " -", 1))
        self.mediaPlayer.show_text('\n'.join(programm), duration="7000", level=None)        

        
    def tv_programm_later(self):
        self.mediaPlayer.osd_font_size = self.osd_font_size
        channels = ['Das Erste', 'ZDF', 'ZDFinfo', 'ZDFneo', 'MDR', 'Phoenix', 
                    'RBB', 'BR', 'HR', 'SWR', 'NDR', 'WDR', 'Arte', '3sat', 'ARD alpha', 
                    'Sport 1', 'ORF 1', 'ORF 2', 'ORF 3', 'ORF Sport', 'tagesschau24', 'One ,']

        url = "https://www.hoerzu.de/text/tv-programm/gleich.php"
        programm = []

        pr = (request(method='GET', url = url).text.partition(".</H3>")[2]
            .partition("nach oben")[0][1:].replace("* ", "").replace("* ", "").replace(" .", ""))

        for ch in channels:
            x = int(pr.find(ch))
            line = pr[x:].partition("</a>")[0].replace(">", "").partition("<br/")[0]
            if not line == "":
                programm.append(line.replace(" ,", ":", 1).replace(" ,", " -", 1))
        self.mediaPlayer.show_text('\n'.join(programm), duration="7000", level=None) 

         
    def dragEnterEvent(self, event):
        event.acceptProposedAction()

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            url = event.mimeData().urls()[0].toString()
            print(f"neue URL abgelegt: '{url}'")
            self.link = url.strip()
            self.mediaPlayer.stop()
            self.mediaPlayer.play(self.link)
        elif event.mimeData().hasText():
            mydrop =  event.mimeData().text().strip()
            if ("http") in mydrop:
                print(f"neuer Link abgelegt: '{mydrop}'")
                self.link = mydrop
                self.mediaPlayer.play(self.link)
        event.acceptProposedAction()
        

    def recfinished(self):
        print("Aufnahme wird beendet")

    def is_tool(self, name):
        tool = QStandardPaths.findExecutable(name)
        if tool != "":
            return True
        else:
            return False

    def getPIDR(self):
        print("pid", self.processR.processId())
        self.pid = self.processR.processId()

    def getPIDW(self):
        print("pid", self.processW.processId())
        self.pid = self.processW.processId()
            
    def record_without_timer(self):
        if not self.recording_enabled == False:
            if QFile(self.outfile).exists:
                print("lösche Datei " + self.outfile) 
                QFile(self.outfile).remove
            else:
                print("Die Datei " + self.outfile + " existiert nicht") 
            self.recname = self.channelname
            print("Aufnahme in Datei /tmp/TV.mp4")
            self.mediaPlayer.show_text("record without timer", duration="3000", level=None) 
            self.is_recording = True
            self.recordChannelW()

    def record_with_timer(self):
        if not self.recording_enabled == False:
            if QFile(self.outfile).exists:
                print("lösche Datei " + self.outfile) 
                QFile(self.outfile).remove
            else:
                print("Die Datei " + self.outfile + " existiert nicht") 
            infotext = '<i>temporäre Aufnahme in Datei: /tmp/TV.mp4</i> \
                            <br><b><font color="#a40000";>Speicherort und Dateiname werden nach Beenden der Aufnahme festgelegt.</font></b> \
                            <br><br><b>Beispiel:</b><br>60s (60 Sekunden)<br>120m (120 Minuten)'
            dlg = QInputDialog()
            tout, ok = dlg.getText(self, 'Länge der Aufnahme', infotext, \
                                    QLineEdit.Normal, "90m", Qt.Dialog)
            if ok:
                self.tout = str(tout)
                self.recordChannel()
            else:
                print("Aufnahme abgebrochen")

    def recordChannel(self):
        self.processR.isRunning = True
        self.recname = self.channelname
        cmd = f'timeout {str(self.tout)} ffmpeg -y -i {self.link.replace("?sd=10&rebase=on", "")} -bsf:a aac_adtstoasc -vcodec copy -c copy -crf 50 "{self.outfile}"'
        print("Aufnahme in /tmp mit Timeout: " + str(self.tout))
        self.mediaPlayer.show_text(f"Aufnahme mit Timer {str(self.tout)}", duration="3000", level=None) 
        self.is_recording = True
        self.processR.start(cmd)
        
    def recordChannelW(self):
        self.processW.isRunning = True
        self.recname = self.channelname
        cmd = f'ffmpeg -y -i {self.link.replace("?sd=10&rebase=on", "")} -bsf:a aac_adtstoasc -vcodec copy -c copy -crf 50 "{self.outfile}"'
        self.mediaPlayer.show_text("Aufnahme", duration="3000", level=None) 
        self.is_recording = True
        self.processW.start(cmd)
################################################################

    def saveMovie(self):
        self.fileSave()

    def fileSave(self):
        infile = QFile(self.outfile)
        path, _ = QFileDialog.getSaveFileName(self, "Speichern als...", QDir.homePath() + "/Videos/" + self.recname + ".mp4",
            "Video (*.mp4)")
        if os.path.exists(path):
            os.remove(path)
        if (path != ""):
            savefile = path
            if QFile(savefile).exists:
                QFile(savefile).remove()
            print("saving " + savefile)
            if not infile.copy(savefile):
                QMessageBox.warning(self, "Fehler",
                    "Kann Datei nicht schreiben %s:\n%s." % (path, infile.errorString()))
            if infile.exists:
                infile.remove()

    def stop_recording(self):
        print("StateR:", self.processR.state())
        print("StateW:", self.processW.state())
        if self.is_recording == True:
            if self.processW.isRunning:
                print("recording will be stopped")
                cmd = f"kill -9 {self.pid}"
                print(cmd, "(stop ffmpeg)")
                QProcess().execute(cmd)
                if self.processW.exitStatus() == 0:
                    self.processW.isRunning = False
                    self.saveMovie()
        else:
            print("no recording")

    def timer_finished(self):
        print("Timer ended\nrecording will be stopped")
        self.processR.isRunning = False
        self.is_recording = False
        self.saveMovie()

    def playURL(self):
        clip = QApplication.clipboard()
        self.link = clip.text().strip()
        self.mediaPlayer.play(self.link)

    def handleError(self, loglevel, message):
        print('{}: {}'.format(loglevel, message), file=sys.stderr)

    def handleMute(self):
        if not self.mediaPlayer.mute:
            self.mediaPlayer.mute = True
            print("stumm")
        else:
            self.mediaPlayer.mute = False
            print("nicht stumm")

    def handleAbout(self):
        QMessageBox.about(self, "TVPlayer2", self.myinfo)
        
    def getEPG(self):      
        print("ch =", self.channelname)
        ch_name = self.channelname.replace(" SD", "").replace(" HD", "")
        if ch_name == "ARD":
            ch_name = "Das Erste"
        if "MDR" in ch_name :
            ch_name = "MDR"
        if "NDR" in ch_name :
            ch_name = "NDR"
        if "BR" in ch_name :
            ch_name = "BR"
        if "Tagesschau" in ch_name:
            ch_name = "tagesschau24"
        if "Alpha" in ch_name:
            ch_name = "ARD alpha"
        if "ZDF info" in ch_name:
            ch_name = "ZDFinfo"
        if "ZDF neo" in ch_name:
            ch_name = "ZDFneo"
        if "ONE" in ch_name:
            ch_name = "One ,"
        if ch_name == "SR":
            ch_name = "SWR"
        if "ARTE" in ch_name:
            ch_name = "Arte"
        if "Welt" in ch_name:
            ch_name = "WELT"
        if "ORF" in ch_name:
            ch_name = ch_name.replace("-", " ")
        if "3Sat" in ch_name or "3 Sat" in ch_name:
            ch_name = "3sat"
        if "kika" in ch_name:
            return
            
        url = "https://www.hoerzu.de/text/tv-programm/jetzt.php"
        programm = []

        pr = (request(method='GET', url = url).text.partition(".</H3>")[2]
                        .partition("nach oben")[0][1:].replace("* ", "")
                        .replace("* ", "").replace(" .", ""))

        x = int(pr.find(ch_name))
        line = pr[x:].partition("Uhr")[0].replace(",", " - ")
        if not line == "":
            programm.append(line.replace(f"{ch_name}  -  ", ''))
        
        now = str(datetime.now())[11:16]
        msg = '\n'.join(programm)
        msg = f"{now}\n{msg}Uhr"
        print(msg)
        self.mediaPlayer.osd_font_size = 40
        self.mediaPlayer.show_text(msg, duration="3000", level=None)
        
    def getEPG_detail(self):
        print("ch =", self.channelname)
        ch_name = self.channelname.replace(" SD", "").replace(" HD", "")
        if ch_name == "ARD":
            ch_name = "Das Erste"
        if "MDR" in ch_name :
            ch_name = "MDR"
        if "NDR" in ch_name :
            ch_name = "NDR"
        if "BR" in ch_name :
            ch_name = "BR"
        if "Tagesschau" in ch_name:
            ch_name = "tagesschau24"
        if "Alpha" in ch_name:
            ch_name = "ARD alpha"
        if "ZDF info" in ch_name:
            ch_name = "ZDFinfo"
        if "ZDF neo" in ch_name:
            ch_name = "ZDFneo"
        if "ONE" in ch_name:
            ch_name = "One ,"
        if ch_name == "SR":
            ch_name = "SWR"
        if "ARTE" in ch_name:
            ch_name = "Arte"
        if "Welt" in ch_name:
            ch_name = "WELT"
        if "ORF" in ch_name:
            ch_name = ch_name.replace("-", " ")
        if "3Sat" in ch_name or "3 Sat" in ch_name:
            ch_name = "3sat"
        if "kika" in ch_name:
            return
        self.mediaPlayer.osd_font_size = 24
        url = "https://www.hoerzu.de/text/tv-programm/jetzt.php"
        t = get(url).content.decode("utf-8")

        titel = t.partition(ch_name)[2].partition("</a>")[0].replace(",", "")[2:]

        r = t.partition(ch_name)[0].rpartition('<a href="')[2].partition('">')[0]
        link = f"https://www.hoerzu.de/text/tv-programm/{r}"

        result = get(link).text.partition(ch_name)[2].partition("<p>")[2].partition("</p>")[0]
        msg = (f'{titel}\n{result}')
        self.mediaPlayer.show_text(msg, duration="8000", level=None)
        
    def tv_programm_tag(self):
        self.mediaPlayer.osd_font_size = self.osd_font_size
        ch = self.channelname.replace(" SD", "").replace(" HD", "")
        if ch.startswith("BR"):
            ch = ch.partition(" ")[0]
        if ch.startswith("MDR"):
            ch = ch.partition(" ")[0]
        if ch.startswith("NDR"):
            ch = ch.partition(" ")[0]
        if ch.startswith("RBB"):
            ch = ch.partition(" ")[0]
        if ch.startswith("ORF"):
            ch = ch.replace("-", " ")
        if "Tagesschau" in ch:
            ch = "tagesschau"
        if "ARTE" in ch:
            ch = "arte"
        if "alpha" in ch or "Alpha" in ch:
            ch = "alpha"
        if ch =="SR":
            ch = "swr"
        if "ONE" in ch:
            ch = "one"
        if "3Sat" in ch or "3 Sat" in ch:
            ch = "3sat"
        tp = Tagesprogramm()
        msg = tp.getProgramm(ch)
        if not msg == None:
            now = f"{str(datetime.now().hour)}:"
            if now in msg:
                msg = f"{now}{msg.partition(now)[2]}"
            self.mediaPlayer.show_text(msg, duration="7000", level=None) 

    def handleFullscreen(self):
        if self.fullscreen == True:
            self.fullscreen = False
            print("kein Fullscreen")
        else:
            self.rect = self.geometry()
            self.showFullScreen()
            QApplication.setOverrideCursor(Qt.ArrowCursor)
            self.fullscreen = True
            print("Fullscreen eingeschaltet")
        if self.fullscreen == False:
            self.showNormal()
            self.setGeometry(self.rect)
            QApplication.setOverrideCursor(Qt.BlankCursor)
        self.handleCursor()

    def handleCursor(self):
        if  QApplication.overrideCursor() ==  Qt.ArrowCursor:
            QApplication.setOverrideCursor(Qt.BlankCursor)
        else:
            QApplication.setOverrideCursor(Qt.ArrowCursor)
    
    def handleQuit(self):
        self.mediaPlayer.quit
        self.writeSettings()
        print("Auf Wiedersehen ...")
        app.quit()
        sys.exit()

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Q:
            self.handleQuit()
        elif e.key() == Qt.Key_H:
            self.handleCursor()
        elif e.key() == Qt.Key_P:
            self.tv_programm_tag()
        elif e.key() == Qt.Key_J:
            self.tv_programm_now()
        elif e.key() == Qt.Key_D:
            self.tv_programm_later()
        elif e.key() == Qt.Key_F:
            self.handleFullscreen()
        elif e.key() == Qt.Key_M:
            self.handleMute()
        elif e.key() == Qt.Key_I:
            self.handleAbout()
        elif e.key() == Qt.Key_U:
            self.playURL()
        elif e.key() == Qt.Key_R:
            self.record_with_timer()
        elif e.key() == Qt.Key_S:
            self.stop_recording()
        elif e.key() == Qt.Key_T:
            self.showTime()
        elif e.key() == Qt.Key_E:
            self.getEPG_detail()
        elif e.key() == Qt.Key_W:
            self.record_without_timer()
        elif e.key() == Qt.Key_C:
            self.showColorDialog()
        elif e.key() == Qt.Key_1:
            self.play_own(0)
        elif e.key() == Qt.Key_2:
            self.play_own(1)
        elif e.key() == Qt.Key_3:
            self.play_own(2)
        elif e.key() == Qt.Key_4:
            self.play_own(3)
        elif e.key() == Qt.Key_5:
            self.play_own(4)
        elif e.key() == Qt.Key_6:
            self.play_own(5)
        elif e.key() == Qt.Key_7:
            self.play_own(6)
        elif e.key() == Qt.Key_8:
            self.play_own(7)
        elif e.key() == Qt.Key_9:
            self.play_own(8)
        elif e.key() == Qt.Key_0:
            self.play_own(9)
        elif e.key() == Qt.Key_A:
            self.playARD()
        elif e.key() == Qt.Key_Z:
            self.playZDF()
        elif e.key() == Qt.Key_Right:
            self.play_next(self.default_key + 1)
        elif e.key() == Qt.Key_Plus:
            self.play_own(self.own_key + 1)
        elif e.key() == Qt.Key_Left:
            self.play_next(self.default_key - 1)
        elif e.key() == Qt.Key_Minus:
            if not self.own_key == 0:
                self.play_own(self.own_key - 1)
        elif e.key() == Qt.Key_Up:
            if self.mediaPlayer.volume < 160:
                self.mediaPlayer.volume = (self.mediaPlayer.volume + 5)
                print("Lautstärke:", self.mediaPlayer.volume)
        elif e.key() == Qt.Key_Down:
            if self.mediaPlayer.volume > 5:
                self.mediaPlayer.volume = (self.mediaPlayer.volume - 5)
                print("Lautstärke:", self.mediaPlayer.volume)
        else:
            e.accept()

    def contextMenuRequested(self, point):
        self.channels_menu.exec_(self.mapToGlobal(point))
        
    def playFromKey(self, url):
        self.link = url
        self.mediaPlayer.play(self.link)
        
    def playARD(self):
        for x in range(len(self.default_list)):
            line = self.default_list[x].split(",")
            if line[0] == "ARD":
                self.link = line[1]
                self.playFromKey(self.link)
                self.channelname = "ARD"
                if self.channelname in self.channel_list:
                    self.default_key = self.channel_list.index(self.channelname)
        
    def playZDF(self):
        for x in range(len(self.default_list)):
            line = self.default_list[x].split(",")
            if line[0] == "ZDF SD":
                self.link = line[1]
                self.playFromKey(self.link)
                self.channelname = "ZDF"
                if self.channelname in self.channel_list:
                    self.default_key = self.channel_list.index(self.channelname)
                
    def playTV(self):
        action = self.sender()
        self.link = action.data().replace("\n", "")
        self.channelname = action.text()
        if self.channelname in self.channel_list:
            self.default_key = self.channel_list.index(self.channelname)
        else:
            self.own_key = self.own_list.index(f"{self.channelname},{self.link}")
        print(f"aktueller Sender: {self.channelname}\nURL: {self.link}")
        self.mediaPlayer.play(self.link)
        #self.mediaPlayer.wait_until_playing()
        self.getEPG()
        

    def play_own(self, channel):
        if not channel > len(self.own_list) - 1:
            self.own_key = channel
            self.link = self.own_list[channel].split(",")[1]
            self.channelname = self.own_list[channel].split(",")[0]
            print("eigener Sender:", self.channelname, "\nURL:", self.link)
            self.mediaPlayer.play(self.link)
            #self.mediaPlayer.wait_until_playing()
            self.getEPG()
        else:
            print(f"Kanal {channel} ist nicht vorhanden")
            
            
    def play_next(self, channel):
        if not channel > len(self.default_list) - 1:
            self.default_key = channel
            self.link = self.default_list[channel].split(",")[1]
            self.channelname = self.default_list[channel].split(",")[0]
            print(f"aktueller Sender: {self.channelname}\nURL: {self.link}")
            self.mediaPlayer.play(self.link)
            #self.mediaPlayer.wait_until_playing()
            self.getEPG()
        else:
            self.play_next(0)
            
    def play_previous(self, channel):
        if not channel == 0:
            self.default_key = channel
            self.link = self.default_list[channel].split(",")[1]
            self.channelname = self.default_list[channel].split(",")[0]
            print(f"aktueller Sender: {self.channelname}\nURL: {self.link}")
            self.mediaPlayer.play(self.link)
            #self.mediaPlayer.wait_until_playing()
            self.getEPG()
        else:
            self.play_next(len(self.default_list))

    def closeEvent(self, event):
        event.accept()

    def msgbox(self, message):
        QMessageBox.warning(self, "Meldung", message)
        
    def wheelEvent(self, event):
        mwidth = self.frameGeometry().width()
        mscale = round(event.angleDelta().y() / 6)
        self.resize(mwidth + mscale, round((mwidth + mscale) / ratio))
        event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() \
                      - QPoint(round(self.frameGeometry().width() / 2), \
                               round(self.frameGeometry().height() / 2)))
            event.accept()
            
    def setBrightness(self):
        self.mediaPlayer.brightness = self.brightnessSlider.value()
        
    def setContrast(self):
        self.mediaPlayer.contrast = self.contrastSlider.value()
        
    def setHue(self):
        self.mediaPlayer.hue = self.hueSlider.value()

    def setSaturation(self):
        self.mediaPlayer.saturation = self.saturationSlider.value()
        
    def showColorDialog(self):
        if self.colorDialog is None:
            self.brightnessSlider = QSlider(Qt.Horizontal)
            self.brightnessSlider.setRange(-100, 100)
            self.brightnessSlider.setValue(self.mediaPlayer.brightness)
            self.brightnessSlider.valueChanged.connect(self.setBrightness)

            self.contrastSlider = QSlider(Qt.Horizontal)
            self.contrastSlider.setRange(-100, 100)
            self.contrastSlider.setValue(self.mediaPlayer.contrast)
            self.contrastSlider.valueChanged.connect(self.setContrast)
            
            self.hueSlider = QSlider(Qt.Horizontal)
            self.hueSlider.setRange(-100, 100)
            self.hueSlider.setValue(self.mediaPlayer.hue)
            self.hueSlider.valueChanged.connect(self.setHue)

            self.saturationSlider = QSlider(Qt.Horizontal)
            self.saturationSlider.setRange(-100, 100)
            self.saturationSlider.setValue(self.mediaPlayer.saturation)
            self.saturationSlider.valueChanged.connect(self.setSaturation)

            layout = QFormLayout()
            layout.addRow("Helligkeit", self.brightnessSlider)
            layout.addRow("Kontrast", self.contrastSlider)
            layout.addRow("Farbton", self.hueSlider)
            layout.addRow("Farbe", self.saturationSlider)

            btn = QPushButton("zurücksetzen")
            btn.setIcon(QIcon.fromTheme("preferences-color"))
            layout.addRow(btn)

            button = QPushButton("Schließen")
            button.setIcon(QIcon.fromTheme("ok"))
            layout.addRow(button)

            self.colorDialog = QDialog(self)
            self.colorDialog.setWindowTitle("Bildeinstellungen")
            self.colorDialog.setLayout(layout)

            btn.clicked.connect(self.resetColors)
            button.clicked.connect(self.colorDialog.close)

        self.colorDialog.resize(300, 180)
        self.colorDialog.show()

    def resetColors(self):
        self.brightnessSlider.setValue(0)
        self.mediaPlayer.brightness = (0)

        self.contrastSlider.setValue(0)
        self.mediaPlayer.contrast = (0)

        self.saturationSlider.setValue(0)
        self.mediaPlayer.saturation = (0)

        self.hueSlider.setValue(0)
        self.mediaPlayer.hue = (0)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    locale.setlocale(locale.LC_NUMERIC, 'C')
    mainWin = MainWindow()
    sys.exit(app.exec_())
