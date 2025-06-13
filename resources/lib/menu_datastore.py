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

DEFAULTPATH = Path(xbmcvfs.translatePath(Path(CWD) / 'resources' / 'menu_default.json'))
CONFIGPATH = Path(xbmcvfs.translatePath(Path("special://profile") / "addon_data" / ADDONID / 'menu.json'))
SKININCLUDEPATH = Path(xbmcvfs.translatePath(Path("special://skin") / 'xml' / 'Includes_Home_Menucontent.xml'))

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

    # Accessors

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

    # Menu modifications

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
                if up:
                    if index_submenu == 0:
                        return
                    index_new = index_submenu - 1
                else:
                    if index_submenu >= len(submenu) - 1:
                        return
                    index_new = index_submenu + 1
                submenu[index_submenu], submenu[index_new] = submenu[index_new], submenu[index_submenu]
                return index_new
            else:
                if up:
                    if index_menu == 0:
                        return
                    index_new = index_menu - 1
                else:
                    if index_menu >= len(self.menu) - 1:
                        return
                    index_new = index_menu + 1
                self.menu[index_menu], self.menu[index_new] = self.menu[index_new], self.menu[index_menu]
                return index_new
        except Exception as e:
            log(f"MenuDataStore.switchElements: error switching elements: {e}", xbmc.LOGERROR)
            return None


class MenuXMLWriter:

    def __init__(self, am):
        self.am = am

    def save(self, menu):
        root = ET.Element('includes')

        # Include home_mainmenu_content
        include_mainmenu_content = ET.SubElement(root, 'include', name='home_mainmenu_content')
        item_content = ET.SubElement(include_mainmenu_content, 'content')

        # Include home_mainmenu_submenus
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

    def mainMenuItem(self, parent, item, sub_id=0):
        label = self.getLabel(item.get('label', ''))
        thumbsize = self.getThumbsize(item)
        self.menuItem(parent, label, item.get('thumb', ''), thumbsize,
                      item.get('actiontype', -1), item.get('action', -1), sub_id)

    def submenusItem(self, parent, sub_id):
        include_submenu = ET.SubElement(parent, 'include', content='home_submenu')
        param = ET.SubElement(include_submenu, 'param', name='id')
        param.text = str(sub_id)

    def submenuContent(self, parent, submenu, sub_id):
        include_submenu = ET.SubElement(parent, 'include', name=f'home_submenu_content_id_{sub_id}')
        item_content = ET.SubElement(include_submenu, 'content')
        for item in submenu:
            if not item.get('visible', True):
                continue
            label = self.getLabel(item.get('label', ''))
            thumbsize = self.getThumbsize(item)
            self.menuItem(item_content, label, item.get('thumb', ''), thumbsize,
                          item.get('actiontype', -1), item.get('action', -1), -1)

    def menuItem(self, parent, label, thumb, thumbsize, actiontype, action, sub_id):
        xml_item = ET.SubElement(parent, 'item')

        xml_label = ET.SubElement(xml_item, 'label')
        xml_label.text = encode4XML(label)

        xml_thumb = ET.SubElement(xml_item, 'thumb')
        xml_thumb.text = thumb

        if actiontype > 3:
            xml_onclick = ET.SubElement(xml_item, 'onclick')
            xml_onclick.text = self.am.getOnClick(actiontype, action)
        else:
            xml_onclick1 = ET.SubElement(xml_item, 'onclick', condition=self.am.getOnClickCond(actiontype))
            xml_onclick1.text = self.am.getOnClick(actiontype, action)

            xml_onclick2 = ET.SubElement(xml_item, 'onclick', condition='!' + self.am.getOnClickCond(actiontype))
            xml_onclick2.text = self.am.getOnClickAlt(actiontype)

        xml_thumbsize = ET.SubElement(xml_item, 'property', name='thumbsize')
        xml_thumbsize.text = f'$NUMBER[{thumbsize}]'

        if sub_id == -1:
            return

        submenu_id = ET.SubElement(xml_item, 'property', name='submenu_id')
        submenu_id.text = f'$NUMBER[{sub_id}]'

    def getLabel(self, label):
        if isinstance(label, str) and label.isdigit():
            return f'$LOCALIZE[{label}]'
        return label

    def getThumbsize(self, item):
        thumbsize = item.get('thumbsize')
        if thumbsize and str(thumbsize).isdigit():
            return int(thumbsize)
        return 5


def indent(elem, level=0):
    # Pretty print XML indentation
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
