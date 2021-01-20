#!/bin/sh
echo "temporäres Backup anlegen"
mkdir -p /tmp/TVPlayerBackup
cp $HOME/.local/share/LiveStream-TVPlayer-master/*.txt /tmp/TVPlayerBackup
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
echo "Listen wiederherstellen"
cp /tmp/TVPlayerBackup/*.txt $HOME/.local/share/LiveStream-TVPlayer-master
cp $HOME/.local/share/LiveStream-TVPlayer-master/TVPlayer2.desktop $HOME/.local/share/applications
mkdir -p ~/.icons && cp ~/.local/share/LiveStream-TVPlayer-master/icon2.png ~/.icons/ 
rm ~/Downloads/TVPlayerInstall.sh
