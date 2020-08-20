#!/bin/sh
echo "kopiere tv_listen nach /tmp"
cp -rf ~/.local/share/LiveStream-TVPlayer-master/tv_listen /tmp
echo "alte Listen umwandeln ..."
~/Downloads
wget https://raw.githubusercontent.com/Axel-Erfurt/LiveStream-TVPlayer-Deutsch/master/tv_listen_umwandeln.py
sleep 1
python3 ~/Downloads/tv_listen_umwandeln.py
echo "neue Version herunterladen ..."
wget 'https://raw.githubusercontent.com/Axel-Erfurt/LiveStream-TVPlayer-Deutsch/master/TVPlayerInstall.sh'
chmod +x ./TVPlayerInstall.sh
./TVPlayerInstall.sh
echo "tv_listen Ordner wiederherstellen ..."
mv /tmp/tv_listen ~/.local/share/LiveStream-TVPlayer-master/tv_listen
echo "TVPlayer2Update.sh entfernen"
rm ~/Downloads/TVPlayer2Update.sh
echo "fertg!"

