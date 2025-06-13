#!/usr/bin/env python3
import time
import xbmc
import xbmcgui
from resources.lib.helper import json_call, log, getUtcOffset

# Propriedades usadas nas chamadas JSON
timer_properties = [
    "timerid", "starttime", "endtime", "title", "state", "channelid"
]

channel_properties = [
    "channelid", "channelnumber", "label"
]

class PVRTimers:

    def __init__(self):
        pass

    def refresh(self):
        win_home = xbmcgui.Window(10000)
        try:
            widget_id = int(win_home.getProperty('widget_timers_id'))
        except (ValueError, TypeError):
            return
        
        if widget_id == -1:
            return
        
        timestr = time.strftime("%Y%m%d%H%M%S", time.gmtime())
        win_home.setProperty('widgetreload-timers', timestr)
        
        widget = win_home.getControl(widget_id)
        if not widget.isVisible() and self.timersAvailable():
            widget.setVisibleCondition('true')
        
        log("Timers widget reloaded")

    def delTimerDialog(self, timer_id):
        timer = self.fetchTimer(timer_id)
        if not timer:
            return False

        header = xbmc.getLocalizedString(19060) + '?'
        line1 = timer.get('title', '')
        line2 = xbmc.getLocalizedString(846)
        dialog = xbmcgui.Dialog()
        if dialog.yesno(header, line1, line2):
            self.delTimer(timer_id)
            return True
        return False

    def timersAvailable(self):
        return len(self.fetchTimers()) > 0

    def fetchTimers(self):
        try:
            query = json_call('PVR.GetTimers', properties=timer_properties)
            return query['result'].get('timers', [])
        except Exception as e:
            log(f"ERROR FETCH TIMERS: {e}")
            return []

    def fetchTimer(self, timer_id):
        try:
            query = json_call('PVR.GetTimerDetails', properties=timer_properties, params={'timerid': int(timer_id)})
            return query['result'].get('timerdetails')
        except Exception as e:
            log(f"ERROR FETCH TIMER {timer_id}: {e}")
            return None

    def fetchChannel(self, channel_id):
        try:
            query = json_call('PVR.GetChannelDetails', properties=channel_properties, params={'channelid': channel_id})
            return query['result'].get('channeldetails')
        except Exception as e:
            log(f"ERROR FETCH CHANNEL {channel_id}: {e}")
            return None

    def delTimer(self, timer_id):
        try:
            json_call('PVR.DeleteTimer', params={'timerid': int(timer_id)})
            log(f"Timer {timer_id} deleted")
        except Exception as e:
            log(f"ERROR DELETE TIMER {timer_id}: {e}")
