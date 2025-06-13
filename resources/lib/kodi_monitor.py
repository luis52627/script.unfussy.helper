#!/usr/bin/python

import xbmc
import time
import json
from resources.lib.helper import *

class KodiMonitor(xbmc.Monitor):

    def __init__(self, **kwargs):
        super(KodiMonitor, self).__init__()
        self.win = kwargs.get('win')

    def onDatabaseUpdated(self, database):
        pass

    def onNotification(self, sender, method, data):
        try:
            mediatype = ''
            if isinstance(data, bytes):  # garantir compatibilidade
                data = data.decode('utf-8')
            data = json.loads(data)
            if isinstance(data, dict):
                if 'item' in data:
                    mediatype = data['item'].get('type', '')
                elif 'type' in data:
                    mediatype = data.get('type', '')
            if method == 'Player.OnStop' and mediatype == 'episode':
                self.refresh_widget('nextepisodes')
        except Exception as ex:
            log(f'Exception in KodiMonitor: {ex}', xbmc.LOGWARNING)

    def refresh_widget(self, widget):
        prop = f'widgetreload-{widget}'
        self.win.setProperty(prop, time.strftime("%Y%m%d%H%M%S", time.gmtime()))
