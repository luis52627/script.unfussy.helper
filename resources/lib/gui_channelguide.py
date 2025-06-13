#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import xbmc
import xbmcgui
import xbmcvfs
import xbmcaddon
from resources.lib.helper import *

ADDON = xbmcaddon.Addon()

class Gui_ChannelGuide(xbmcgui.WindowXMLDialog):

    def __init__(self, *args, **kwargs):
        self.channelgroups = None
        self.detail_active = False
        self.channels_loaded = self.loadChannels()

    def loadChannels(self):
        if not self.loadChannelGroups():
            return False
        for index, group in enumerate(self.channelgroups):
            try:
                query = json_call('PVR.GetChannels',
                                  properties=channeldetail_properties,
                                  params={'channelgroupid': group['channelgroupid']})
                self.channelgroups[index]['channels'] = query['result']['channels']
                self.channelgroups[index]['channellistitems'] = None
            except Exception as e:
                log(f'error loading channels: {e}', xbmc.LOGWARNING)
                return False
        return True

    def loadChannelGroups(self):
        try:
            query = json_call('PVR.GetChannelGroups', params={'channeltype': 'tv'})
            self.channelgroups = query['result']['channelgroups']
        except Exception:
            return False
        log(f"loaded groups: {self.channelgroups}", xbmc.LOGDEBUG)

        if xbmc.getCondVisibility('Skin.HasSetting(hide_all_channels)'):
            str_allchannels = xbmc.getLocalizedString(19287)
            self.channelgroups = [
                group for group in self.channelgroups
                if group['label'] != str_allchannels
            ]
        log(f"groups after hide_all_channels: {self.channelgroups}", xbmc.LOGDEBUG)
        return True

    def onInit(self):
        self.hor_layout = xbmc.getCondVisibility('Skin.HasSetting(use_channelgroups_fullwidth)')
        if not self.channels_loaded:
            return
        self.list_channelgroups = self.getControl(12)
        self.list_channels = self.getControl(13)
        self.active_channel_number = self.getActiveChannelNumber()
        self.group_index, self.channel_index = self.getActiveChannelIndex()
        self.jump_to_next_group = xbmc.getCondVisibility('Skin.HasSetting(jump_to_next_channelgroup)')
        self.renderChannelGroups()
        self.list_channelgroups.selectItem(self.group_index)
        self.renderChannels()
        self.positionChannellist()
        self.list_channels.selectItem(self.channel_index)
        self.setFocusId(13)
        xbmc.executebuiltin('ClearProperty(loadingchannels,10608)')

    def onClick(self, control_id):
        if control_id != 13:
            return
        group_index = self.list_channelgroups.getSelectedPosition()
        channel_index = self.list_channels.getSelectedPosition()
        channel_uid = self.channelgroups[group_index]['channels'][channel_index]['broadcastnow']['channeluid']
        xbmc.executebuiltin('SetProperty(noslide,true,10608)')
        self.setProperty('noslide', 'true')
        xbmc.sleep(10)
        self._close()
        self.switchChannel(channel_uid)

    def onAction(self, action):
        actions = {
            92: self._close,
            1: self.keyLeft,
            2: self.keyRight,
            3: self.keyUp,
            4: self.keyDown
        }
        func = actions.get(action.getId())
        if func:
            func()

    def _close(self):
        self.clearProperty('showdetail')
        self.close()
        xbmc.executebuiltin('Action(Close,10608)')

    def keyLeft(self):
        focus = self.getFocusId()
        if focus == 13:
            if self.detail_active:
                self.clearProperty('showdetail')
                self.detail_active = False
            else:
                self.setFocusId(12)
        elif focus == 12:
            self._close()

    def keyRight(self):
        if self.getFocusId() == 12:
            self.setFocusId(13)
        elif self.getFocusId() == 13:
            self.setProperty('showdetail', 'true')
            self.detail_active = True

    def keyUp(self):
        focus = self.getFocusId()
        if focus == 12:
            self.group_index = self.list_channelgroups.getSelectedPosition()
            self.channel_index = 0
            self.updateChannels()
        elif focus == 13:
            self.channel_index = self.list_channels.getSelectedPosition()
            if self.channel_index == len(self.channelgroups[self.group_index]['channels']) - 1 and self.jump_to_next_group:
                self.groupUp()

    def keyDown(self):
        focus = self.getFocusId()
        if focus == 12:
            self.group_index = self.list_channelgroups.getSelectedPosition()
            self.channel_index = 0
            self.updateChannels()
        elif focus == 13:
            self.channel_index = self.list_channels.getSelectedPosition()
            if self.channel_index == 0 and self.jump_to_next_group:
                self.groupDown()

    def groupUp(self):
        self.group_index = (self.group_index - 1) % len(self.channelgroups)
        self.list_channelgroups.selectItem(self.group_index)
        self.channel_index = len(self.channelgroups[self.group_index]['channels']) - 1
        self.updateChannels()

    def groupDown(self):
        self.group_index = (self.group_index + 1) % len(self.channelgroups)
        self.list_channelgroups.selectItem(self.group_index)
        self.channel_index = 0
        self.updateChannels()

    def updateChannels(self):
        self.renderChannels()
        self.positionChannellist()
        self.list_channels.selectItem(self.channel_index)

    def renderChannels(self):
        if not self.channelgroups[self.group_index]['channellistitems']:
            self.setChannelListItems()
        self.list_channels.reset()
        for item in self.channelgroups[self.group_index]['channellistitems']:
            self.list_channels.addItem(item)

    def renderChannelGroups(self):
        for index, group in enumerate(self.channelgroups):
            listitem = xbmcgui.ListItem(group['label'])
            listitem.setProperty('numchannels', str(len(group['channels'])))
            if index == self.group_index:
                listitem.setProperty('group_activechannel', 'true')
                listitem.select(True)
            self.list_channelgroups.addItem(listitem)

    def positionChannellist(self):
        if self.hor_layout:
            return
        x, y = 100, 0
        height = 1080
        max_items = 11
        num_channels = len(self.channelgroups[self.group_index]['channels'])
        if num_channels < max_items:
            height = num_channels * 100
            y = int((1080 - height) / 2)
        self.list_channels.setHeight(height)
        self.list_channels.setPosition(x, y)

    def setChannelListItems(self):
        self.channelgroups[self.group_index]['channellistitems'] = []
        utc_offset = getUtcOffset()
        for channel in self.channelgroups[self.group_index]['channels']:
            try:
                now = channel['broadcastnow']
                next_ = channel['broadcastnext']
                listitem = xbmcgui.ListItem(channel['label'])
                listitem.setArt({'icon': channel['icon']})
                listitem.setProperty('channelnumber', str(channel['channelnumber']))
                listitem.setProperty('isrecording', str(now.get('hastimer', False)))
                listitem.setProperty('progress', str(int(now.get('progresspercentage', 0))))
                listitem.setProperty('now_title', now.get('title', ''))
                listitem.setProperty('now_episodename', now.get('episodename', ''))
                listitem.setProperty('now_episodenum', str(now.get('episodenum', '')))
                listitem.setProperty('now_year', str(now.get('year', '')))
                listitem.setProperty('now_director', now.get('director', ''))
                listitem.setProperty('now_genre', ', '.join(now.get('genre', [])))
                listitem.setProperty('now_cast', now.get('cast', ''))
                listitem.setProperty('now_plot', now.get('plot', ''))
                st = getTimeFromString(now['starttime'], '%Y-%m-%d %H:%M:%S', utc_offset)
                et = getTimeFromString(now['endtime'], '%Y-%m-%d %H:%M:%S', utc_offset)
                listitem.setProperty('now_starttime', st.strftime('%H:%M') if st else '')
                listitem.setProperty('now_endtime', et.strftime('%H:%M') if et else '')
                listitem.setProperty('now_runtime', str(now.get('runtime', '')))

                listitem.setProperty('next_title', next_.get('title', ''))
                listitem.setProperty('next_episodename', next_.get('episodename', ''))
                listitem.setProperty('next_episodenum', str(next_.get('episodenum', '')))
                listitem.setProperty('next_year', str(next_.get('year', '')))
                listitem.setProperty('next_director', next_.get('director', ''))
                listitem.setProperty('next_genre', ', '.join(next_.get('genre', [])))
                listitem.setProperty('next_cast', next_.get('cast', ''))
                listitem.setProperty('next_plot', next_.get('plot', ''))
                stn = getTimeFromString(next_['starttime'], '%Y-%m-%d %H:%M:%S', utc_offset)
                etn = getTimeFromString(next_['endtime'], '%Y-%m-%d %H:%M:%S', utc_offset)
                listitem.setProperty('next_starttime', stn.strftime('%H:%M') if stn else '')
                listitem.setProperty('next_endtime', etn.strftime('%H:%M') if etn else '')
                listitem.setProperty('next_runtime', str(next_.get('runtime', '')))

                if channel['channelnumber'] == self.active_channel_number:
                    listitem.select(True)
                self.channelgroups[self.group_index]['channellistitems'].append(listitem)
            except Exception as e:
                log(f'no epg for channel: {e}', xbmc.LOGWARNING)

    def getActiveChannelNumber(self):
        try:
            channel_num = xbmc.getInfoLabel('VideoPlayer.ChannelNumberLabel')
            return int(channel_num)
        except (ValueError, TypeError):
            return -1

    def getActiveChannelIndex(self):
        for index, group in enumerate(self.channelgroups):
            for index_channel, channel in enumerate(group['channels']):
                if channel['channelnumber'] == self.active_channel_number:
                    return (index, index_channel)
        return (-1, -1)

    def switchChannel(self, channel_uid):
        all_channels_loc = xbmc.getLocalizedString(19287)
        pvr_backend = self.pvrBackendAddonId()
        if not pvr_backend:
            return
        pvr_url = f'pvr://channels/tv/{all_channels_loc}/{pvr_backend}_{channel_uid}.pvr'
        xbmc.executebuiltin(f'PlayMedia({pvr_url})')

    def pvrBackendAddonId(self):
        try:
            query_addons = json_call('Addons.GetAddons', params={'type': 'xbmc.pvrclient'}, properties=['enabled'])
            addons = query_addons['result']['addons']
            for addon in addons:
                if addon.get('enabled'):
                    return addon['addonid']
        except Exception as e:
            log(f'error querying pvr addon: {e}', xbmc.LOGWARNING)
        return None
