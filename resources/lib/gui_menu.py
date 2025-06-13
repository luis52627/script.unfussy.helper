#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import xbmc
import xbmcgui
import xbmcvfs
import xbmcaddon

from resources.lib.helper import *
from resources.lib.menu_actionmanager import MenuActionManager
from resources.lib.menu_datastore import MenuDataStore

ADDON = xbmcaddon.Addon()

class Gui_Menu(xbmcgui.WindowXMLDialog):

    def __init__(self, *args, **kwargs):
        self.am = MenuActionManager()
        self.menu = MenuDataStore(self.am)
        if not self.menu.loadMenu():
            log("fatal error loading menu structure", xbmc.LOGWARNING)
            self.close()

    def onInit(self):
        self.index_menu = -1
        self.index_submenu = -1

        self.control_menu = self.getControl(100)
        self.control_submenu = self.getControl(110)
        self.control_submenu.setVisible(False)
        self.radio_visible = self.getControl(212)
        self.label_actiontype = self.getControl(215)
        self.label_action = self.getControl(219)
        self.button_new_submenu = self.getControl(222)
        self.label_thumbsize = self.getControl(232)

        self.renderMenu()
        self.setFocus(self.control_menu)
        self.setMenuIndex()
        self.setDetail()

    def onClick(self, control_id):
        self.setMenuIndex()
        actions = {
            201: lambda: self.moveItem(up=True),
            203: lambda: self.moveItem(up=False),
            207: self.editLabel,
            211: self.editIcon,
            212: self.setVisibility,
            216: lambda: self.actionType(next=True),
            217: lambda: self.actionType(next=False),
            220: self.action,
            221: self.newElement,
            222: self.newSubmenu,
            223: self.deleteElement,
            224: self.reset2Default,
            100: self.showSubmenu,
            110: self.hideSubmenu,
            233: lambda: self.thumbSize(next=True),
            234: lambda: self.thumbSize(next=False)
        }
        if control_id in actions:
            actions[control_id]()

    def onAction(self, action):
        self.setMenuIndex()
        if action.getId() == 92:
            if self.control_submenu.isVisible():
                self.hideSubmenu()
            else:
                self.menu.saveMenu()
                self.close()
        elif action.getId() in (3, 4):
            if self.getFocusId() in (100, 110):
                self.setDetail()

    def hasChanged(self):
        return self.menu.changed

    def setMenuIndex(self):
        self.index_menu = self.control_menu.getSelectedPosition()
        self.index_submenu = self.control_submenu.getSelectedPosition() if self.control_submenu.isVisible() else -1

    def renderMenu(self):
        self.control_menu.reset()
        for menuitem in self.menu.mainmenu():
            self.control_menu.addItem(self.createListItem(menuitem))

    def showSubmenu(self):
        if not self.menu.hasSubmenu(self.index_menu):
            return
        item = self.control_menu.getSelectedItem()
        item.setProperty('show_submenu', 'true')
        self.renderSubmenu()
        self.control_submenu.setVisible(True)
        self.setFocus(self.control_submenu)
        self.setMenuIndex()
        self.setDetail()

    def hideSubmenu(self):
        self.control_submenu.setVisible(False)
        item = self.control_menu.getSelectedItem()
        item.setProperty('show_submenu', 'false')
        self.setFocus(self.control_menu)
        self.control_submenu.reset()
        self.setMenuIndex()
        self.setDetail()

    def renderSubmenu(self):
        self.control_submenu.reset()
        for menuitem in self.menu.submenu(self.index_menu):
            self.control_submenu.addItem(self.createListItem(menuitem, submenu=True))
        top = min(self.index_menu * 80, 360)
        self.control_submenu.setPosition(400, top)

    def reloadMenu(self, focus=-1):
        if self.index_submenu > -1:
            self.renderSubmenu()
            self.control_submenu.selectItem(focus if focus > -1 else self.index_submenu)
        else:
            self.renderMenu()
            self.control_menu.selectItem(focus if focus > -1 else self.index_menu)

    def createListItem(self, menuitem, submenu=False):
        listitem = xbmcgui.ListItem(menuitem['label'])
        if menuitem['label'].isdigit():
            listitem.setLabel(xbmc.getLocalizedString(int(menuitem['label'])))
        listitem.setArt({'thumb': menuitem['thumb']})
        if not submenu and menuitem.get('submenu'):
            listitem.setProperty('has_submenu', 'true')
        listitem.setProperty('is_visible', 'true' if menuitem.get('visible') else 'false')
        listitem.setProperty('thumbsize', str(menuitem.get('thumbsize', 0)))
        return listitem

    def setDetail(self):
        is_visible = self.menu.getValue(self.index_menu, self.index_submenu, 'visible')
        self.radio_visible.setSelected(is_visible)
        thumbsize = self.menu.getValue(self.index_menu, self.index_submenu, 'thumbsize')
        self.label_thumbsize.setLabel(self.am.thumbsizes[int(thumbsize)])
        action_type = self.menu.getValue(self.index_menu, self.index_submenu, 'actiontype')
        action = self.menu.getValue(self.index_menu, self.index_submenu, 'action')
        self.label_actiontype.setLabel(self.am.getActionType(action_type))
        self.label_action.setLabel(self.am.getActionName(action_type, action))
        show = self.index_submenu == -1 and not self.menu.hasSubmenu(self.index_menu)
        self.button_new_submenu.setVisible(show)

    def moveItem(self, up=False):
        pos_new = self.menu.switchElements(self.index_menu, self.index_submenu, up)
        self.reloadMenu(pos_new)

    def editLabel(self):
        label = self.menu.getValue(self.index_menu, self.index_submenu, 'label')
        if label.isdigit():
            label = xbmc.getLocalizedString(int(label))
        new_label = xbmcgui.Dialog().input(ADDON.getLocalizedString(30028), type=xbmcgui.INPUT_ALPHANUM, defaultt=label)
        if new_label:
            self.menu.setValue(self.index_menu, self.index_submenu, 'label', new_label)
            self.reloadMenu()

    def editIcon(self):
        new_thumb = xbmcgui.Dialog().browse(2, ADDON.getLocalizedString(30029), 'local', '', True)
        if new_thumb:
            self.menu.setValue(self.index_menu, self.index_submenu, 'thumb', new_thumb)
            self.reloadMenu()

    def setVisibility(self):
        selected = self.radio_visible.isSelected()
        self.menu.setValue(self.index_menu, self.index_submenu, 'visible', selected)
        self.reloadMenu()

    def actionType(self, next=False):
        new_type = self.menu.getValue(self.index_menu, self.index_submenu, 'actiontype')
        new_type = (new_type + 1) % self.am.numActions() if next else (new_type - 1) % self.am.numActions()
        self.menu.setValue(self.index_menu, self.index_submenu, 'actiontype', new_type)
        self.menu.setValue(self.index_menu, self.index_submenu, 'action', -1)
        self.label_actiontype.setLabel(self.am.getActionType(new_type))
        self.label_action.setLabel(self.am.getActionName(new_type, -1))

    def action(self):
        action_type = self.menu.getValue(self.index_menu, self.index_submenu, 'actiontype')
        actiontype_name = self.am.getActionType(action_type, False)
        action_items = self.am.getActionItems(action_type)
        action_new = xbmcgui.Dialog().select(actiontype_name, action_items, preselect=-1, useDetails=True)
        if action_new == -1:
            return
        thumb_new = self.am.getThumb(action_type, action_new)
        if action_type in (8, 9):
            action_new = self.am.getPlaylistId(action_type, action_new)
        elif action_type == 10:
            action_new = self.am.getAddonId(action_new)
        self.menu.setValue(self.index_menu, self.index_submenu, 'label', self.am.getActionName(action_type, action_new))
        self.menu.setValue(self.index_menu, self.index_submenu, 'action', action_new)
        self.menu.setValue(self.index_menu, self.index_submenu, 'thumb', thumb_new)
        self.reloadMenu()
        self.setDetail()

    def newElement(self):
        self.menu.newElement(self.index_menu, self.index_submenu)
        if self.index_submenu == -1:
            self.index_menu += 1
        else:
            self.index_submenu += 1
        self.reloadMenu()
        self.setDetail()
        self.setFocusId(207)

    def newSubmenu(self):
        self.menu.newSubmenu(self.index_menu)
        self.reloadMenu()
        self.showSubmenu()

    def deleteElement(self):
        header = ADDON.getLocalizedString(30112)
        label = self.menu.getLabel(self.index_menu, self.index_submenu)
        content = f"{ADDON.getLocalizedString(30113)}?\n\"{label}\""
        if self.index_submenu == -1 and self.menu.hasSubmenu(self.index_menu):
            content += f"\n\n{ADDON.getLocalizedString(30114)}"
        if xbmcgui.Dialog().yesno(header, content):
            self.menu.deleteElement(self.index_menu, self.index_submenu)
            if self.index_submenu > -1 and not self.menu.hasSubmenu(self.index_menu):
                self.control_submenu.reset()
                self.index_submenu = -1
            self.reloadMenu()
            self.setDetail()

    def reset2Default(self):
        if xbmcgui.Dialog().yesno(ADDON.getLocalizedString(30112), ADDON.getLocalizedString(30115)):
            self.menu.reset()
            self.index_menu = 0
            self.index_submenu = -1
            self.reloadMenu()
            self.setDetail()

    def thumbSize(self, next=False):
        thumbsize = int(self.menu.getValue(self.index_menu, self.index_submenu, 'thumbsize'))
        thumbsize = (thumbsize + 1) % 3 if next else (thumbsize - 1) % 3
        self.menu.setValue(self.index_menu, self.index_submenu, 'thumbsize', thumbsize)
        self.label_thumbsize.setLabel(self.am.thumbsizes[thumbsize])
        self.reloadMenu()
