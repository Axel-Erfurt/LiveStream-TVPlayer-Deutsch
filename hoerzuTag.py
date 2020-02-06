#!/usr/bin/python3
# -*- coding: utf-8 -*-
##############################################
### ©2020 Axel Schneider
### https://github.com/Axel-Erfurt
### Dank an Hoerzu für die TV-Daten
### http://mobile.hoerzu.de/programbystation
##############################################
import requests
import time
import locale
from datetime import date
import webbrowser
import os

### html header
header = """<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0//EN" "http://www.w3.org/TR/REC-html40/strict.dtd">
              <html><head><meta name="qrichtext" content="1" /><meta http-equiv="Content-Type" \
              content="text/html; charset=UTF-8" /><style type="text/css">
              p, li { white-space: pre-wrap; }
              </style></head>
              <style>
              table {width: auto; border-style: ridge;  border-width: 12px; border-color: #729fcf; \
              background-color: #2e3436; margin-top: 10px;}
              th  {border:2px inset #d3d7cf; padding-left:10px; color: #729fcf;}   
              td {border:2px inset #d3d7cf; padding-left:10px; padding-right:10px; \
              color: #d3d7cf; overflow:hidden; table-layout:fixed;}
              body {width: auto; background-color: #2e3436;font-family:'Noto Sans'; \
              font-size:13px; font-weight:400; font-style:normal;}
              hr {border-style: ridge;}</style>"""

### html body
body = """</p></body></html>"""

loc = locale.getlocale()
locale.setlocale(locale.LC_ALL, loc)
dt = f"{date.today():%-d.%B %Y}"
titleList = []

### Liste der Sender mit ID
### Die ID eines Senders kann man herausfinden auf 'view-source:http://test.mobil.hoerzu.de/tv-sender/'
### Zum Entfernen eines Sender das Paar entfernen
dictList = {'ard': 71, 'zdf': 37, 'zdf neo': 659, 'zdf info': 276, 'arte': 58, 'wdr': 46, 'ndr': \
            47, 'mdr': 48, 'hr': 49, 'swr': 10142, 'br': 51, 'rbb': 52, '3sat': 56,'alpha': 104, \
            'kika': 57, 'phoenix': 194, 'tagesschau 24': 100, 'one': 146, 'rtl': 38, 'sat 1': 39, \
            'pro 7': 40,'rtl plus': 12033, 'kabel 1': 44, 'rtl 2': 41, 'vox': 42, 'rtl nitro': 763, \
            'n24 doku': 12045, 'kabel 1 doku': 12043, 'sport 1': 64, 'super rtl': 43, \
            'sat 1 gold': 774, 'vox up': 12125, 'sixx': 694, 'servus tv': 660, \
            'welt': 175, 'orf 1': 54, 'orf 2': 55, 'orf 3': 56, 'tele 5': 277, '7maxx': 783, \
            'dmaxx': 507, 'dw': 300, 'fox': 565, 'srf 1': 59, 'srf 2': 60}


myday = f"{date.today():%d}"
print("Tag:", myday)

### json von Hoerzu laden
response = requests.get('http://mobile.hoerzu.de/programbystation')
response_json = response.json()

### Daten jedes in dictList enthaltenen Senders verarbeiten und zu HTML konvertieren
def getValues(id):
    for ch in dictList:                                                                                    
        titleList.append(f'<a style="text-decoration: none;" href="#{ch}">\
                        <font color="#729fcf">{ch.upper()}</font>&nbsp;&nbsp;</a>')
    titleList.append(f'<a style="text-decoration: none;" \
                        href="https://www.hoerzu.de/text/tv-programm/jetzt.php" target="_blank">\
                        <font color="#73d216">Jetzt im TV</font>&nbsp;&nbsp;</a>')
    titleList.append(f'<a style="text-decoration: none;" \
                        href="https://www.hoerzu.de/text/tv-programm/gleich.php" \
                        target="_blank"><font color="#d3d7cf">Danach im TV</font>&nbsp;&nbsp;</a>')
    titleList.append(f'<a style="text-decoration: none;" \
                        href="https://www.hoerzu.de/text/tv-programm/tipps.php" \
                        target="_blank"><font color="#c4a000">TV Tipps</font>&nbsp;&nbsp;</a>')                        
                        
    
    for i in response_json:
        if i['id'] == id:
            plist = []
            pmlist = []
            pmdlist = []
            pr = i['broadcasts']
            for a in pr:
                p = ""
                pm = ""
                title = a.get('title')
                st = a.get('startTime')
                d = a.get('duration')
                duration = '{:02d}:{:02d}'.format(*divmod(int(d), 60))
                start = time.strftime("%-H:%M", time.localtime(st))
                day = time.strftime("%d", time.localtime(int(st)))
                titleList.append("<tr>")
                titleList.append("<td>")                
                if day == myday and int(start.replace(":", "")) > 529 and int(start.replace(":", "")) < 1600:
                    p = f"{start} {title}<br>"
                    plist.append(p)
                if day == myday and int(start.replace(":", "")) >= 1599 and int(start.replace(":", "")) < 2359:
                    pm = f"{start} {title}<br>"  
                    pmlist.append(pm)   
                if not day == myday:
                    pmd = f"{start} {title}<br>"  
                    pmdlist.append(pmd) 
            
            pml = '\n'.join(pmlist)
            pl = '\n'.join(plist)
            pmld = '\n'.join(pmdlist)
            
            titleList.append('<center><table>')
                                
            titleList.append(f"<tr><th align='left'>5.30 Uhr - 16 Uhr</th>\
                            <th align='left'>16 Uhr - 24 Uhr</th>\
                            <th align='left'>24 Uhr - 5.30 Uhr</th></tr><tr><td>\
                            {pl}</font></td><td>\
                            {pml}</font></td><td>\
                            {pmld}</font></td></tr>\
                            </table></center>")

### Gesamtliste erstellen
def makeList():
    print("Kanäle:", len(dictList))
    titleList.append(header)
    m = f"<center><font color='#729fcf'><h4><i>{dt}</i></h4></font></center>"
    titleList.append('<p style="text-align: center; font-size: 30px; \
                        line-height: 1px; color: #babdb6;text-shadow: \
                        1px 1px 1px #555753;">TV Programm</p>')
    titleList.append(m)
    titleList.append('<hr color="#729fcf"></hr>')
    for ch in dictList:
        titleList.append(f'<center><font color="#d3d7cf"><h2 padding-bottom="0" margin-bottom="0" \
                         id="{ch}"><a href="#"></a>&nbsp;&nbsp;&nbsp;&nbsp;{ch.upper()} \
                         &nbsp;&nbsp;&nbsp;&nbsp;<a href="#"></a></h2></font></center>')
        titleList.append('<hr color="#729fcf"></hr>')
        r = getValues(dictList.get(ch))
    
    
    titleList.append(body)
    t = '\n'.join(titleList)

    ### temporäre Datei erstellen in /tmp
    with open('/tmp/tagesprogramm.html', 'w') as f:
        url = 'file://' + f.name
        f.write(t)
        f.close()
    ### mit default Browser öffnen
    webbrowser.open(url)

### alles abarbeiten    
makeList()
