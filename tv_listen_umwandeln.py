#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os

channels = ['3Sat', 'ARD Alpha', 'ARD ONE', 'ARD Tagesschau', 'ARD', 'ARTE DE', 'ARTE FR', 'BR Nord', 'BR Süd', 'DW', 'HR', 'KIKA', 'MDR Sachsen', 'MDR Sachsen-Anhalt', 'MDR Thüringen', 'mtv', 'NDR Fernsehen Hamburg', 'NDR Fernsehen Mecklenburg-Vorpommern', 'NDR Fernsehen Niedersachsen', 'NDR Fernsehen Schleswig-Holstein', 'NDR', 'ORF-1', 'ORF-2', 'ORF-3', 'ORF-SPORT', 'ORF-Sport', 'PHOENIX', 'RBB Berlin', 'RBB Brandenburg', 'ZDF info', 'ZDF neo', 'ZDF', 'SR', 'SWR', 'WDR']

tv_folder = os.path.expanduser("~/.local/share/LiveStream-TVPlayer-master/tv_listen")
myfile = os.path.expanduser("~/.local/share/LiveStream-TVPlayer-master/mychannels.txt")

mlist = []

for file in os.listdir(tv_folder):
    filepath = os.path.join(tv_folder, file)
    if os.path.isfile(filepath):
        url = filepath
        name = os.path.splitext(os.path.basename(url))[0]
        if not name in channels:
            mlist.append(f"{name},{url}")

mlist.sort(key=str.lower)
result = '\n'.join(mlist)

with open(myfile, 'w') as f:
    f.write(result)
    
