#!/bin/sh
filename=$HOME/.local/share/LiveStream-TVPlayer-master/tv_listen
if [ -d "$filename" ]
then
    echo "$filename gefunden, kopiere nach /tmp"
    cp -rf $filename /tmp
else
    echo "$filename nicht gefunden"
fi
sharedapps=$HOME/.local/share/applications/
if [ -d "$sharedapps" ]
 then
    echo "$sharedapps gefunden"
else
    echo "$sharedapps nicht gefunden"
    mkdir $sharedapps
fi
echo "lösche TVPlayer2"
rm -rf ~/.local/share/LiveStream-TVPlayer-master
cd ~/.local/share/
echo "TVPlayer2 herunterladen ..."
wget https://github.com/Axel-Erfurt/LiveStream-TVPlayer-Deutsch/archive/master.zip
echo "TVPlayer2 extrahieren"
unzip -o master.zip
sleep 1
echo "zip Datei löschen"
rm master.zip
mv ~/.local/share/LiveStream-TVPlayer-Deutsch-master ~/.local/share/LiveStream-TVPlayer-master
rf=/tmp/tv_listen
if [ -d "$rf" ]
then
    echo "tv_listen wiederherstellen"
    cp $rf -rf $HOME/.local/share/LiveStream-TVPlayer-master
else
    echo "$rf nicht gefunden"
fi
desktopfile=$HOME/.local/share/applications/TVPlayer2.desktop
if [ -e "$desktopfile" ]
then
    echo "$desktopfile ist schon vorhanden"
else
    echo "$desktopfile nicht gefunden"
    cp $HOME/.local/share/LiveStream-TVPlayer-master/TVPlayer2.desktop $HOME/.local/share/applications
fi
rm ~/Downloads/TVPlayerInstall.sh
echo "Sender aktualisieren ... "
python3 ~/.local/share/LiveStream-TVPlayer-master/query_mv.py ~/.local/share/LiveStream-TVPlayer-master/
echo "TVPlayer2 starten ... "
python3 ~/.local/share/LiveStream-TVPlayer-master/TVPlayer2.py
