#!/usr/bin/python3
# -*- coding: utf-8 -*-
import requests
import time
import locale
from datetime import date
import webbrowser
import tempfile

header = """<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0//EN" "http://www.w3.org/TR/REC-html40/strict.dtd">
<html><head><meta name="qrichtext" content="1" /><meta http-equiv="Content-Type" content="text/html; charset=UTF-8" /><style type="text/css">
p, li { white-space: pre-wrap; }
</style></head>
<body style="background-color: #d3d7cf;font-family:'Noto Sans'; font-size:9pt; font-weight:400; font-style:normal;">
<p style=" margin-top:10px; margin-bottom:0px; margin-left:10px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">"""

body = """</p></body></html>"""

loc = locale.getlocale()
locale.setlocale(locale.LC_ALL, loc)
dt = date.today().strftime("%-d.%B %Y")
titleList = []

          
dictList = {'ard': 71, 'zdf': 37, 'zdf neo': 659, 'zdf info': 276, 'arte': 58, 'wdr': 46, 'ndr': \
            47, 'mdr': 48, 'hr': 49, 'swr': 10142, 'br': 51, 'rbb': 52, '3sat': 56,'alpha': 104, \
            'kika': 57, 'phoenix': 194, 'tagesschau 24': 100, 'one': 146, 'rtl': 38, 'sat 1': 39, \
            'pro 7': 40,'rtl plus': 12033, 'kabel 1': 44, 'rtl 2': 41, 'vox': 42, 'rtl nitro': 763, \
            'n24 doku': 12045, 'kabel 1 doku': 12043, 'sport 1': 64, 'super rtl': 43, \
            'sat 1 gold': 774, 'vox up': 12125, 'sixx': 694, 'servus tv': 660, \
            'welt': 175, 'orf 1': 54, 'orf 2': 55, 'orf 3': 56}


response = requests.get('http://mobile.hoerzu.de/programbystation')
response_json = response.json()

def getURL(id):
    for ch in dictList:
        titleList.append((f'<a style="text-decoration: none" padding-bottom="0" margin-bottom="0" href="#{ch}">\
                        <font color="#8f5902">{ch.upper()}</font>&nbsp;&nbsp;</a>'))
    titleList.append('<br><br>')
    for i in response_json:
        if i['id'] == id:
            pr = i['broadcasts']
            for a in pr:
                title = a.get('title')
                st = a.get('startTime')
                d = a.get('duration')
                duration = '{:02d}:{:02d}'.format(*divmod(int(d), 60))
                start = time.strftime("%-H:%M", time.localtime(st))
                p = f"{start} {title}"
                if int(start.replace(":", "")) >= 0 and int(start.replace(":", "")) < 900:
                    titleList.append(f"<font color='#0a4012'>{start} {title}&nbsp;({duration})</font><br>")
                elif int(start.replace(":", "")) > 899 and int(start.replace(":", "")) < 1400:
                    titleList.append(f"<font color='#136258'>{start} {title}&nbsp;({duration})</font><br>")
                elif int(start.replace(":", "")) > 1399 and int(start.replace(":", "")) < 1700:
                    titleList.append(f"<font color='#204a87'>{start} {title}&nbsp;({duration})</font><br>")
                elif int(start.replace(":", "")) > 1699 and int(start.replace(":", "")) < 2015:
                    titleList.append(f"<font color='#8f5902'>{start} {title}&nbsp;({duration})</font><br>")
                elif start == "20:15":
                    titleList.append(f"<font color='#982727'><b>{start} {title}&nbsp;({duration})</b></font><br>")
                elif int(start.replace(":", "")) > 2015 and int(start.replace(":", "")) < 2359:
                    titleList.append(f"<font color='#56296f'>{start} {title}&nbsp;({duration})</font><br>")
                else:
                    titleList.append(f"<font color='#3e465d'>{start} {title}&nbsp;({duration})</font><br>")



def makeList():
    print("Kanäle:", len(dictList))

    for ch in dictList:
        titleList.append(f'<font color="#0a4012"><h2 padding-bottom="0" margin-bottom="0" \
                         id="{ch}"><a href="#"></a>&nbsp;&nbsp;&nbsp;&nbsp;{ch.upper()} \
                         &nbsp;&nbsp;&nbsp;&nbsp;<a href="#"></a></h2></font>')
        titleList.append('<hr color="#8f5902"></hr>')
        r = getURL(dictList.get(ch))

    t = '\n'.join(titleList)


    with open('/tmp/tagesprogramm.html', 'w') as f:
        url = 'file://' + f.name
        f.write(header)
        f.write('<hr color="#8f5902"></hr>')
        f.write(f"<font color='#3e465d'><h4><i>TV Programm vom {dt}</i></h4></font>")
        f.write('<hr color="#8f5902"></hr>')
        f.write(t)
        #f.write('<a href="#" class="scrollup" title="Nach oben springen!">↑</a>')
        f.write(body)
        f.close()
    webbrowser.open(url)
    
makeList()