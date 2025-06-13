#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import xbmc
import xbmcgui
import xbmcaddon
import xbmcvfs
import os
import json
from resources.lib.helper import *

#######################################################################################

ADDON = xbmcaddon.Addon()
ADDONID = ADDON.getAddonInfo('id')

CONFIGPATH = xbmcvfs.translatePath(f"special://profile/addon_data/{ADDONID}/widget_addon_pathes.json")

#######################################################################################

class AddonPathManager:

    def __init__(self):
        pass

    def addPath(self, path, label):
        log(f"add widget path: {path}")
        if not path:
            return
        dialog = xbmcgui.Dialog()
        name = dialog.input(ADDON.getLocalizedString(30274), defaultt=label, type=xbmcgui.INPUT_ALPHANUM)
        if not name:
            return
        self.add(name, path)

    def add(self, name, path):
        addon_pathes = self.readExisting()
        path_id = self.getNextId(addon_pathes)
        new_path = {
            'id': path_id,
            'name': name,
            'path': path
        }
        addon_pathes.append(new_path)

        base_path = os.path.dirname(CONFIGPATH)
        if not xbmcvfs.exists(base_path):
            xbmcvfs.mkdirs(base_path)

        with xbmcvfs.File(CONFIGPATH, 'w') as fh:
            fh.write(json.dumps(addon_pathes))

    def deletePaths(self, paths, paths_del):
        for index_del in sorted(paths_del, reverse=True):
            del paths[index_del]
        with xbmcvfs.File(CONFIGPATH, 'w') as fh:
            fh.write(json.dumps(paths))

    def readExisting(self):
        if not xbmcvfs.exists(CONFIGPATH):
            return []
        try:
            with xbmcvfs.File(CONFIGPATH, 'r') as fh:
                addon_pathes = fh.read()
        except Exception:
            addon_pathes = '[]'
        return json.loads(addon_pathes)

    def getNextId(self, addon_pathes):
        if not addon_pathes:
            return 0
        return addon_pathes[-1]['id'] + 1
