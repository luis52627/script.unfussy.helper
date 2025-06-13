#!/usr/bin/env python3
import locale
from datetime import datetime, timedelta
import xbmcgui
from resources.lib.helper import *  # Presumo que tenha funções usadas aqui (json_call, getUtcOffset, getTimeFromString, log)

#######################################################################################

class PVRRunningAt:

    def __init__(self):
        try:
            default_locale = locale.getdefaultlocale()[0]
            if default_locale:
                locale.setlocale(locale.LC_ALL, default_locale)
        except Exception:
            log(f"ERROR setting locale: {default_locale}")

    def getBroadcastAt(self, starttime_str, channelid):
        utc_offset = getUtcOffset()
        broadcasts = self.getBroadcasts(channelid)
        if not broadcasts:
            return None

        starttime, start_interval, stop_interval = self.getStartTimeInterval(starttime_str)
        fallback_index = -1

        for i, broadcast in enumerate(broadcasts):
            start_bc = getTimeFromString(broadcast['starttime'], '%Y-%m-%d %H:%M:%S', utc_offset)
            end_bc = getTimeFromString(broadcast['endtime'], '%Y-%m-%d %H:%M:%S', utc_offset)

            if start_interval < start_bc < stop_interval and end_bc > stop_interval:
                return broadcast

            if start_bc < starttime < end_bc:
                fallback_index = i

        return broadcasts[fallback_index] if fallback_index >= 0 else None

    def showInfo(self, broadcast_id, channel_id, xml_file, xml_filepath):
        bc_id = [{'broadcastid': int(broadcast_id), 'channelid': int(channel_id)}]
        broadcasts = self.getBroadcastsById(bc_id)
        if not broadcasts:
            log("Error fetching broadcast details")
            return

        broadcast = broadcasts[0]
        win = xbmcgui.WindowXMLDialog(xml_file, xml_filepath)
        # Define propriedades simplificando e evitando múltiplas chamadas
        properties = {
            'broadcastid': str(broadcast['broadcastid']),
            'title': broadcast.get('title', ''),
            'plot': broadcast.get('plot', ''),
            'plotoutline': broadcast.get('plotoutline', ''),
            'cast': broadcast.get('cast', ''),
            'genre': ', '.join(broadcast.get('genre', [])) if isinstance(broadcast.get('genre'), list) else broadcast.get('genre', ''),
            'director': broadcast.get('director', ''),
            'episodename': broadcast.get('episodename', ''),
            'episodenum': str(broadcast.get('episodenum', 0)),
            'episodepart': str(broadcast.get('episodepart', 0)),
            'thumbnail': broadcast.get('thumbnail', ''),
            'year': str(broadcast.get('year', '')),
            'date': broadcast.get('date', ''),
            'datelong': broadcast.get('datelong', ''),
            'starttime': broadcast.get('starttime', ''),
            'endtime': broadcast.get('endtime', ''),
            'runtime': str(broadcast.get('runtime', 0)),
            'switchdate': broadcast.get('switchdate', ''),
            'channelid': str(broadcast['channel'].get('channelid', '')) if broadcast.get('channel') else '',
            'channel': broadcast['channel'].get('channel', '') if broadcast.get('channel') else '',
            'channelnumber': str(broadcast['channel'].get('channelnumber', '')) if broadcast.get('channel') else '',
            'channelicon': broadcast['channel'].get('icon', '') if broadcast.get('channel') else ''
        }

        for key, value in properties.items():
            win.setProperty(key, value)

        win.doModal()
        del win

    def setTimer(self, bc_id):
        json_call('PVR.AddTimer', params={'broadcastid': int(bc_id)})

    #######################################################################################
    # Private methods
    #######################################################################################

    def getBroadcasts(self, channelid):
        query = json_call('PVR.GetBroadcasts', params={'channelid': channelid}, properties=['starttime', 'endtime'])
        try:
            return query['result']['broadcasts']
        except Exception:
            log("ERROR getBroadcasts")
            return None

    def getBroadcastsById(self, broadcast_ids):
        utc_offset = getUtcOffset()
        broadcasts = []

        for bc in broadcast_ids:
            bc_id = bc['broadcastid']
            channel_id = bc['channelid']

            query = json_call('PVR.GetBroadcastDetails', params={'broadcastid': bc_id}, properties=broadcast_properties)
            try:
                broadcast = query['result']['broadcastdetails']
                starttime = getTimeFromString(broadcast['starttime'], '%Y-%m-%d %H:%M:%S', utc_offset)
                endtime = getTimeFromString(broadcast['endtime'], '%Y-%m-%d %H:%M:%S', utc_offset)

                broadcast.update({
                    'date': starttime.strftime('%d.%m'),
                    'datelong': starttime.strftime('%a %d.%b'),
                    'starttime': starttime.strftime('%H:%M'),
                    'endtime': endtime.strftime('%H:%M'),
                    'switchdate': starttime.strftime('%d.%m.%Y %H:%M'),
                    'cast': self.beautifyCast(broadcast.get('cast', '')),
                    'channel': self.getChannelDetails(channel_id)
                })

                broadcasts.append(broadcast)
            except Exception:
                log("ERROR GetBroadcastDetails")

        return broadcasts

    def beautifyCast(self, cast):
        if not cast:
            return ''
        return '\n'.join(actor.strip() for actor in cast.split(','))

    def getChannelDetails(self, channel_id):
        query = json_call('PVR.GetChannelDetails', properties=channel_properties, params={'channelid': channel_id})
        try:
            return query['result']['channeldetails']
        except Exception:
            return None

    def getStartTimeInterval(self, str_starttime):
        now = datetime.now()
        date_now = now.strftime("%m-%d-%Y")
        starttime = getTimeFromString(f"{date_now} {str_starttime}", '%m-%d-%Y %H:%M')
        if now > starttime:
            starttime += timedelta(days=1)
        start_interval = starttime - timedelta(seconds=300)
        stop_interval = starttime + timedelta(seconds=300)
        return starttime, start_interval, stop_interval
