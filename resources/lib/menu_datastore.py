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
CWD = Path(xbmcvfs.translatePath(str(Path(ADDON.getAddonInfo('path')))))

DEFAULTPATH = Path(xbmcvfs.translatePath(f"special://home/addons/{ADDONID}/resources/menu_default.json"))
CONFIGPATH = Path(xbmcvfs.translatePath(f"special://profile/addon_data/{ADDONID}/menu.json"))
SKININCLUDEPATH = Path(xbmcvfs.translatePath("special://skin/xml/Includes_Home_Menucontent.xml"))

#######################################################################################

class MenuDataStore:

    def __init__(self, am=None):
        self.am = am if am else MenuActionManager()
        self.changed = False
        self.menu = None
        self.xmlWriter = MenuXMLWriter(self.am)

    def loadMenu(self):
        if not self.load(CONFIGPATH):
            if not self.load(DEFAULTPATH):
                self.menu = None
        return self.menu is not None

    def load(self, file_path: Path):
        try:
            with file_path.open(encoding='utf-8') as f:
                self.menu = json.load(f)
            return True
        except Exception as e:
            log(f"MenuDataStore.load: failed to load {file_path}: {e}", xbmc.LOGWARNING)
            self.menu = None
            return False

    def reset(self):
        try:
            if CONFIGPATH.exists():
                CONFIGPATH.unlink()
            self.menu = None
            self.changed = True
            self.loadMenu()
        except Exception as e:
            log(f"MenuDataStore.reset: error resetting menu: {e}", xbmc.LOGERROR)

    def saveMenu(self):
        if not self.changed:
            return
        self.saveJson()
        self.xmlWriter.save(self.menu)
        self.changed = False

    def saveJson(self):
        try:
            CONFIGPATH.parent.mkdir(parents=True, exist_ok=True)
            with CONFIGPATH.open('w', encoding='utf-8') as f:
                json.dump(self.menu, f, indent=2, ensure_ascii=False)
        except Exception as e:
            log(f"MenuDataStore.saveJson: failed to save {CONFIGPATH}: {e}", xbmc.LOGERROR)

    def checkXMLIncludes(self):
        if SKININCLUDEPATH.exists():
            return False
        if self.loadMenu():
            self.changed = True
            self.saveMenu()
            return True
        return False

    def mainmenu(self):
        return self.menu

    def submenu(self, index):
        return self.menu[index].get('submenu', []) if self.menu else []

    def hasSubmenu(self, index):
        return bool(self.menu and self.menu[index].get('submenu'))

    def getValue(self, index_menu, index_submenu, item):
        try:
            if index_submenu > -1:
                return self.menu[index_menu]['submenu'][index_submenu].get(item, 0)
            else:
                return self.menu[index_menu].get(item, 0)
        except (IndexError, KeyError, TypeError):
            return 0

    def getLabel(self, index_menu, index_submenu):
        try:
            label = self.menu[index_menu]['label']
            if index_submenu > -1:
                label = self.menu[index_menu]['submenu'][index_submenu]['label']
            if label.isdigit():
                label = f'$LOCALIZE[{label}]'
            return label
        except (IndexError, KeyError, TypeError):
            return ''

    def setValue(self, index_menu, index_submenu, item, value):
        self.changed = True
        try:
            if index_submenu > -1:
                self.menu[index_menu]['submenu'][index_submenu][item] = value
            else:
                self.menu[index_menu][item] = value
            log(f'Item changed: {self.menu[index_menu]}')
        except (IndexError, KeyError, TypeError) as e:
            log(f"MenuDataStore.setValue: error setting value: {e}", xbmc.LOGERROR)

    def newElement(self, index_menu, index_submenu):
        self.changed = True
        try:
            if index_submenu == -1:
                self.menu.insert(index_menu + 1, self.newMenuItem())
            else:
                self.menu[index_menu]['submenu'].insert(index_submenu + 1, self.newMenuItem())
        except Exception as e:
            log(f"MenuDataStore.newElement: error inserting element: {e}", xbmc.LOGERROR)

    def newSubmenu(self, index_menu):
        self.changed = True
        try:
            self.menu[index_menu]['submenu'].append(self.newMenuItem())
        except Exception as e:
            log(f"MenuDataStore.newSubmenu: error adding submenu: {e}", xbmc.LOGERROR)

    def newMenuItem(self):
        return {
            'label': ADDON.getLocalizedString(30022),
            'thumb': 'icons/buttons/new.png',
            'actiontype': -1,
            'action': -1,
            'visible': True,
            'submenu': []
        }

    def deleteElement(self, index_menu, index_submenu):
        self.changed = True
        try:
            if index_submenu == -1:
                del self.menu[index_menu]
            else:
                del self.menu[index_menu]['submenu'][index_submenu]
        except Exception as e:
            log(f"MenuDataStore.deleteElement: error deleting element: {e}", xbmc.LOGERROR)

    def switchElements(self, index_menu, index_submenu, up):
        self.changed = True
        try:
            if index_submenu > -1:
                submenu = self.menu[index_menu]['submenu']
                if (up and index_submenu == 0) or (not up and index_submenu >= len(submenu) - 1):
                    return
                index_new = index_submenu - 1 if up else index_submenu + 1
                submenu[index_submenu], submenu[index_new] = submenu[index_new], submenu[index_submenu]
                return index_new
            else:
                if (up and index_menu == 0) or (not up and index_menu >= len(self.menu) - 1):
                    return
                index_new = index_menu - 1 if up else index_menu + 1
                self.menu[index_menu], self.menu[index_new] = self.menu[index_new], self.menu[index_menu]
                return index_new
        except Exception as e:
            log(f"MenuDataStore.switchElements: error switching elements: {e}", xbmc.LOGERROR)
            return None
