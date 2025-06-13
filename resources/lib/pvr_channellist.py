#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import locale
import json
import xbmcgui
from datetime import datetime

from resources.lib.helper import *  # Usar helper com json_call, log, getUtcOffset, getTimeFromString etc.

#######################################################################################

class PVRChannelList:

    def __init__(self):
        def_loc = ''
        try:
            def_loc = locale.getdefaultlocale()[0]
            locale.setlocale(locale.LC_ALL, def_loc)
        except Exception:
            log(f"ERROR setting locale: {def_loc}", xbmc.LOGERROR)

    def setChannelIds(self):
        # Usar json_call do helper com parâmetros adequados
        res = json_call('PVR.GetChannels', 
                        properties=['channelnumber', 'channelid'], 
                        params={'channelgroupid': 'alltv'})

        channels = []
        try:
            channels = res['result']['channels']
        except Exception as e:
            log(f"setChannelIds: failed to get channels - {e}", xbmc.LOGERROR)
            return None

        channel_ids = {ch['channelnumber']: ch['channelid'] for ch in channels}

        win = xbmcgui.Window(10700)
        win.setProperty('channel_ids', json.dumps(channel_ids))
        log(f"setChannelIds: stored {len(channel_ids)} channels", xbmc.LOGDEBUG)

    def fetchBroadcasts(self, channel_id):
        # broadcast_properties_short teste
        broadcast_properties_short = ['broadcastid', 'title', 'episodename', 'runtime', 'starttime', 'endtime']

        res = json_call('PVR.GetBroadcasts', 
                        properties=broadcast_properties_short, 
                        params={'channelid': channel_id})

        broadcasts = []
        try:
            broadcasts = res['result']['broadcasts']
        except Exception as e:
            log(f"fetchBroadcasts: failed to get broadcasts for channel {channel_id} - {e}", xbmc.LOGERROR)
            return []

        broadcasts_beautified = self.beautifyBroadcasts(channel_id, broadcasts)
        return broadcasts_beautified

    def beautifyBroadcasts(self, channel_id, broadcasts):
        utc_offset = getUtcOffset()
        now = datetime.now()
        broadcasts_beautified = []

        for bc in broadcasts:
            starttime = getTimeFromString(bc.get('starttime', ''), '%Y-%m-%d %H:%M:%S', utc_offset)
            endtime = getTimeFromString(bc.get('endtime', ''), '%Y-%m-%d %H:%M:%S', utc_offset)

            if not starttime or not endtime:
                continue
            if endtime < now:
                continue

            bc_beautified = {
                'id': bc.get('broadcastid', ''),
                'channel_id': channel_id,
                'title': bc.get('title', ''),
                'episodename': bc.get('episodename', ''),
                'runtime': bc.get('runtime', 0),
                'date': starttime.strftime('%a %d.%b'),
                'starttime': starttime.strftime('%H:%M'),
                'endtime': endtime.strftime('%H:%M'),
            }
            broadcasts_beautified.append(bc_beautified)

        log(f"beautifyBroadcasts: {len(broadcasts_beautified)} broadcasts beautified for channel {channel_id}", xbmc.LOGDEBUG)
        return broadcasts_beautified
