#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import xbmc
import xbmcgui
import xbmcvfs
import xbmcaddon
import xml.etree.ElementTree as ET

from resources.lib.helper import *
from resources.lib.widgets_datastore import WidgetsDataStore
from resources.lib.widget_manager import WidgetManager
from resources.lib.addon_paths_manager import AddonPathManager

ADDON = xbmcaddon.Addon()

class Gui_Widgets(xbmcgui.WindowXMLDialog):
    def __init__(self, *args, **kwargs):
        self.wm = WidgetManager()
        self.widgets = WidgetsDataStore(self.wm)
        if not self.widgets.loadWidgets():
            log("fatal error loading widgets structure", xbmc.LOGWARNING)
            self.close()

    def onInit(self):
        self.index_widget = -1
        self.control_widgets = self.getControl(100)
        self.label_header = self.getControl(302)
        self.button_limit = self.getControl(306)
        self.radio_visible = self.getControl(307)
        self.label_category = self.getControl(402)
        self.label_widget = self.getControl(502)
        self.button_widget = self.getControl(503)

        # Inicializar seletores
        self.channel_selector = ChannelSelector(self)
        self.addon_selector = AddonSelector(self)
        self.playlist_selector = PlaylistSelector(self)
        self.addon_path_selector = AddonPathSelector(self)
        self.order_selector = OrderSelector(self)

        self.renderWidgets()
        self.setFocus(self.control_widgets)
        self.setWidgetIndex()
        self.setDetail()

    def onClick(self, control_id):
        self.setWidgetIndex()
        actions = {
            201: lambda: self.moveItem(up=True),
            203: lambda: self.moveItem(up=False),
            221: self.newElement,
            223: self.deleteElement,
            224: self.reset2Default,
            303: self.editHeader,
            306: self.editLimit,
            307: self.setVisibility,
            403: lambda: self.editCategory(next=True),
            404: lambda: self.editCategory(next=False),
            503: self.editWidget,
            604: self.editChannels,
            608: self.editPointInTime,
            704: self.editAddons,
            707: lambda: self.editAddonOrder(next=False),
            708: lambda: self.editAddonOrder(next=True),
            804: self.editPlaylist,
            904: self.editAddonPath,
            905: self.manageAddonPaths,
            1004: lambda: self.sortOrder(next=False),
            1005: lambda: self.sortOrder(next=True),
        }
        if control_id in actions:
            actions[control_id]()

    def onAction(self, action):
        self.setWidgetIndex()
        if action.getId() == 92:  # back
            self.widgets.saveWidgets()
            self.widgets.setSkinStrings()
            self.close()
        elif action.getId() in (3, 4):  # up/down
            if self.getFocusId() == 100:
                self.setDetail()

    def hasChanged(self):
        return self.widgets.changed

    def renderWidgets(self):
        self.control_widgets.reset()
        for widget in self.widgets.widgets:
            self.control_widgets.addItem(self.createListItem(widget))

    def reloadWidgets(self, focus=-1):
        self.renderWidgets()
        self.control_widgets.selectItem(focus if focus > -1 else self.index_widget)

    def createListItem(self, widget):
        listitem = xbmcgui.ListItem(widget['header'])
        if widget['header'].isdigit():
            listitem.setLabel(ADDON.getLocalizedString(int(widget['header'])))
        listitem.setArt({'thumb': 'icons/settings/widget.png'})
        listitem.setProperty('is_visible', 'true' if widget.get('visible') else 'false')
        listitem.setProperty('category', self.wm.getCategory(widget['category']))
        listitem.setProperty('type', self.wm.getType(widget['category'], widget['type']))
        listitem.setProperty('desc', self.wm.getDesc(widget['category'], widget['type']))
        listitem.setProperty('styledesc', self.wm.getStyleDesc(widget['category'], widget['type'], widget['style']))
        listitem.setProperty('size', self.wm.getSize(widget['category'], widget['type'], widget['style']))
        listitem.setProperty('layout', self.wm.getLayout(widget['category'], widget['type'], widget['style']))
        limit = widget.get('limit', 0)
        listitem.setProperty('limit', str(limit) if limit > 0 else '')
        return listitem

    def setWidgetIndex(self):
        self.index_widget = self.control_widgets.getSelectedPosition()

    def setDetail(self):
        idx = self.index_widget
        cat = self.widgets.getValue(idx, 'category')
        typ = self.widgets.getValue(idx, 'type')
        style = self.widgets.getValue(idx, 'style')

        self.button_limit.setVisible(self.wm.setLimit(cat, typ))
        self.radio_visible.setSelected(self.widgets.getValue(idx, 'visible'))
        self.label_category.setLabel(self.wm.getCategory(cat, True))
        self.label_widget.setLabel(self.wm.getWidget(cat, typ, style))
        self.button_widget.setEnabled(cat != -1)

        # Atualiza visualização para cada seletor
        for selector, fields in [
            (self.channel_selector, ('channels', 'pointintime')),
            (self.addon_selector, ('addons',)),
            (self.playlist_selector, ('playlist',)),
            (self.addon_path_selector, ('addonpath',)),
            (self.order_selector, ('sortby',))
        ]:
            if selector.show(cat, typ):
                selector.setVisible(True)
                vals = [self.widgets.getValue(idx, f) for f in fields]
                selector.setDetail(*vals)
            elif selector.hide(cat, typ):
                selector.setVisible(False)

    # Ações básicas:
    def moveItem(self, up): self.widgets.switchElements(self.index_widget, up); self.reloadWidgets()
    def newElement(self):
        self.widgets.newElement(self.index_widget)
        self.index_widget += 1
        self.reloadWidgets()
        self.setDetail()
        self.setFocusId(303)
    def deleteElement(self):
        header = self.widgets.getHeader(self.index_widget)
        if xbmcgui.Dialog().yesno(
            ADDON.getLocalizedString(30112),
            f"{ADDON.getLocalizedString(30113)}?\n\"{header}\""
        ):
            self.widgets.deleteElement(self.index_widget)
            self.reloadWidgets()
            self.setDetail()
    def reset2Default(self):
        if xbmcgui.Dialog().yesno(
            ADDON.getLocalizedString(30112),
            ADDON.getLocalizedString(30117)
        ):
            self.widgets.reset()
            self.index_widget = 0
            self.reloadWidgets()
            self.setDetail()
    def editHeader(self):
        hdr = self.widgets.getValue(self.index_widget, 'header')
        if hdr.isdigit():
            hdr = ADDON.getLocalizedString(int(hdr))
        new = xbmcgui.Dialog().input(ADDON.getLocalizedString(30030), type=xbmcgui.INPUT_ALPHANUM, defaultt=hdr)
        if new: self.widgets.setValue(self.index_widget, 'header', new); self.reloadWidgets()
    def editLimit(self):
        cur = str(self.widgets.getValue(self.index_widget, 'limit'))
        new = xbmcgui.Dialog().numeric(0, ADDON.getLocalizedString(30019), cur)
        if new: self.widgets.setValue(self.index_widget, 'limit', int(new)); self.reloadWidgets()
    def setVisibility(self):
        self.widgets.setValue(self.index_widget, 'visible', self.radio_visible.isSelected()); self.reloadWidgets()
    def editCategory(self, next):
        idx = self.index_widget
        new_cat = (self.widgets.getValue(idx, 'category') + (1 if next else -1)) % self.wm.numCategories()
        self.widgets.setValue(idx, 'category', new_cat)
        # reset campos
        for f in ['limit', 'type', 'style', 'channels', 'pointintime', 'addons', 'playlist', 'addonpath']:
            self.widgets.setValue(idx, f, [] if f.endswith('s') else '')
        self.button_widget.setEnabled(True)
        self.setDetail()
    def editWidget(self):
        idx = self.index_widget
        cat = self.widgets.getValue(idx, 'category')
        typ, style = self.wm.getWidgetDetails(cat,
            xbmcgui.Dialog().select(
                self.wm.getCategory(cat), 
                self.wm.getWidgetItems(cat), preselect=self.wm.getWidgetIndex(cat, *self.widgets.getValue(idx, 'type', 'style')),
                useDetails=True
            )
        )
        self.widgets.setValue(idx, 'type', typ)
        self.widgets.setValue(idx, 'style', style)
        self.widgets.setValue(idx, 'header', self.wm.getType(cat, typ))
        if not self.wm.setLimit(cat, typ):
            self.widgets.setValue(idx, 'limit', -1)
        self.reloadWidgets()
        self.setDetail()
    def editChannels(self):
        new = self.channel_selector.showSelector(self.widgets.getValue(self.index_widget, 'channels'))
        if new is not None: self.widgets.setValue(self.index_widget, 'channels', new); self.setDetail()
    def editPointInTime(self):
        new = self.channel_selector.showTimeSelector(self.widgets.getValue(self.index_widget, 'pointintime'))
        if new: self.widgets.setValue(self.index_widget, 'pointintime', new); self.setDetail()
    def editAddons(self):
        new = self.addon_selector.showSelector(self.widgets.getValue(self.index_widget, 'addons'))
        if new is not None: self.widgets.setValue(self.index_widget, 'addons', new); self.setDetail()
    def editAddonOrder(self, next):
        self.addon_selector.editOrder(next); self.widgets.hasChanged()
    def editPlaylist(self):
        sel = self.widgets.getValue(self.index_widget, 'playlist')
        cat = self.widgets.getValue(self.index_widget, 'category')
        typ = self.widgets.getValue(self.index_widget, 'type')
        new = self.playlist_selector.showSelector(cat, typ, sel)
        if new: self.widgets.setValue(self.index_widget, 'playlist', new); self.setDetail()
    def editAddonPath(self):
        sel = self.widgets.getValue(self.index_widget, 'addonpath')
        new = self.addon_path_selector.showSelector(sel)
        if new: self.widgets.setValue(self.index_widget, 'header', new['name']); self.widgets.setValue(self.index_widget, 'addonpath', new); self.reloadWidgets(); self.setDetail()
    def manageAddonPaths(self):
        self.addon_path_selector.showManager()
    def sortOrder(self, next):
        idx = self.order_selector.editOrder(next); self.widgets.setValue(self.index_widget, 'sortby', idx); self.setDetail()

############################################################################
# ChannelSelector
############################################################################
class ChannelSelector:

    def __init__( self, window ):
        self.label_channels = window.getControl(602)
        self.label_channels_selected = window.getControl(603)
        self.button_select_channels = window.getControl(604)
        self.label_time = window.getControl(606)
        self.label_time_selected = window.getControl(607)
        self.button_select_time = window.getControl(608)

    def setVisible( self, show ):
        self.label_channels.setVisible(show)
        self.label_channels_selected.setVisible(show)
        self.button_select_channels.setVisible(show)
        self.label_time.setVisible(show)
        self.label_time_selected.setVisible(show)
        self.button_select_time.setVisible(show)

    def show( self, cat, type ):
        if cat == 0 and type == 3:
            return True
        return False

    def hide( self, cat, type ):
        if self.label_channels.isVisible() and not(cat == 0 and type == 3):
            return True
        return False

    def setDetail(self, channels, point_in_time):
        num_channels = len(channels)
        self.label_channels_selected.setLabel(str(num_channels))
        if point_in_time == '':
            point_in_time = ADDON.getLocalizedString(30116)
        self.label_time_selected.setLabel(point_in_time)
        

    def showSelector(self, channel_ids):
        channels_list = self.loadChannels()
        channel_listitems = self.getListitems(channels_list)
        channels_selected = self.getChannelIndexes(channels_list, channel_ids)
        dialog = xbmcgui.Dialog()
        channels_new = dialog.multiselect(ADDON.getLocalizedString(30035), channel_listitems, preselect=channels_selected, useDetails=True)
        channel_ids = self.getChannelIds(channels_list, channels_new)
        return channel_ids

    def showTimeSelector( self, point_in_time ):
        if point_in_time == '':
            point_in_time = '00:00'
        dialog = xbmcgui.Dialog()
        time_new = dialog.numeric(2, ADDON.getLocalizedString(30037), defaultt=point_in_time)
        return time_new

    def loadChannels(self):
        query = json_call('PVR.GetChannels',
                    properties=['icon', 'channelnumber'],
                    params={'channelgroupid': 'alltv'}
                )
        try:
            channels = query['result']['channels']
        except Exception:
            return []
        return channels

    def getListitems(self, channels):
        items = []
        for channel in channels:
            label = str(channel['channelnumber']) + '. ' + channel['label']
            listitem = xbmcgui.ListItem(label)
            listitem.setArt({ 'thumb': channel['icon'] })
            items.append(listitem)
        return items

    def getChannelIds(self, channels, channels_new):
        channel_ids = []
        for channel_new in channels_new:
            channel_ids.append(channels[channel_new]['channelid'])
        return channel_ids

    def getChannelIndexes(self, channels, channel_ids):
        channel_indexes = []
        for channel_id in channel_ids:
            i = 0
            for channel in channels:
                if channel['channelid'] == channel_id:
                    channel_indexes.append(i)
                    break
                i += 1
        return channel_indexes

############################################################################
# AddonSelector
############################################################################
class AddonSelector:

    def __init__( self, window ):
        self.label_addons = window.getControl(702)
        self.label_addons_selected = window.getControl(703)
        self.button_select_addons = window.getControl(704)
        self.list_addons = window.getControl(705)
        self.button_addon_left = window.getControl(707)
        self.button_addon_right = window.getControl(708)

    def setVisible( self, show ):
        self.label_addons.setVisible(show)
        self.label_addons_selected.setVisible(show)
        self.button_select_addons.setVisible(show)
        self.list_addons.setVisible(show)
        self.button_addon_left.setVisible(show)
        self.button_addon_right.setVisible(show)

    def show( self, cat, type ):
        if cat == 5 and type == 0:
            return True
        return False

    def hide( self, cat, type ):
        if self.label_addons.isVisible() and not(cat == 5 and type == 0):
            return True
        return False

    def setDetail(self, addons):
        self.addons = addons
        self.label_addons_selected.setLabel(str(len(addons)))
        self.renderAddonList()

    def showSelector(self, addons):
        addons_list = self.loadAddons()
        if len(addons_list) == 0: return
        addons_listitems = self.getListitems(addons_list)
        addons_selected = self.getAddonIndexes(addons_list, addons)
        dialog = xbmcgui.Dialog()
        addons_new = dialog.multiselect(ADDON.getLocalizedString(30233), addons_listitems, preselect=addons_selected, useDetails=True)
        addon_ids = self.getAddonIds(addons_list, addons_new)
        return addon_ids

    def editOrder(self, next=False):
        selected = self.list_addons.getSelectedPosition()
        if not next and selected == 0:
            return
        if next and selected == len(self.addons) - 1:
            return
        tmp = self.addons[selected]
        if not next:
            self.addons[selected] = self.addons[selected-1]
            self.addons[selected-1] = tmp
            selected -= 1
        else:
            self.addons[selected] = self.addons[selected+1]
            self.addons[selected+1] = tmp
            selected += 1
        self.renderAddonList()
        self.list_addons.selectItem(selected)

    def renderAddonList(self):
        self.list_addons.reset()
        for addon in self.addons:
            listitem = xbmcgui.ListItem(addon['name'])
            listitem.setArt({ 'thumb': addon['thumb'] })
            self.list_addons.addItem(listitem)

    def loadAddons(self):
        addon_types = [
            'xbmc.addon.video',
            'xbmc.addon.audio',
            'xbmc.addon.image',
            'xbmc.addon.executable'
        ]
        list_addons = []
        for addon_type in addon_types:
            query_addons = json_call('Addons.GetAddons',
                                      properties=['name', 'thumbnail'],
                                      params={ 'type': addon_type }
                                      )
            try:
                addons = query_addons['result']['addons']
                for addon in addons:
                    if not self.addonExists(list_addons, addon):
                        list_addons.append(addon)
            except Exception:
                pass
        return list_addons

    def addonExists(self, addons, addon_new):
        for a in addons:
            if a['addonid'] == addon_new['addonid']:
                return True
        return False

    def getListitems(self, addons):
        items = []
        for addon in addons:
            listitem = xbmcgui.ListItem(addon['name'])
            listitem.setArt({ 'thumb': addon['thumbnail'] })
            items.append(listitem)
        return items

    def getAddonIds(self, addons, addons_new):
        addon_ids = []
        for addon_new in addons_new:
            addon = {
                'id': addons[addon_new]['addonid'],
                'name': addons[addon_new]['name'],
                'thumb': addons[addon_new]['thumbnail']
            }
            addon_ids.append(addon)
        return addon_ids

    def getAddonIndexes(self, addons, addon_ids):
        addon_indexes = []
        for addon in addon_ids:
            i = 0
            addon_id = addon['id']
            for addon in addons:
                if addon['addonid'] == addon_id:
                    addon_indexes.append(i)
                    break
                i += 1
        return addon_indexes

############################################################################
# PlaylistSelector
############################################################################
class PlaylistSelector:

    def __init__( self, window ):
        self.playlist_widgets = [
            { 'cat': 1, 'type': 2, 'pl_type': 'video', 'pl_subtype': 'movies' },
            { 'cat': 2, 'type': 2, 'pl_type': 'video', 'pl_subtype': 'tvshows' },
            { 'cat': 2, 'type': 3, 'pl_type': 'video', 'pl_subtype': 'episodes' },
            { 'cat': 3, 'type': 3, 'pl_type': 'music', 'pl_subtype': 'songs' },
            { 'cat': 3, 'type': 4, 'pl_type': 'music', 'pl_subtype': 'albums' },
            { 'cat': 3, 'type': 5, 'pl_type': 'music', 'pl_subtype': 'artists' },
            { 'cat': 4, 'type': 2, 'pl_type': 'video', 'pl_subtype': 'musicvideos' }
        ]
        self.label_playlist = window.getControl(802)
        self.label_playlist_selected = window.getControl(803)
        self.button_select_playlist = window.getControl(804)

    def setVisible( self, show ):
        self.label_playlist.setVisible(show)
        self.label_playlist_selected.setVisible(show)
        self.button_select_playlist.setVisible(show)

    def show( self, cat, type ):
        for pw in self.playlist_widgets:
            if pw['cat'] == cat and pw['type'] == type:
                return True
        return False

    def hide( self, cat, type ):
        if not self.label_playlist.isVisible():
            return False
        for pw in self.playlist_widgets:
            if not (pw['cat'] == cat and pw['type'] == type):
                return True
        return False

    def setDetail(self, playlist):
        if playlist == '':
            playlist = ADDON.getLocalizedString(30116)
        self.label_playlist_selected.setLabel(playlist)

    def showSelector(self, category, type, playlist_presel):
        playlist_widget_index = self.getPlaylistWidgetIndex(category, type)
        if playlist_widget_index == -1:
            return
        pl_type = self.playlist_widgets[playlist_widget_index]['pl_type']
        pl_subtype = self.playlist_widgets[playlist_widget_index]['pl_subtype']
        playlists = self.loadPlaylist(pl_type, pl_subtype)
        listitems = []
        for pl in playlists:
            thumb = 'icons/mainmenu/' + pl['type'] + '.png'
            listitem = xbmcgui.ListItem(label=pl['name'])
            listitem.setArt( { 'thumb': thumb } )
            listitems.append(listitem)
        playlist_selected = self.getPlaylistIndex(playlists, playlist_presel)
        dialog = xbmcgui.Dialog()
        playlist_new = dialog.select(ADDON.getLocalizedString(30250), listitems, preselect=playlist_selected, useDetails=True)
        if playlist_new == -1:
            return ''
        return playlists[playlist_new]['name'] + '.' + playlists[playlist_new]['type']

    def loadPlaylist(self, playlist_type, playlist_subtype):
        path_playlists = xbmc.translatePath(  'special://masterprofile/playlists/' + playlist_type ).decode("utf-8")
        log('path_playlists %s' % path_playlists)
        dirs, files = xbmcvfs.listdir(path_playlists)
        playlists = []
        exts = ['.xsp', '.m3u']
        for playlist in files:
            log('checking %s' % playlist)            
            playlist_ext = ''
            for ext in exts:
                if playlist.find(ext) > -1:
                    playlist_ext = ext[1:4]
            log('ext %s' % playlist_ext)
            subtype = ''
            if playlist_ext == 'xsp':
                subtype = self.getPlaylistSubType(path_playlists, playlist)
            elif playlist_ext == 'm3u':
                subtype = 'songs'
            log('subtype %s, playlist subtype %s' % (subtype, playlist_subtype))            
            if subtype != playlist_subtype:
                continue
            playlist = {
                'name': playlist[0:-4],
                'type': playlist_ext
            }
            playlists.append(playlist)
        return playlists

    def getPlaylistSubType(self, path, playlist):
        file = path + '/' + playlist
        log("checking %s" % file)
        tree = xml.parse(file)
        root = tree.getroot()
        return root.attrib['type']

    def getPlaylistIndex(self, playlists, playlist):
        index = 0
        for pl in playlists:
            pl_file = pl['name'] + '.' + pl['type']
            if pl_file == playlist:
                return index
            index += 1
        return -1

    def getPlaylistWidgetIndex(self, cat, type):
        index = 0
        for pw in self.playlist_widgets:
            if pw['cat'] == cat and pw['type'] == type:
                return index
            index += 1
        return -1

############################################################################
# AddonPathSelector
############################################################################
class AddonPathSelector:

    def __init__( self, window ):
        self.label_path = window.getControl(902)
        self.label_path_selected = window.getControl(903)
        self.button_select_path = window.getControl(904)
        self.button_manage_paths = window.getControl(905)

    def setVisible( self, show ):
        self.label_path.setVisible(show)
        self.label_path_selected.setVisible(show)
        self.button_select_path.setVisible(show)
        self.button_manage_paths.setVisible(show)

    def show( self, cat, type ):
        if cat == 5 and type == 1:
            return True
        return False

    def hide( self, cat, type ):
        if self.label_path.isVisible() and not(cat == 5 and type == 1):
            return True
        return False

    def setDetail(self, path):
        if not path:
            self.label_path_selected.setLabel(ADDON.getLocalizedString(30116))
        self.label_path_selected.setLabel(path['name'])

    def showSelector(self, path_selected):
        apm = AddonPathManager()
        paths = apm.readExisting()
        if len(paths) == 0:
            dialog = xbmcgui.Dialog()
            ok = dialog.ok(ADDON.getLocalizedString(30279), ADDON.getLocalizedString(30280))
            return
        listitems = self.createListItems(paths)
        selected = self.getSelectedIndex(path_selected, paths)
        dialog = xbmcgui.Dialog()
        path_new = dialog.select(ADDON.getLocalizedString(30281), listitems, preselect=selected, useDetails=True)
        if path_new == -1:
            return None
        return paths[path_new]

    def showManager(self):
        apm = AddonPathManager()
        paths = apm.readExisting()
        if len(paths) == 0:
            dialog = xbmcgui.Dialog()
            ok = dialog.ok(ADDON.getLocalizedString(30279), ADDON.getLocalizedString(30280))
            return
        listitems = self.createListItems(paths)
        dialog = xbmcgui.Dialog()
        paths_delete = dialog.multiselect(ADDON.getLocalizedString(30284), listitems, useDetails=True)
        log("pathes_delete: %s" % paths_delete)
        if not paths_delete: return
        apm.deletePaths(paths, paths_delete)

    def createListItems(self, paths):
        listitems = []
        for path in paths:
            listitem = xbmcgui.ListItem(label=path['name'])
            listitem.setLabel2(path['path'])
            listitems.append(listitem)
        return listitems

    def getSelectedIndex(self, selected, paths):
        if not selected:
            return 0
        for index, path in enumerate(paths):
            if path['id'] == selected['id']:
                return index
        return 0

############################################################################
# OrderSelector
############################################################################
class OrderSelector:

    def __init__( self, window ):
        self.sortby_livetv = [
            ADDON.getLocalizedString(30286),
            ADDON.getLocalizedString(30287)
        ]
        self.order = 0
        self.label_order = window.getControl(1002)
        self.label_order_selected = window.getControl(1003)
        self.button_prev = window.getControl(1004)
        self.button_next = window.getControl(1005)

    def setVisible( self, show ):
        self.label_order.setVisible(show)
        self.label_order_selected.setVisible(show)
        self.button_prev.setVisible(show)
        self.button_next.setVisible(show)

    def show( self, cat, type ):
        if cat == 0 and type == 0:
            return True
        return False

    def hide( self, cat, type ):
        if self.label_order.isVisible() and not(cat == 0 and type == 0):
            return True
        return False

    def setDetail(self, order):
        log("sort order: %s" % order)
        self.order = order
        self.label_order_selected.setLabel(self.sortby_livetv[self.order])

    def editOrder(self, next=False):
        if not next:
            if self.order == 0:
                self.order = len(self.sortby_livetv) - 1
            else:
                self.order -= 1
        else:
            self.order = (self.order + 1)%len(self.sortby_livetv)
        return self.order 
