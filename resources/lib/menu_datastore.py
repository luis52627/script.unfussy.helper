#!/usr/bin/env python3
# coding: utf-8

import json
import xml.etree.ElementTree as ET
from pathlib import Path
import xbmc, xbmcgui, xbmcvfs, xbmcaddon

from resources.lib.helper import *
from resources.lib.menu_actionmanager import MenuActionManager

#######################################################################################

ADDON = xbmcaddon.Addon()
ADDONID = ADDON.getAddonInfo('id')
CWD = ADDON.getAddonInfo('path')

DEFAULTPATH = Path(xbmcvfs.translatePath(str(Path(CWD) / 'resources' / 'menu_default.json')))
CONFIGPATH = Path(xbmcvfs.translatePath(str(Path("special://profile") / "addon_data" / ADDONID / 'menu.json')))
SKININCLUDEPATH = Path(xbmcvfs.translatePath(str(Path("special://skin") / 'xml' / 'Includes_Home_Menucontent.xml')))

#######################################################################################

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

class MenuXMLWriter:

    def __init__(self, am):
        self.am = am

    def save(self, menu):
        root = ET.Element('includes')

        include_mainmenu_content = ET.SubElement(root, 'include', name='home_mainmenu_content')
        item_content = ET.SubElement(include_mainmenu_content, 'content')

        include_mainmenu_submenus = ET.SubElement(root, 'include', name='home_mainmenu_submenus')

        submenu_id = 10
        for item in menu:
            if not item.get('visible', True):
                continue
            if not item.get('submenu'):
                self.mainMenuItem(item_content, item)
            else:
                self.mainMenuItem(item_content, item, submenu_id)
                self.submenusItem(include_mainmenu_submenus, submenu_id)
                self.submenuContent(root, item['submenu'], submenu_id)
                submenu_id += 10

        indent(root)
        tree = ET.ElementTree(root)
        tree.write(str(SKININCLUDEPATH), encoding='utf-8', xml_declaration=True, method="xml")
