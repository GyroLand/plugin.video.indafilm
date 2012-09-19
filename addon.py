#!/usr/bin/env python
import xbmcplugin, xbmcgui
import urllib, urllib2, urlparse, re
from pyamf.remoting.client import RemotingService

PLUGIN_NAME = 'IndaFilm'
PLUGIN_ID = 'plugin.video.indafilm'

def addDir(name, url, mode, thumb, info):
    u = sys.argv[0] + '?url=' + urllib.quote_plus(url) + '&mode=' + str(mode) + '&name=' + urllib.quote_plus(name) + '&thumb=' + urllib.quote_plus(thumb)
    item = xbmcgui.ListItem(name, iconImage = "DefaultFolder.png", thumbnailImage = thumb)
    item.setInfo(type = 'Video', infoLabels = info)
    return xbmcplugin.addDirectoryItem(handle = int(sys.argv[1]), url = u, listitem = item, isFolder = True)

def addLink(name, url, iconimage):
    item = xbmcgui.ListItem(name, iconImage = 'DefaultVideo.png', thumbnailImage = iconimage)
    item.setInfo(type = 'Video', infoLabels = {'title': name})
    return xbmcplugin.addDirectoryItem(handle = int(sys.argv[1]), url = url, listitem = item, isFolder = False)

def CATEGORIES():
    doc = urllib2.urlopen('http://film.indavideo.hu/browse/mozifilm')
    started = False
    rex = re.compile('<li ><a href="(/browse/.*)">(.*)</a></li>')
    while True:
        line = doc.readline()
        if not line: break
        line = line.strip()
        if line == '': continue
        if line == '<ul id="channelList">':
            started = True
        if started:
            if line == '</ul>': break
            m = rex.match(line)
            if m:
                url = 'http://film.indavideo.hu' + m.group(1)
                title = m.group(2)
                addDir(title, url, 1, 'DefaultFolder.png', {'title': title})

def INDEX(url):
    divstack = []
    info = {}
    doc = urllib2.urlopen(url)
    divexp = re.compile('<div (class|id)="([^"]*)"')
    thumbexp = re.compile('<img src="(http://pics.indavideo.hu/videos/[^"]*)"')
    videoexp = re.compile('<a href="(/video/.*)" >(.*)</a>')
    spanexp = re.compile('<span>\((\d*)\' (\d*)\)</span>')
    while True:
        line = doc.readline()
        if not line: break
        line = line.strip()
        if line == '': continue
        idx = line.find('<div')
        while idx >= 0:
            m = divexp.match(line[idx:])
            if m:
                divstack.append(m.group(2))
            else:
                divstack.append('unnamed')
            idx = line.find('<div', idx + 1)
        if 'COLUMN_1' in divstack:
            break
        if 'item TYPE_24   ' in divstack:
            m = thumbexp.search(line)
            if m:
                thumb = m.group(1)
            if 'title_duration_year' in divstack:
                m = spanexp.search(line)
                if m:
                    info['duration'] = m.group(1)
                    info['year'] = m.group(2)
                m = videoexp.search(line)
                if m:
                    url = 'http://film.indavideo.hu' + m.group(1)
                    title = m.group(2)
                    info['title'] = title
            if 'description' in divstack:
                if line.startswith('<div'):
                    descr = []
                elif line.startswith('</div'):
                    info['plot'] = '\n'.join(descr)
                else:
                    descr.append(line)

        if line.find('</div>') >= 0:
            item = divstack.pop()
            if item == 'item TYPE_24   ':
                addDir(title, url, 2, thumb, info)
                info = {}
                title = ''
                url = ''
                thumb = ''


def VIDEOLINKS(url, name, thumb):
    frameexp = re.compile('<iframe .* src="(http://embed.indavideo.hu/player/html5/([^/]*)/\?autostart=1&hide=1)" .*></iframe>')
    client = RemotingService('http://amfphp.indavideo.hu/gateway.php')
    service = client.getService('hash_2_video.GetVideoValues.getVideo')
    doc = urllib2.urlopen(url)
    while True:
        line = doc.readline()
        if not line: break
        line = line.strip()
        if line == '': continue
        m = frameexp.match(line)
        if m:
            id = m.group(2)
            response = service(id, 's')
            url = response['VALUES']['video_flv'].encode('ascii', 'ignore')
            addLink(name, url, thumb)
            break


def log(text):
    xbmc.log('%s plugin: %s' % (PLUGIN_NAME, text))


param = {}
parts = urlparse.urlparse(sys.argv[2])
if parts[4]:
    for param_pair in parts[4].split('&'):
        name, value = param_pair.split('=')
        param[name] = urllib.unquote_plus(value)

if 'mode' not in param or 'url' not in param:
    CATEGORIES()
elif len(param['url']) < 1:
    CATEGORIES()
elif int(param['mode']) == 1:
    INDEX(param['url'])
elif int(param['mode']) == 2:
    VIDEOLINKS(param['url'], param['name'], param['thumb'])
 
xbmcplugin.endOfDirectory(int(sys.argv[1]))

