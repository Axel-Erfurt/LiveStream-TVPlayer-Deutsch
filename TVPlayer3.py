#!/usr/bin/python3
# -*- coding: utf-8 -*-
#############################################################################
from PyQt5.QtCore import (QPoint, Qt, QUrl, QProcess, QFile, QDir, QSettings, 
                          QStandardPaths, QFileInfo, QCoreApplication, QRect)
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (QAction, QApplication, QMainWindow, QMessageBox, 
                             QMenu, QInputDialog, QLineEdit, QFileDialog, QLabel, 
                             QFormLayout, QSlider, QPushButton, QDialog)
from PyQt5.QtMultimedia import QMediaContent, QMediaPlayer
from PyQt5.QtMultimediaWidgets import QVideoWidget

import os
import sys
from requests import get, post, request
import time
import locale
from datetime import date

mytv = "tv-symbolic"
mybrowser = "video-television"
ratio = 1.777777778

class Tagesprogramm():
    def __init__(self):
        loc = locale.getlocale()
        locale.setlocale(locale.LC_ALL, loc)
        dt = date.today().strftime("%-d.%B %Y")
        self.titleList = []
        self.titleList.append(dt)
                  
        self.dictList = {'ard': 71, 'zdf': 37, 'arte': 58, 'zdf neo': 659, 'zdf info': 276, 'wdr': 46, 'ndr': 47, \
                    'mdr': 48, 'hr': 49, 'swr': 10142, 'br': 51, 'rbb': 52, '3sat': 56, 'kika': 57, \
                    'phoenix': 194, 'tagesschau': 100, 'one': 146, 'rtl': 38, 'sat 1': 39, 'pro 7': 40, \
                    'sport 1': 64, 'servus tv': 660, 'welt': 175, 'orf 1': 54, 'orf 2': 55, 'orf 3': 56}

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
            self.titleList.append(f"{ch.upper()} Programm\n")
            self.getURL(self.dictList.get(ch))

            t = '\n'.join(self.titleList)
            return t
        else:
            return None


class URLGrabber():
    def __init__(self):
        self.channels = ["ard", "zdf", "mdr", "phoenix", "rbb", "br", "hr", "sr", "swr", "ndr", "dw", "wdr", "arte", "3sat", "kika", "orf", "sf"]
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
        self.settings = QSettings("TVPlayer2", "settings")
        mg = URLGrabber()
        print("hole aktuelle Stream URLs")
        self.pList = mg.grab_urls()
        self.colorDialog = None
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

        self.process = QProcess()
        self.process.started.connect(self.getPID)
        self.process.finished.connect(self.timer_finished)
        self.process.finished.connect(self.recfinished)

        self.mediaPlayer = QMediaPlayer(None, QMediaPlayer.StreamPlayback)
        self.mediaPlayer.service().requestControl('org.qt-project.qt.mediastreamscontrol/5.0')
        self.mediaPlayer.setVolume(90)
        print("Volume:", self.mediaPlayer.volume())
        self.mediaPlayer.error.connect(self.handleError)
        #self.mediaPlayer.bufferStatusChanged.connect(self.getBufferStatus)
        self.setAcceptDrops(True)

        self.videoWidget = QVideoWidget(self)
        self.videoWidget.setStyleSheet("background: black;")
        self.videoWidget.setAcceptDrops(True)
        self.videoWidget.setAspectRatioMode(1)
        self.videoWidget.setContextMenuPolicy(Qt.CustomContextMenu);
        self.videoWidget.customContextMenuRequested[QPoint].connect(self.contextMenuRequested)
        self.setCentralWidget(self.videoWidget)
        self.mediaPlayer.setVideoOutput(self.videoWidget)

        self.lbl = QLabel(self.videoWidget)
        self.lbl.setGeometry(3, 3, 11, 11)
        self.lbl.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        self.lbl.setStyleSheet("background: #2e3436; color: #ef2929; font-size: 10pt;")
        self.lbl.setText("®")
        self.lbl.hide()

        self.root = QFileInfo.path(QFileInfo(QCoreApplication.arguments()[0]))
        self.own_file = f"{self.root}/mychannels.txt"
        if os.path.isfile(self.own_file):
            self.mychannels = open(self.own_file).read()
            ### remove empty lines
            self.mychannels = os.linesep.join([s for s in self.mychannels.splitlines() if s])

        self.fullscreen = False

        self.setAttribute(Qt.WA_NoSystemBackground, True)
        self.setMinimumSize(320, 180)
        self.setGeometry(100, 100, 480, 480 / ratio)

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)

        self.setWindowTitle("TV Player & Recorder")
        self.setWindowIcon(QIcon.fromTheme("multimedia-video-player"))

        self.myinfo = """<h1 style=" margin-top:18px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><!--StartFragment--><span style=" font-size:xx-large; font-weight:600;">TVPlayer2</span></h1>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">©2020<br /><a href="https://github.com/Axel-Erfurt"><span style=" text-decoration: none; color:#0000ff;">Axel Schneider</span></a></p>
<p style="-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><br /></p>
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
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">d = was danach im Fersehen läuft (mehrere Sender)"""
        print("Willkommen beim TV Player & Recorder")
        if self.is_tool("streamlink"):
            print("streamlink gefunden\nAufnahme möglich")
            self.recording_enabled = True
        else:
            self.msgbox("streamlink nicht gefunden\nkeine Aufnahme möglich")
            
        self.createMenu()
        self.readSettings()
        
    def addToOwnChannels(self):
        k = "Name"
        dlg = QInputDialog()
        myname, ok = dlg.getText(self, 'Dialog', 'Namen eingeben', QLineEdit.Normal, k, Qt.Dialog)
        if ok:
            with open(self.own_file, 'a') as f:
                f.write(f"\n{myname},{self.link}")
                self.channelname = myname
            
    def readSettings(self):
        print("lese Konfigurationsdatei ...")
        if self.settings.contains("geometry"):
            self.setGeometry(self.settings.value("geometry", QRect(26, 26, 200, 200)))
        else:
            self.setGeometry(100, 100, 480, 480 / ratio)
        if self.settings.contains("lastUrl") and self.settings.contains("lastName"):
            self.link = self.settings.value("lastUrl")
            self.channelname = self.settings.value("lastName")
            self.mediaPlayer.setMedia(QMediaContent(QUrl(self.link)))
            self.mediaPlayer.play()
            print("aktueller Sender:", self.channelname, "\nURL:", self.link)
        else:
            if len(self.own_list) > 0:
                self.play_own(0)
            else:
                self.playARD()
        if self.settings.contains("volume"):
            vol = self.settings.value("volume")
            print("setze Lautstärke auf", vol)
            self.mediaPlayer.setVolume(int(vol))

                
    def writeSettings(self):
        print("schreibe Konfigurationsdatei ...")
        self.settings.setValue("geometry", self.geometry())
        self.settings.setValue("lastUrl", self.link)
        self.settings.setValue("lastName", self.channelname)
        self.settings.setValue("volume", self.mediaPlayer.volume())
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

        a = QAction(QIcon.fromTheme(mybrowser), "Sport1 Live", self, triggered=self.play_Sport1)
        self.channels_menu.addAction(a)
        self.channel_list.append("Sport 1")
        
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
        
        self.addChannelAction = QAction(QIcon.fromTheme("add"), "aktuellen Sender hinzufügen", triggered = self.addToOwnChannels)
        self.channels_menu.addAction(self.addChannelAction)
        
        self.quit_action = QAction(QIcon.fromTheme("application-exit"), "Beenden (q)", triggered = self.handleQuit)
        self.channels_menu.addAction(self.quit_action)
        
    def tv_programm_now(self):
        channels = ['Das Erste', 'ZDF', 'ZDFinfo', 'ZDFneo', 'MDR', 'Phoenix', 'RBB', 'BR', 'HR', 'SWR', 'NDR', 'WDR', 'Arte', '3sat', 'ARD alpha', 'KiKa', 'Sport 1', 'ORF 1', 'ORF 2', 'ORF 3', 'ORF Sport']

        url = "https://www.hoerzu.de/text/tv-programm/jetzt.php"
        programm = []

        pr = request(method='GET', url = url).text.partition(".</H3>")[2].partition("nach oben")[0][1:].replace("* ", "").replace("* ", "").replace(" .", "")

        for ch in channels:
            x = int(pr.find(ch))
            line = pr[x:].partition("</a>")[0].replace(">", "").partition("<br/")[0]
            if not line == "":
                programm.append(line)
                
        self.programmbox("jetzt im Programm", '\n'.join(programm))
        
    def tv_programm_later(self):
        channels = ['Das Erste', 'ZDF', 'ZDFinfo', 'ZDFneo', 'MDR', 'Phoenix', 'RBB', 'BR', 'HR', 'SWR', 'NDR', 'WDR', 'Arte', '3sat', 'ARD alpha', 'KiKa', 'Sport 1', 'ORF 1', 'ORF 2', 'ORF 3', 'ORF Sport']

        url = "https://www.hoerzu.de/text/tv-programm/gleich.php"
        programm = []

        pr = request(method='GET', url = url).text.partition(".</H3>")[2].partition("nach oben")[0][1:].replace("* ", "").replace("* ", "").replace(" .", "")

        for ch in channels:
            x = int(pr.find(ch))
            line = pr[x:].partition("</a>")[0].replace(">", "").partition("<br/")[0]
            if not line == "":
                programm.append(line)
        self.programmbox("danach im Programm", '\n'.join(programm))
         
    def dragEnterEvent(self, event):
        event.acceptProposedAction()

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            url = event.mimeData().urls()[0].toString()
            print("neue URL abgelegt = ", url)
            self.link = url
            self.mediaPlayer.stop()
            self.mediaPlayer.setMedia(QMediaContent(QUrl(self.link)))
            self.mediaPlayer.play()
        elif event.mimeData().hasText():
            mydrop =  event.mimeData().text()
            if mydrop.startswith("http"):
                print("neuer Link abgelegt = ", mydrop)
                self.link = mydrop
                self.mediaPlayer.setMedia(QMediaContent(QUrl(self.link)))
                self.mediaPlayer.play()
        event.acceptProposedAction()
        

    def recfinished(self):
        print("Aufnahme beendet 1")

    def is_tool(self, name):
        tool = QStandardPaths.findExecutable(name)
        if tool != "":
            return True
        else:
            return False

    def getPID(self):
        print(self.process.pid(), self.process.processId() )

    def record_without_timer(self):
        if not self.recording_enabled == False:
            if QFile(self.outfile).exists:
                print("lösche Datei " + self.outfile) 
                QFile(self.outfile).remove
            else:
                print("Die Datei " + self.outfile + " existiert nicht") 
            self.recname = self.channelname
            self.showLabel()
            print("Aufnahme in /tmp")
            self.is_recording = True
            cmd = 'streamlink --force ' + self.link.replace("?sd=10&rebase=on", "") + ' best -o ' + self.outfile
            print(cmd)
            self.process.startDetached(cmd)

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
                self.lbl.hide()
                print("Aufnahme abgebrochen")

    def recordChannel(self):
        self.recname = self.channelname
        self.showLabel()
        cmd =  'timeout ' + str(self.tout) + ' streamlink --force ' + self.link.replace("?sd=10&rebase=on", "") + ' best -o ' + self.outfile
        print(cmd)
        print("Aufnahme in /tmp mit Timeout: " + str(self.tout))
        self.lbl.update()
        self.is_recording = True
        self.process.start(cmd)
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
            self.lbl.hide()
        else:
            self.lbl.hide()

    def stop_recording(self):
        print(self.process.state())
        if self.is_recording == True:
            print("Aufnahme wird gestoppt")
            QProcess().execute("killall streamlink")
            self.process.kill()
            self.is_recording = False
            if self.process.exitStatus() == 0:
                self.saveMovie()
        else:
            print("es wird gerade nicht aufgenommen")
            self.lbl.hide()
 
    def rec_finished(self):
        print("Aufnahme beendet")
        self.process.kill()

    def timer_finished(self):
        print("Timer beendet")
        self.is_recording = False
        self.process.kill()
        print("Aufnahme beendet")

        self.lbl.hide()
        self.saveMovie()

    def playURL(self):
        clip = QApplication.clipboard()
        self.link = clip.text()
        if not self.link.startswith("http"):
            self.mediaPlayer.setMedia(QMediaContent(QUrl.fromLocalFile(self.link)))
        else:
            self.mediaPlayer.setMedia(QMediaContent(QUrl(self.link)))
        self.mediaPlayer.play()

    def handleError(self):
        if not "Should no longer be called" in self.mediaPlayer.errorString():
            print("Fehler: " + self.mediaPlayer.errorString())
            self.msgbox("Fehler: " + self.mediaPlayer.errorString())

    def handleMute(self):
        if not self.mediaPlayer.isMuted():
            self.mediaPlayer.setMuted(True)
        else:
            self.mediaPlayer.setMuted(False)

    def handleAbout(self):
        QMessageBox.about(self, "TVPlayer2", self.myinfo)
        
    def tv_programm_tag(self):
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
        if "alpha" in ch:
            ch = "alpha"
        if ch =="SR":
            ch = "swr"
        if "ONE" in ch:
            ch = "one"
        tp = Tagesprogramm()
        msg = tp.getProgramm(ch)
        if not msg == None:
            self.programmbox("Tagesprogramm", msg)

    def handleFullscreen(self):
        if self.fullscreen == True:
            self.fullscreen = False
            print("kein Fullscreen")
        else:
            self.rect = self.geometry()
            self.showMaximized()
            QApplication.setOverrideCursor(Qt.ArrowCursor)
            self.fullscreen = True
            print("Fullscreen eingeschalter")
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
        self.mediaPlayer.stop()
        self.writeSettings()
        print("Auf Wiedersehen ...")
        app.quit()

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
        elif e.key() == Qt.Key_T:
            self.playTagesschau()
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
            if self.mediaPlayer.volume() < 100:
                self.mediaPlayer.setVolume(self.mediaPlayer.volume() + 5)
                print("Lautstärke:", self.mediaPlayer.volume())
        elif e.key() == Qt.Key_Down:
            if self.mediaPlayer.volume() > 5:
                self.mediaPlayer.setVolume(self.mediaPlayer.volume() - 5)
                print("Lautstärke:", self.mediaPlayer.volume())
        else:
            e.accept()

    def contextMenuRequested(self, point):
        self.channels_menu.exec_(self.mapToGlobal(point))
        
    def playFromKey(self, url):
        self.mediaPlayer.setMedia(QMediaContent(QUrl(url)))
        self.mediaPlayer.play()
        
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
                
    def playTagesschau(self):
        for x in range(len(self.default_list)):
            line = self.default_list[x].split(",")
            if line[0] == "ARD Tagesschau":
                self.link = line[1]
                self.playFromKey(self.link)
                self.channelname = "ARD Tagesschau"
                if self.channelname in self.channel_list:
                    self.default_key = self.channel_list.index(self.channelname)

    def play_Sport1(self):
        if not self.is_recording:
            self.lbl.hide()
        url = "https://tv.sport1.de/sport1/"
        r = get(url)
        myurl = r.text.partition('file: "')[2].partition('"')[0].replace("\n", "")
        print("grabbed url Sport1:", myurl)
        if not myurl =="":
            self.channelname = "Sport 1"
            self.mediaPlayer.setMedia(QMediaContent(QUrl(myurl)))
            self.link = myurl
            print("aktueller Sender:", self.channelname, "\nURL:", self.link)
            self.mediaPlayer.play()
            self.default_key = self.channel_list.index(self.channelname)

    def showLabel(self):
        self.lbl.show()

    def playTV(self):
        if not self.is_recording:
            self.lbl.hide()
        action = self.sender()
        self.link = action.data().replace("\n", "")
        self.channelname = action.text()
        if self.channelname in self.channel_list:
            self.default_key = self.channel_list.index(self.channelname)
        else:
            self.own_key = self.own_list.index(f"{self.channelname},{self.link}")
        print("aktueller Sender:", self.channelname, "\nURL:", self.link)
        self.mediaPlayer.setMedia(QMediaContent(QUrl(self.link)))
        self.mediaPlayer.play()
        

    def play_own(self, channel):
        if not channel > len(self.own_list) - 1:
            if not self.is_recording:
                self.lbl.hide()
            self.own_key = channel
            self.link = self.own_list[channel].split(",")[1]
            self.channelname = self.own_list[channel].split(",")[0]
            print("eigener Sender:", self.channelname, "\nURL:", self.link)
            self.mediaPlayer.setMedia(QMediaContent(QUrl(self.link)))
            self.mediaPlayer.play()
        else:
            print(f"Kanal {channel} ist nicht vorhanden")
            
            
    def play_next(self, channel):
        if not channel > len(self.default_list) - 1:
            if not self.is_recording:
                self.lbl.hide()
            self.default_key = channel
            self.link = self.default_list[channel].split(",")[1]
            self.channelname = self.default_list[channel].split(",")[0]
            print("aktueller Sender:", self.channelname, "\nURL:", self.link)
            self.mediaPlayer.setMedia(QMediaContent(QUrl(self.link)))
            self.mediaPlayer.play()
        else:
            self.play_next(0)
            
    def play_previous(self, channel):
        if not channel == 0:
            if not self.is_recording:
                self.lbl.hide()
            self.default_key = channel
            self.link = self.default_list[channel].split(",")[1]
            self.channelname = self.default_list[channel].split(",")[0]
            print("aktueller Sender:", self.channelname, "\nURL:", self.link)
            self.mediaPlayer.setMedia(QMediaContent(QUrl(self.link)))
            self.mediaPlayer.play()
        else:
            self.play_next(len(self.default_list))

    def closeEvent(self, event):
        event.accept()

    def msgbox(self, message):
        QMessageBox.warning(self, "Meldung", message)
        
    def programmbox(self, title, message):
        QMessageBox.information(self, title, message)

    def wheelEvent(self, event):
        mwidth = self.frameGeometry().width()
        mscale = event.angleDelta().y() / 6
        self.resize(mwidth + mscale, (mwidth + mscale) / ratio)
        event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() \
                      - QPoint(self.frameGeometry().width() / 2, \
                               self.frameGeometry().height() / 2))
            event.accept()

    def showColorDialog(self):
        if self.colorDialog is None:
            self.brightnessSlider = QSlider(Qt.Horizontal)
            self.brightnessSlider.setRange(-100, 100)
            self.brightnessSlider.setValue(self.videoWidget.brightness())
            self.brightnessSlider.sliderMoved.connect(
                    self.videoWidget.setBrightness)
            self.videoWidget.brightnessChanged.connect(
                    self.brightnessSlider.setValue)

            self.contrastSlider = QSlider(Qt.Horizontal)
            self.contrastSlider.setRange(-100, 100)
            self.contrastSlider.setValue(self.videoWidget.contrast())
            self.contrastSlider.sliderMoved.connect(self.videoWidget.setContrast)
            self.videoWidget.contrastChanged.connect(self.contrastSlider.setValue)

            self.hueSlider = QSlider(Qt.Horizontal)
            self.hueSlider.setRange(-100, 100)
            self.hueSlider.setValue(self.videoWidget.hue())
            self.hueSlider.sliderMoved.connect(self.videoWidget.setHue)
            self.videoWidget.hueChanged.connect(self.hueSlider.setValue)

            self.saturationSlider = QSlider(Qt.Horizontal)
            self.saturationSlider.setRange(-100, 100)
            self.saturationSlider.setValue(self.videoWidget.saturation())
            self.saturationSlider.sliderMoved.connect(
                    self.videoWidget.setSaturation)
            self.videoWidget.saturationChanged.connect(
                    self.saturationSlider.setValue)

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
        self.videoWidget.setBrightness(0)

        self.contrastSlider.setValue(0)
        self.videoWidget.setContrast(0)

        self.saturationSlider.setValue(0)
        self.videoWidget.setSaturation(0)

        self.hueSlider.setValue(0)
        self.videoWidget.setHue(0)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    mainWin = MainWindow()
    mainWin.show()
    sys.exit(app.exec_())
