#!/usr/bin/python3
# -*- coding: utf-8 -*-
#############################################################################

from PyQt5.QtCore import (QPoint, QRect, Qt, QUrl, QProcess, QFile, QDir, QTimer, QSize, QEvent, 
                                                    QStandardPaths, QFileInfo, QCoreApplication)
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (QAction, QApplication, QMainWindow, QMessageBox, 
                                                    QMenu, QWidget, QInputDialog, QLineEdit, QFileDialog, QLabel, 
                                                    QFormLayout, QSlider, QPushButton, QDialog)
from PyQt5.QtMultimedia import QMediaContent, QMediaPlayer
from PyQt5.QtMultimediaWidgets import QVideoWidget

import os
from time import sleep
import subprocess
import sys
from requests import get as getURL

mytv = "tv-symbolic"
mybrowser = "video-television"
ratio = 1.777777778

class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()

        self.colorDialog = None
        self.urlList = []
        self.link = ""
        self.menulist = []
        self.recording_enabled = False
        self.is_recording = False
        self.timeout = "60"
        self.tout = 60
        self.outfile = "/tmp/TV.mp4"
        self.myARD = ""
        self.channelname = ""

        self.channels_menu = QMenu()
        self.c_menu = self.channels_menu.addMenu(QIcon.fromTheme(mytv), "Sender")

        self.process = QProcess()
        self.process.started.connect(self.getPID)
        self.process.finished.connect(self.timer_finished)
        self.process.finished.connect(self.recfinished)

        self.mediaPlayer = QMediaPlayer(None, QMediaPlayer.StreamPlayback)
        self.mediaPlayer.setVolume(90)
        print("Volume:", self.mediaPlayer.volume())
        self.mediaPlayer.error.connect(self.handleError)
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
        self.lbl.setGeometry(10,10, 70, 16)
        self.lbl.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        self.lbl.setStyleSheet("background: #2e3436; color: #ef2929; font-size: 8pt;")
        self.lbl.setText("Aufnahme ...")
        self.lbl.hide()

        self.root = QFileInfo.path(QFileInfo(QCoreApplication.arguments()[0]))
        print("Programmordner ist: " + self.root)

        self.fullscreen = False

        self.setAttribute(Qt.WA_NoSystemBackground, True)
        self.setMinimumSize(320, 180)
        self.setGeometry(0, 0, 480, 480 / ratio)

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        screen = QApplication.primaryScreen()
        screenGeometry = QRect(screen.geometry())
        screensize = QPoint(screenGeometry.width(), screenGeometry.height())
        p = QPoint(self.mapToGlobal(QPoint(screensize)) -
                    QPoint(self.size().width() + 2, self.size().height() + 2))
        self.move(p)
    
        screenGeometry = QApplication.desktop().availableGeometry()
        screenGeo = screenGeometry.bottomRight()
        self.move(screenGeo)

        self.setWindowTitle("TV Player & Recorder")
        self.setWindowIcon(QIcon.fromTheme("multimedia-video-player"))

        self.myinfo = "<h1>TVPlayer2</h1>©2018<br><a href='https://goodoldsongs.jimdofree.com/'>Axel Schneider</a>\
                        <br><br>mediaterm von <a href='http://martikel.bplaced.net/skripte1/mediaterm.html'>Martin O'Connor</a>\
                        <h3>Tastaturkürzel:</h3>q = Beenden<br>f = toggle Fullscreen<br>\
                        u = Url aus dem Clipboard abspielen<br>\
                        Mausrad = Größe ändern<br>\
                        ↑ = lauter<br>\
                        ↓ = leiser<br>\
                        m = Ton an/aus<br>\
                        h = Mauszeiger an / aus<br>\
                        r = Aufnahme mit Timer<br>\
                        w = Aufnahme ohne Timer<br>s = Aufnahme beenden"
        print("Willkommen beim TV Player & Recorder")
        if self.is_tool("streamlink"):
            print("streamlink gefunden\nAufnahme möglich")
            self.recording_enabled = True
        else:
            self.msgbox("streamlink nicht gefunden\nkeine Aufnahme möglich")
        self.getLists()
        self.makeMenu()
        if not self.myARD == "":
            self.play_ARD()
        
    def getMenu(self):
        chFolder = self.root + "/tv_listen/"
        pList = [f for f in os.listdir(chFolder) if os.path.isfile(os.path.join(chFolder, f))]
        menuList = []
        
        for x in range(len(pList)):
            ft = f"{chFolder}{pList[x]}"
            name = os.path.splitext(os.path.basename(ft))[0]
            text = open(ft, 'r').read()
            
            mlist = text.splitlines()
            for x in range(len(mlist)):
                if "RESOLUTION=640" in mlist[x]:
                    menuList.append(f"{name.upper()},{mlist[x+1]}")
                    if name.upper() == "ARD":
                        self.myARD = (f"{name.upper()},{mlist[x+1]}")
                    if name.upper() == "ZDF":
                        self.myZDF = (f"{name.upper()},{mlist[x+1]}")
                    if name.upper() == "MDR THÜRINGEN":
                        self.myMDR = (f"{name.upper()},{mlist[x+1]}")
                    if name.upper() == "PHOENIX":
                        self.myPhoenix = (f"{name.upper()},{mlist[x+1]}")
                    if name.upper() == "ZDF INFO":
                        self.myZDFInfo = (f"{name.upper()},{mlist[x+1]}")
                    break
            for x in range(len(mlist)):
                if "RESOLUTION=1280" in mlist[x]:
                    menuList.append(f"{name.upper()} HD,{mlist[x+1]}")
                    break
                elif "RESOLUTION=852" in mlist[x]:
                    menuList.append(f"{name.upper()} HD,{mlist[x+1]}")
                    break
        menuList.sort(key=lambda x:x.partition(",")[0].upper()[:5])
        return menuList


    def makeMenu(self):
        pList = self.getMenu()
        hdm = self.c_menu.addMenu(QIcon.fromTheme("computer"), "HD")
        for playlist in pList:
            name = playlist.partition(",")[0]
            url = playlist.partition(",")[2]
            if not "HD" in name:
                a = QAction(name, self, triggered=self.playTV)
                a.setIcon(QIcon.fromTheme(mybrowser))
                a.setData(url)
                rm = self.c_menu.addAction(a)
            else:
                a = QAction(name, self, triggered=self.playTV)
                a.setIcon(QIcon.fromTheme(mybrowser))
                a.setData(url)
                rm = hdm.addAction(a)

        a = QAction(QIcon.fromTheme(mybrowser), "Sport1 Live", self, triggered=self.play_Sport1)
        self.c_menu.addAction(a)
    
    def dragEnterEvent(self, event):
        if (event.mimeData().hasUrls()):
            event.acceptProposedAction()

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            url = event.mimeData().urls()[0].toString()
            print("url = ", url)
            self.mediaPlayer.stop()
            self.mediaPlayer.setMedia(QMediaContent(QUrl(url)))
            self.mediaPlayer.play()
        elif event.mimeData().hasText():
            mydrop =  event.mimeData().text()
            if "http" in mydrop:
                print("stream url = ", mydrop)
                self.mediaPlayer.setMedia(QMediaContent(QUrl(mydrop)))
                self.mediaPlayer.play()
        event.acceptProposedAction()
        

    def recfinished(self):
        print("Aufnahme beendet 1")

    def is_tool(self, name):
        tool = QStandardPaths.findExecutable(name)
        if tool is not "":
            print(tool)
            return True
        else:
            return False

    def getPID(self):
        print(self.process.pid(), self.process.processId() )

    def recordNow2(self):
        if not self.recording_enabled == False:
            if QFile(self.outfile).exists:
                print("lösche Datei " + self.outfile) 
                QFile(self.outfile).remove
            else:
                print("Die Datei " + self.outfile + " existiert nicht") 
            self.showLabel()
            print("Aufnahme in /tmp")
            self.is_recording = True
            cmd = 'streamlink --force ' + self.link.replace("?sd=10&rebase=on", "") + ' best -o ' + self.outfile
            print(cmd)
            self.process.startDetached(cmd)

    def recordNow(self):
        if not self.recording_enabled == False:
            if QFile(self.outfile).exists:
                print("lösche Datei " + self.outfile) 
                QFile(self.outfile).remove
            else:
                print("Die Datei " + self.outfile + " existiert nicht") 
            #self.showLabel()
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
        self.showLabel()
        cmd =  'timeout ' + str(self.tout) + ' streamlink --force ' + self.link.replace("?sd=10&rebase=on", "") + ' best -o ' + self.outfile
        print(cmd)
        print("Aufnahme in /tmp mit Timeout: " + str(self.tout))
        self.lbl.update()
        self.is_recording = True
        self.process.start(cmd)
################################################################

    def saveMovie(self):
        #self.msgbox("recording finished")
        self.fileSave()

    def fileSave(self):
        infile = QFile(self.outfile)
        path, _ = QFileDialog.getSaveFileName(self, "Speichern als...", QDir.homePath() + "/Videos/" + self.channelname + ".mp4",
            "Video (*.mp4)")
        #path = QDir.homePath() + "/Videos/TVRecording.mp4"
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
#        self.timer_finished()

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
        if not str(self.mediaPlayer.errorString()) == "QWidget::paintEngine: Should no longer be called":
            print("Fehler: " + self.mediaPlayer.errorString())
            self.msgbox("Fehler: " + self.mediaPlayer.errorString())

    def handleMute(self):
        if not self.mediaPlayer.isMuted():
            self.mediaPlayer.setMuted(True)
        else:
            self.mediaPlayer.setMuted(False)

    def handleAbout(self):
        msg = QMessageBox.about(self, "TVPlayer2", self.myinfo)

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
        print("Auf Wiedersehen ...")
        app.quit()

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Q:
            self.handleQuit()
        elif e.key() == Qt.Key_H:
            self.handleCursor()
        elif e.key() == Qt.Key_F:
            self.handleFullscreen()
        elif e.key() == Qt.Key_M:
            self.handleMute()
        elif e.key() == Qt.Key_I:
            self.handleAbout()
        elif e.key() == Qt.Key_U:
            self.playURL()
        elif e.key() == Qt.Key_R:
            self.recordNow()
        elif e.key() == Qt.Key_S:
            self.stop_recording()
        elif e.key() == Qt.Key_W:
            self.recordNow2()
        elif e.key() == Qt.Key_C:
            self.showColorDialog()
        elif e.key() == Qt.Key_1:
            self.play_ARD()
        elif e.key() == Qt.Key_2:
            self.play_ZDF()
        elif e.key() == Qt.Key_3:
            self.play_MDR()
        elif e.key() == Qt.Key_4:
            self.play_Phoenix()
        elif e.key() == Qt.Key_5:
            self.play_Sport1()
        elif e.key() == Qt.Key_Z:
            self.play_Info()
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

    def getLists(self):
        the_folder = self.root + "/tv_listen"
        for entry in os.listdir(the_folder):
            if str(entry).endswith(".m3u8"):
                self.urlList.append(the_folder + "/" + str(entry))
        self.urlList.sort()

    def contextMenuRequested(self, point):
        self.channels_menu.clear()
        self.channels_menu.addMenu(self.c_menu)
        if not self.recording_enabled == False:
            self.channels_menu.addSection("Aufnahme")
    
            tv_record = QAction(QIcon.fromTheme("media-record"), "Aufnahme mit Timer (r)", triggered = self.recordNow)
            self.channels_menu.addAction(tv_record)

            tv_record2 = QAction(QIcon.fromTheme("media-record"), "Aufnahme ohne Timer (w)", triggered = self.recordNow2)
            self.channels_menu.addAction(tv_record2)

            tv_record_stop = QAction(QIcon.fromTheme("media-playback-stop"), "Aufnahme beenden (s)", triggered = self.stop_recording)
            self.channels_menu.addAction(tv_record_stop)
    
            self.channels_menu.addSeparator()

        self.channels_menu.addSeparator()

        about_action = QAction(QIcon.fromTheme("help-about"), "Info (i)", triggered = self.handleAbout, shortcut = "i")
        self.channels_menu.addAction(about_action)

        self.channels_menu.addSeparator()

        url_action = QAction(QIcon.fromTheme(mybrowser), "URL vom Clipboard spielen (u)", triggered = self.playURL)
        self.channels_menu.addAction(url_action)

        self.channels_menu.addSection("Einstellungen")

        color_action = QAction(QIcon.fromTheme("preferences-color"), "Bildeinstellungen (c)", triggered = self.showColorDialog)
        self.channels_menu.addAction(color_action)

        self.channels_menu.addSeparator()
        
        self.updateAction = QAction(QIcon.fromTheme("download"), "Sender aktualisieren", triggered = self.updateChannels)
        self.channels_menu.addAction(self.updateAction)
        
        self.channels_menu.addSeparator()

        quit_action = QAction(QIcon.fromTheme("application-exit"), "Beenden (q)", triggered = self.handleQuit)
        self.channels_menu.addAction(quit_action)

        self.channels_menu.exec_(self.mapToGlobal(point))
        
    def updateChannels(self):
        update_script = f"{os.path.join(self.root, 'query_mv.py')}"
        print(update_script)
        if os.path.isfile(update_script):
            print("starting", update_script)
            subprocess.call(["python3", update_script, self.root])
            self.c_menu.clear()
            self.makeMenu()
            self.msgbox("aktualisierte Sender sind verfügbar")

    def play_ARD(self):
        self.lbl.hide()
        self.link = self.myARD.partition(",")[2]
        self.channelname = "ARD"
        self.mediaPlayer.setMedia(QMediaContent(QUrl(self.link)))
        self.mediaPlayer.play()

    def play_ZDF(self):
        self.lbl.hide()
        self.link = self.myZDF.partition(",")[2]
        self.channelname = "ZDF"
        self.mediaPlayer.setMedia(QMediaContent(QUrl(self.link)))
        self.mediaPlayer.play()

    def play_MDR(self):
        self.lbl.hide()
        self.link = self.myMDR.partition(",")[2]
        self.channelname = "MDR"
        self.mediaPlayer.setMedia(QMediaContent(QUrl(self.link)))
        self.mediaPlayer.play()

    def play_Info(self):
        self.lbl.hide()
        self.link = self.myZDFInfo.partition(",")[2]
        self.channelname = "ZDF Info"
        self.mediaPlayer.setMedia(QMediaContent(QUrl(self.link)))
        self.mediaPlayer.play()

    def play_Phoenix(self):
        self.lbl.hide()
        self.link = self.myPhoenix.partition(",")[2]
        self.channelname = "Phoenix"
        self.mediaPlayer.setMedia(QMediaContent(QUrl(self.link)))
        self.mediaPlayer.play()

    def play_Sport1(self):
        self.lbl.hide()
        url = "https://tv.sport1.de/sport1/"
        r = getURL(url)
        myurl = r.text.partition('file: "')[2].partition('"')[0]
        print("grabbed url Sport1:", myurl)
        if not myurl =="":
            self.channelname = "Sport1"
            self.mediaPlayer.setMedia(QMediaContent(QUrl(myurl)))
            self.link = myurl
            self.mediaPlayer.play()

    def showLabel(self):
        self.lbl.show()

    def playTV(self):
        self.lbl.hide()
        action = self.sender()
        self.link = action.data()
        self.channelname = action.text()
        print("aktueller Sender:", self.channelname)
        self.mediaPlayer.setMedia(QMediaContent(QUrl(self.link)))
        self.mediaPlayer.play()

    def closeEvent(self, event):
        event.accept()

    def msgbox(self, message):
        QMessageBox.warning(self, "Meldung", message)

    def wheelEvent(self, event):
        mwidth = self.frameGeometry().width()
        mheight = self.frameGeometry().height()
        #ratio = 1.777777778
        mleft = self.frameGeometry().left()
        mtop = self.frameGeometry().top()
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