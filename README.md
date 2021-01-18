# LiveStream-TVPlayer-Deutsch :de:


![screenshot](https://github.com/Axel-Erfurt/LiveStream-TVPlayer-Deutsch/blob/master/screenshot.png)

TVPlayer2 ist ein Player zum Abspielen von TV Streams.

### Voraussetzungen

- [python3](https://wiki.ubuntuusers.de/Python/) >= 3.6
- PyQt5
- [mpv](https://wiki.ubuntuusers.de/mpv/)
- [ffmpeg](https://wiki.ubuntuusers.de/FFmpeg/) (zum Aufnehmen des TV Streams)

### PyQt5

PyQt5 Abhängige Pakete kann man über die Paketquellen installieren mit

```shell
sudo apt-get install python3-pyqt5
```

### mpv

```shell
sudo apt-get install mpv
```


### Installation TVPlayer2

im Terminal folgenden Befehl ausführen:

```shell
wget 'https://raw.githubusercontent.com/Axel-Erfurt/LiveStream-TVPlayer-Deutsch/master/TVPlayerInstall.sh' -O ~/Downloads/TVPlayerInstall.sh && chmod +x ~/Downloads/TVPlayerInstall.sh && ~/Downloads/TVPlayerInstall.sh
```

Damit wird die aktuelle Version von github heruntergeladen und im Ordner ~/.local/share/ gespeichert.

Ein Starter (TVPlayer2.desktop) wird in ~/.local/share/applications erstellt
Programm starten

Aus dem Startmenu (TVPlayer2)

oder im Terminal mit

```shell
cd ~/.local/share/LiveStream-TVPlayer-master && python3 ./TVPlayer2mpv.py
```

### Deinstallation

Dazu im Terminal folgende Befehle ausführen

```shell
rm -rf ~/.local/share/LiveStream-TVPlayer-master 
```
```shell
rm ~/.local/share/applications/TVPlayer2.desktop
```
```shell
rm -rf ~/.config/TVPlayer2
```

### Bedienung

Die Bedienung erfolgt über das Kontextmenu oder Shortcuts.

Im Kontextmenu erscheinen die Sender in SD Auflösung (640x360). Im Submenu HD erscheinen die Sender in der Auflösung (1280x720)

Wenn ffmpeg vorhanden ist kann mit oder ohne Timer aufgenommen werden.

Im Ordner ~/.local/share/LiveStream-TVPlayer-master/ können Playlisten hinzugefügt oder entfernt werden.

Sie müssen die Dateiendung .txt haben.

Die .txt Datei sollte das übliche Format haben. *Name,URL*

Beispiel:

```
ARD,http://mcdn.daserste.de/daserste/de/master.m3u8
```

Der Dateiname wird zum Menupunkt, z.B. Favoriten.txt erscheint als Favoriten im Menu.

In diesem Menu liegen dann alle Sender die in der Datei gespeichert sind.



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

### libmpv

```shell
sudo apt-get install libmpv
```
