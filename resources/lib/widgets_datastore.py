#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import xml.etree.ElementTree as ET
import xbmc
import xbmcaddon
import xbmcvfs
from pathlib import Path

from resources.lib.helper import *
from resources.lib.widget_manager import WidgetManager

ADDON = xbmcaddon.Addon()
ADDONID = ADDON.getAddonInfo('id')
CWD = Path(xbmcvfs.translatePath(ADDON.getAddonInfo('path')))
DEFAULTPATH = os.path.join(CWD, 'resources', 'widgets_default.json')
CONFIGPATH = os.path.join(xbmcvfs.translatePath('special://profile/'), 'addon_data', ADDONID, 'widgets.json')
SKININCLUDEPATH = xbmcvfs.translatePath(os.path.join('special://skin/xml/', 'Includes_Home_Widgetcontent.xml'))


def indent(elem, level=0):
    i = "\n" + level * "  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        for child in elem:
            indent(child, level + 1)
        if not child.tail or not child.tail.strip():
            child.tail = i
    if level and (not elem.tail or not elem.tail.strip()):
        elem.tail = i

class WidgetsDataStore:
    def __init__(self, wm=None):
        self.wm = wm or WidgetManager()
        self.changed = False
        self.widgets = None
        self.xmlWriter = WidgetXMLWriter(self.wm)

    def loadWidgets(self):
        self._load_file(CONFIGPATH) or self._load_file(DEFAULTPATH)
        return bool(self.widgets)

    def _load_file(self, path):
        try:
            with xbmcvfs.File(path) as fh:
                self.widgets = json.loads(fh.read())
            return True
        except:
            self.widgets = None
            return False

    def hasChanged(self):
        self.changed = True

    def reset(self):
        if xbmcvfs.exists(CONFIGPATH):
            xbmcvfs.delete(CONFIGPATH)
        self.changed = True
        self.loadWidgets()

    def saveWidgets(self):
        if not self.changed:
            return
        self._save_json()
        self.xmlWriter.save(self.widgets)
        self.changed = False

    def _save_json(self):
        base = os.path.dirname(CONFIGPATH)
        if not xbmcvfs.exists(base):
            xbmcvfs.mkdirs(base)
        with open(CONFIGPATH, 'w', encoding='utf-8') as fh:
            json.dump(self.widgets, fh, indent=2, ensure_ascii=False)

    def setSkinStrings(self):
        xbmc.executebuiltin('Skin.Reset(runningat_name_0)')
        xbmc.executebuiltin('Skin.Reset(runningat_path_0)')
        xbmc.executebuiltin('Skin.Reset(runningat_name_1)')
        xbmc.executebuiltin('Skin.Reset(runningat_path_1)')
        xbmc.executebuiltin('Skin.Reset(runningat_name_2)')
        xbmc.executebuiltin('Skin.Reset(runningat_path_2)')
        count = 0
        for widget in self.widgets:
            if widget.get('visible') and widget.get('category') == 0 and widget.get('type') == 3:
                name = widget['header']
                path = self.wm.getPath(0, 3)
                path += f"&pointintime={widget['pointintime']}&channels=" + "-".join(map(str, widget['channels']))
                xbmc.executebuiltin(f'Skin.SetString(runningat_name_{count},{name})')
                xbmc.executebuiltin(f'Skin.SetString(runningat_path_{count},{path})')
                count += 1
                if count == 3:
                    break

    def saveJson(self):
        base_path = os.path.dirname(CONFIGPATH)
        if not os.path.exists(base_path):
            os.makedirs(base_path)
        widgets_json_file = open(CONFIGPATH, 'w+')
        json.dump(self.widgets, widgets_json_file)

    def checkXMLIncludes(self):
        if xbmcvfs.exists(SKININCLUDEPATH):
            return False
        self.loadWidgets()
        self.changed = True
        self.saveWidgets()
        return True

    def getWidgetId(self, cat, type):
        widget_id = 500
        for widget in self.widgets:
            if not widget['visible']: 
                continue
            if widget['category'] == cat and widget['type'] == type:
                return widget_id
            widget_id += 1
        return -1

    def getValue(self, index_widget, item):
        if not item in self.widgets[index_widget]:
            return
        return self.widgets[index_widget][item]

    def getHeader(self, index_widget):
        header = self.widgets[index_widget]['header']
        if header.isdigit():
            header = ADDON.getLocalizedString(int(header))
        return header

    def setValue(self, index_widget, item, value):
        if not item in self.widgets[index_widget]:
            return
        self.changed = True
        self.widgets[index_widget][item] = value

    def switchElements(self, index_widget, up):
        self.changed = True
        index_new = -1
        if up:
            if index_widget == 0: return
            index_new = index_widget - 1
        else:
            if index_widget == len( self.widgets ) - 1 : return
            index_new = index_widget + 1
        tmp = self.widgets[index_widget]
        self.widgets[index_widget] = self.widgets[index_new]
        self.widgets[index_new] = tmp
        return index_new

    def newElement(self, index_widget):
        self.changed = True
        new_widget = {
            'header': ADDON.getLocalizedString(30033),
            'category': -1,
            'type': -1,
            'style': -1,
            'limit': 20,
            'sortby': 0,
            'visible': True
        }
        self.widgets.insert(index_widget+1, new_widget)

    def addValue(self, index_widget, item, value):
        self.widgets[index_widget][item] = value

    def addArray(self, index_widget, item):
        self.widgets[index_widget][item] = []
    
    def deleteElement(self, index_widget):
        self.changed = True
        del self.widgets[index_widget]
        
class WidgetXMLWriter:
    def __init__(self, wm):
        self.wm = wm

    def save(self, widgets):
        root = ET.Element('includes')
        include_widget_content = ET.SubElement(root, 'include', name='home_widget_content')
        include_widget_anchor = ET.SubElement(root, 'include', name='home_widget_anchors')

        widget_id = 500
        for widget in widgets:
            if not widget['visible']:
                continue
            self.widgetItem(include_widget_content, widget, widget_id)
            self.widgetAnchor(include_widget_anchor, widget, widget_id, len(widgets))
            if self.wm.isAddonWidget(widget['category'], widget['type']):
                self.writeStaticContent(root, widget, widget_id)
            widget_id += 1

        self.createWidgetHeaderCond(root, widgets)
        indent(root)
        tree = ET.ElementTree(root)
        tree.write(SKININCLUDEPATH, encoding='utf-8', xml_declaration=True, method="xml")

    def widgetItem(self, parent, widget, id):
        item = ET.SubElement(parent, 'include', content='widget_mainmenu')
        self.setParam(item, 'id', id)
        header = widget['header']
        if header.isdigit():
            header = ADDON.getLocalizedString(int(header))
        self.setParam(item, 'header', header)
        if self.wm.setLimit(widget['category'], widget['type']):
            self.setParam(item, 'limit', widget['limit'])
        self.setParam(item, 'type', self.wm.getStyleWidget(widget['category'], widget['type'], widget['style']))
        self.setParam(item, 'itemwidth', self.wm.getWidth(widget['category'], widget['type'], widget['style']))
        self.setParam(item, 'height', self.wm.getHeight(widget['category'], widget['type'], widget['style']))
        path = self.getPath(widget)
        if self.wm.isAddonWidget(widget['category'], widget['type']):
            path += '-' + str(id)
        self.setParam(item, 'path', path)
        if self.wm.staticContent(widget['category'], widget['type']):
            self.setParam(item, 'static_content', 'true')
        if self.wm.hasOnClick(widget['category'], widget['type']):
            self.setParam(item, 'onclick', self.wm.getOnClick(widget['category'], widget['type']))
            self.setParam(item, 'useonclick', 'true')
        if self.wm.isOrderableWidget(widget['category'], widget['type']):
            self.setParam(item, 'sortby', self.wm.getSortbyDynamic(widget['sortby']))
        else:
            self.setParam(item, 'sortby', self.wm.getSortby(widget['category'], widget['type']))
        self.setParam(item, 'sortorder', self.wm.getSortorder(widget['category'], widget['type']))
        if self.wm.hasTarget(widget['category'], widget['type']):
            self.setParam(item, 'target', self.wm.getTarget(widget['category'], widget['type']))
        if self.wm.showPlayStatus(widget['category'], widget['type']):
            self.setParam(item, 'showplaystatus', 'true')

    def widgetAnchor(self, parent, widget, id, total):
        anchor = ET.SubElement(parent, 'control', type='button', id=str(id) + '777')
        ET.SubElement(anchor, 'visible', allowhiddenfocus='true').text = 'false'
        ET.SubElement(anchor, 'onright').text = f'SetProperty(active_channel,{id})'
        ET.SubElement(anchor, 'onright').text = str(id)
        ET.SubElement(anchor, 'onleft').text = '9001'
        ET.SubElement(anchor, 'onup').text = '9001' if id == 500 else f'SetFocus({id - 1})'
        ET.SubElement(anchor, 'ondown').text = 'SetFocus(500)' if id == (500 + total - 1) else f'SetFocus({id + 1})'
        ET.SubElement(anchor, 'onclick').text = self.getOnClick(widget)

    def getOnClick(self, widget):
        cat = widget['category']
        type = widget['type']
        if (cat == 1 and type == 2) or (cat == 2 and type in (2, 3)) or (cat == 4 and type == 2):
            return f"ActivateWindow(Videos,special://profile/playlists/video/{widget['playlist']},return)"
        elif cat == 3 and type in (3, 4, 5):
            return f"ActivateWindow(Music,special://profile/playlists/music/{widget['playlist']},return)"
        elif cat == 5 and type == 1:
            plugin_id = widget['addonpath']['path'].split('/')[0].replace('plugin://', '')
            return f'RunAddon({plugin_id})'
        return self.wm.getHeaderAction(cat, type)

    def getPath(self, widget):
        cat = widget['category']
        type = widget['type']
        if cat == 0 and type == 3:
            base = self.wm.getPath(cat, type)
            channels = '-'.join(map(str, widget['channels']))
            return f"{base}&pointintime={widget['pointintime']}&channels={channels}"
        elif cat in [1, 2, 3, 4] and type in [2, 3, 4, 5]:
            path = self.wm.getPath(cat, type)
            return f"{path}/{widget['playlist']}" if widget.get('playlist') else path
        elif cat == 5 and type == 1:
            return widget['addonpath']['path']
        return self.wm.getPath(cat, type)

    def setParam(self, parent, name, value):
        ET.SubElement(parent, 'param', name=name).text = encode4XML(str(value))

    def writeStaticContent(self, parent, widget, widget_id):
        include_item = ET.SubElement(parent, 'include', name=self.getPath(widget) + '-' + str(widget_id))
        content_item = ET.SubElement(include_item, 'content')
        for addon in widget['addons']:
            item = ET.SubElement(content_item, 'item')
            ET.SubElement(item, 'label').text = encode4XML(addon['name'])
            ET.SubElement(item, 'thumb').text = encode4XML(addon['thumb'])
            ET.SubElement(item, 'onclick').text = encode4XML(f"RunAddon({addon['id']})")

    def createWidgetHeaderCond(self, parent, widgets):
        cond = 'ControlGroup(9002).HasFocus'
        ids = [f'Control.HasFocus({500 + i}777)' for i, w in enumerate(widgets) if w['visible']]
        if ids:
            cond += ' | ' + ' | '.join(ids)
        include_item = ET.SubElement(parent, 'include', name='cond_show_updown_arrows')
        ET.SubElement(include_item, 'visible').text = cond
