#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os

tv_folder = os.path.expanduser("~/.local/share/LiveStream-TVPlayer-master/tv_listen")
myfile = os.path.expanduser("~/.local/share/LiveStream-TVPlayer-master/mychannels.txt")

mlist = []

for file in os.listdir(tv_folder):
    filepath = os.path.join(tv_folder, file)
    if os.path.isfile(filepath):
        url = filepath
        name = os.path.splitext(os.path.basename(url))[0]
        mlist.append(f"{name},{url}")

mlist.sort(key=str.lower)
result = '\n'.join(mlist)

with open(myfile, 'a') as f:
    f.write(result)