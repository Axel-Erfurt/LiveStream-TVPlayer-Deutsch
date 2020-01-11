# LiveStream-TVPlayer-Deutsch

![screenshot](https://github.com/Axel-Erfurt/LiveStream-TVPlayer-Deutsch/blob/master/screenshot.png)

TVPlayer2 ist ein Player zum Abspielen von TV Streams.

### Voraussetzungen

- python3
- PyQt5
- streamlink (zum Aufnehmen des TV Streams)
- gstreamer

### PyQt5

PyQt5 Abhängige Pakete kann man über die Paketquellen installieren mit

> sudo apt-get install python3-pyqt5 python3-pyqt5.qtmultimedia libqt5multimedia5-plugins  

### Gstreamer

Zur Nutzung müssen noch folgende zusätzliche Abhängigkeiten installiert werden.

> sudo apt-get install gstreamer1.0-vaapi libvdpau-va-gl1 gstreamer1.0-libav 

### streamlink

zur Aufnahme des aktuellen Senders (optional)

> sudo apt-get install streamlink 

### Installation TVPlayer2

im Terminal folgenden Befehl ausführen:

> wget 'https://raw.githubusercontent.com/Axel-Erfurt/LiveStream-TVPlayer-Deutsch/master/TVPlayerInstall.sh' -O ~/Downloads/TVPlayerInstall.sh && chmod +x ~/Downloads/TVPlayerInstall.sh && ~/Downloads/TVPlayerInstall.sh

Damit wird die aktuelle Version von github heruntergeladen und im Ordner ~/.local/share/ gespeichert.

Ein Starter (TVPlayer2.desktop) wird in ~/.local/share/applications erstellt
Programm starten

Aus dem Startmenu (TVPlayer2)

oder im Terminal mit

> cd ~/.local/share/LiveStream-TVPlayer-master && python3 ./TVPlayer2.py 

### Deinstallation

Dazu im Terminal folgendes eingeben

> cd ~/.local/share/ && rm -rf LiveStream-TVPlayer-master 

### Bedienung

Die Bedienung erfolgt über das Kontextmenu oder Shortcuts.

Im Kontextmenu erscheinen die Sender in SD Auflösung (640x360). Im Submenu HD erscheinen die Sender in der Auflösung (1280x720)

Wenn streamlink vorhanden ist kann mit oder ohne Timer aufgenommen werden.

Im Ordner ~/.local/share/LiveStream-TVPlayer-master/tv_listen können m3u8 Playlisten hinzugefügt ode entfernt werden.

* Zum Entfernen eines Sender einfach die m3u8 Datei löschen.

Die m3u8 Datei sollte das übliche Format haben.

Beispiel:

#EXTM3U
#EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=184000,RESOLUTION=320x180,CODECS="avc1.66.30, mp4a.40.2"
http://daserstehdde-lh.akamaihd.net/i/daserstehd_de@629196/index_184_av-p.m3u8?sd=10&rebase=on
#EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=3776000,RESOLUTION=1280x720,CODECS="avc1.64001f, mp4a.40.2"
http://daserstehdde-lh.akamaihd.net/i/daserstehd_de@629196/index_3776_av-b.m3u8?sd=10&rebase=on

Der Dateiname wird zum Menupunkt, z.B. zdf info.m3u8 erscheint als ZDF INFO im Menu.

Über das Kontextmenü Sender aktualisieren 🇩🇪 können die Sender der öffentlich rechtlichen deutschen Sender aktualisiert werden.

Dazu werden mittels der MediathekView API die aktuellen Links geholt.

### Shortcuts

- Q 	Beenden
- F 	Fullscreen an / aus
- M 	Stummschalten an / aus
- C 	Einstellungen Farbe / Helligkeit / Kontrast
- U 	URL aus der Zwichenablage abspielen
- H 	Mauszeiger an / aus
- R 	Aufnahme starten mit Timer (90m bedeutet 90 Minuten)
- W 	Aufnahme starten ohne Timer
- S 	Aufnahme stoppen
- ↑ 	lauter
- ↓ 	leiser 

[Download 64bit App Ubuntu/Mint 🇩🇪](https://www.dropbox.com/s/mklr44bcu92kc1g/TVPlayer2_64_deutsch.tar.gz?dl=1)

* letztes Update 10.Januar 2020 18:05

entpacken und TVPlayer2 im entpackten Ordner starten.
