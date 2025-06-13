#!/usr/bin/python
# coding: utf-8

import xbmc
import xbmcgui
import xbmcvfs
import xbmcaddon
from typing import List, Dict, Union

from resources.lib.helper import json_call

ADDON = xbmcaddon.Addon()

class MenuActionManager:
    """
    Gerencia ações do menu, incluindo tipos, ações e playlists.
    """

    def __init__(self) -> None:
        self.thumbsizes: List[str] = [
            ADDON.getLocalizedString(30294),
            ADDON.getLocalizedString(30293),
            ADDON.getLocalizedString(30292)
        ]

        self.actiontypes: List[str] = [
            ADDON.getLocalizedString(30100),
            ADDON.getLocalizedString(30101),
            ADDON.getLocalizedString(30102),
            ADDON.getLocalizedString(30103),
            ADDON.getLocalizedString(30104),
            ADDON.getLocalizedString(30105),
            ADDON.getLocalizedString(30106),
            ADDON.getLocalizedString(30107),
            ADDON.getLocalizedString(30108),
            ADDON.getLocalizedString(30109),
            ADDON.getLocalizedString(30110)
        ]

        self.actionconstraints: List[Dict[str, str]] = [
            {'cond': 'Library.HasContent(movies)', 'alt_path': 'ActivateWindow(Videos,sources://video/,return)'},
            {'cond': 'Library.HasContent(tvshows)', 'alt_path': 'ActivateWindow(Videos,sources://video/,return)'},
            {'cond': 'Library.HasContent(music)', 'alt_path': 'ActivateWindow(Music,sources://music/,return)'},
            {'cond': 'Library.HasContent(musicvideos)', 'alt_path': 'ActivateWindow(Videos,sources://video/,return)'}
        ]

        self.actions: List[List[Dict[str, str]]] = [
            # 0: Links to Video Database
            [
                {'label': '342', 'path': 'titles', 'thumb': 'DefaultMovies.png'},
                {'label': '20382', 'path': 'recentlyaddedmovies', 'thumb': 'DefaultRecentlyAddedMovies.png'},
                {'label': '135', 'path': 'genres', 'thumb': 'DefaultGenre.png'},
                {'label': '652', 'path': 'years', 'thumb': 'DefaultYear.png'},
                {'label': '344', 'path': 'actors', 'thumb': 'DefaultActor.png'},
                {'label': '20348', 'path': 'directors', 'thumb': 'DefaultDirector.png'},
                {'label': '20388', 'path': 'studios', 'thumb': 'DefaultStudios.png'},
                {'label': '20434', 'path': 'sets', 'thumb': 'DefaultSets.png'},
                {'label': '20451', 'path': 'countries', 'thumb': 'DefaultCountry.png'},
                {'label': '20459', 'path': 'tags', 'thumb': 'DefaultTags.png'}
            ],
            # 1: Links to TV Show Database
            [
                {'label': '20343', 'path': 'titles', 'thumb': 'DefaultTVShows.png'},
                {'label': '20382', 'path': 'recentlyaddedepisodes', 'thumb': 'DefaultRecentlyAddedEpisodes.png'},
                {'label': '575', 'path': 'inprogresstvshows', 'thumb': 'DefaultInProgressShows.png'},
                {'label': '135', 'path': 'genres', 'thumb': 'DefaultGenre.png'},
                {'label': '652', 'path': 'years', 'thumb': 'DefaultYear.png'},
                {'label': '344', 'path': 'actors', 'thumb': 'DefaultActor.png'},
                {'label': '20348', 'path': 'directors', 'thumb': 'DefaultDirector.png'},
                {'label': '20388', 'path': 'studios', 'thumb': 'DefaultStudios.png'},
                {'label': '20459', 'path': 'tags', 'thumb': 'DefaultTags.png'}
            ],
            # 2: Links to Music Database
            [
                {'label': '133', 'path': 'artists', 'thumb': 'DefaultMusicArtists.png'},
                {'label': '135', 'path': 'genres', 'thumb': 'DefaultMusicGenres.png'},
                {'label': '132', 'path': 'albums', 'thumb': 'DefaultMusicAlbums.png'},
                {'label': '1050', 'path': 'singles', 'thumb': 'DefaultMusicSongs.png'},
                {'label': '134', 'path': 'songs', 'thumb': 'DefaultMusicSongs.png'},
                {'label': '652', 'path': 'years', 'thumb': 'DefaultMusicYears.png'},
                {'label': '517', 'path': 'recentlyplayedalbums', 'thumb': 'DefaultMusicRecentlyPlayed.png'},
                {'label': '359', 'path': 'recentlyaddedalbums', 'thumb': 'DefaultMusicRecentlyAdded.png'},
                {'label': '521', 'path': 'compilations', 'thumb': 'DefaultMusicCompilations.png'}
            ],
            # 3: Links to Music Video Database
            [
                {'label': '20389', 'path': 'titles', 'thumb': 'DefaultMusicVideos.png'},
                {'label': '20382', 'path': 'recentlyaddedmusicvideos', 'thumb': 'DefaultRecentlyAddedMusicVideos.png'},
                {'label': '135', 'path': 'genres', 'thumb': 'DefaultGenre.png'},
                {'label': '652', 'path': 'years', 'thumb': 'DefaultYear.png'},
                {'label': '133', 'path': 'artists', 'thumb': 'DefaultMusicArtists.png'},
                {'label': '20348', 'path': 'directors', 'thumb': 'DefaultDirector.png'},
                {'label': '132', 'path': 'albums', 'thumb': 'DefaultMusicAlbums.png'},
                {'label': '20388', 'path': 'studios', 'thumb': 'DefaultStudios.png'},
                {'label': '20459', 'path': 'tags', 'thumb': 'DefaultTags.png'}
            ],
            # 4: Live TV Windows
            [
                {'label': '19019', 'path': 'TVChannels', 'thumb': 'DefaultAddonPeripheral.png'},
                {'label': '19069', 'path': 'TVGuide', 'thumb': 'icons/pvr/epg.png'},
                {'label': '19017', 'path': 'TVRecordings', 'thumb': 'icons/pvr/recording_small.png'},
                {'label': '19040', 'path': 'TVTimers', 'thumb': 'icons/pvr/timer_small.png'},
                {'label': '19138', 'path': 'TVTimerRules', 'thumb': 'icons/pvr/timer-rule.png'},
                {'label': '137', 'path': 'TVSearch', 'thumb': 'DefaultAddonsSearch.png'}
            ],
            # 5: Live Radio Windows
            [
                {'label': '19019', 'path': 'RadioChannels', 'thumb': 'DefaultAddonPeripheral.png'},
                {'label': '19069', 'path': 'RadioGuide', 'thumb': 'icons/pvr/epg.png'},
                {'label': '19017', 'path': 'RadioRecordings', 'thumb': 'icons/pvr/recording_small.png'},
                {'label': '19040', 'path': 'RadioTimers', 'thumb': 'icons/pvr/timer_small.png'},
                {'label': '19138', 'path': 'RadioTimerRules', 'thumb': 'icons/pvr/timer-rule.png'},
                {'label': '137', 'path': 'RadioSearch', 'thumb': 'DefaultAddonsSearch.png'}
            ],
            # 6: Common Windows
            [
                {'label': '24001', 'path': 'addonbrowser', 'thumb': 'icons/mainmenu/addons.png'},
                {'label': '1', 'path': 'Pictures', 'thumb': 'icons/mainmenu/pictures.png'},
                {'label': '3', 'path': 'Videos', 'thumb': 'icons/mainmenu/videos.png'},
                {'label': '10134', 'path': 'favourites', 'thumb': 'icons/mainmenu/favourites.png'},
                {'label': '8', 'path': 'Weather', 'thumb': 'icons/mainmenu/weather.png'},
                {'label': ADDON.getLocalizedString(30289), 'path': 'special://profile/playlists/video/', 'thumb': 'defaultplaylist.png'},
                {'label': ADDON.getLocalizedString(30290), 'path': 'special://profile/playlists/music/', 'thumb': 'defaultplaylist.png'}
            ],
            # 7: Execute Command
            [
                {'label': ADDON.getLocalizedString(30242), 'path': 'PlayPvrTV', 'thumb': 'icons/mainmenu/tv.png'},
                {'label': ADDON.getLocalizedString(30243), 'path': 'PlayPvrRadio', 'thumb': 'icons/mainmenu/radio.png'},
                {'label': ADDON.getLocalizedString(30244), 'path': 'PlayDVD', 'thumb': 'DefaultCdda.png'}
            ]
        ]

        self.playlists: Dict[str, List[Dict[str, str]]] = {'video': [], 'music': []}
        self.addons: List[Dict[str, Union[str, Dict]]] = []

    def getActionType(self, index: int, with_index: bool = True) -> str:
        if index == -1:
            return ADDON.getLocalizedString(30116)
        if 0 <= index < len(self.actiontypes):
            return f"{index+1}. {self.actiontypes[index]}" if with_index else self.actiontypes[index]
        return ""

    def getActionName(self, action_type: int, action_index: int) -> str:
        try:
            label_id = int(self.actions[action_type][action_index]['label'])
            return ADDON.getLocalizedString(label_id)
        except (IndexError, ValueError):
            return ""

    def getThumb(self, action_type: int, action_index: int) -> str:
        try:
            return self.actions[action_type][action_index]['thumb']
        except IndexError:
            return ""

    def getOnClick(self, action_type: int, action_index: int, playlist_index: int = 0) -> str:
        """
        Retorna o comando a ser executado ao clicar na ação.
        """
        try:
            action = self.actions[action_type][action_index]
            path = action['path']

            if action_type in (0, 1, 2, 3):  # Database links
                return f"ActivateWindow(Videos,{path},return)"
            elif action_type in (4, 5):  # Live TV or Radio windows
                return f"ActivateWindow({path})"
            elif action_type == 6:  # Common Windows
                if path == 'addonbrowser':
                    return "ActivateWindow(AddonBrowser,addons://sources/,return)"
                if path.startswith('special://profile/playlists/'):
                    ptype = 'video' if 'video' in path else 'music'
                    if self.playlists.get(ptype):
                        playlist_file = self.playlists[ptype][playlist_index]['file']
                        return f"PlayMedia({playlist_file})"
                else:
                    return f"ActivateWindow({path})"
            elif action_type == 7:  # Execute Command
                if path == 'PlayPvrTV':
                    return "Action(10128)"  # Play PVR TV channel
                if path == 'PlayPvrRadio':
                    return "Action(10130)"  # Play PVR Radio channel
                if path == 'PlayDVD':
                    return "Action(10000)"  # Play DVD
                return ""
            return ""
        except IndexError:
            return ""

    def getActionsCount(self, action_type: int) -> int:
        if 0 <= action_type < len(self.actions):
            return len(self.actions[action_type])
        return 0

    def loadPlaylist(self, playlist_type: str) -> None:
        """
        Carrega playlists do tipo 'video' ou 'music' a partir do diretório de playlists do perfil Kodi.
        """
        if playlist_type not in ('video', 'music'):
            return

        self.playlists[playlist_type].clear()
        playlists_path = xbmcvfs.translatePath(f"special://profile/playlists/{playlist_type}/")

        if not xbmcvfs.exists(playlists_path):
            return

        files = xbmcvfs.listdir(playlists_path)[1]  # Lista arquivos
        for file in sorted(files):
            if file.endswith(('.xsp', '.m3u')):
                full_path = xbmcvfs.translatePath(f"{playlists_path}{file}")
                self.playlists[playlist_type].append({'file': full_path, 'name': file})

    def loadAddons(self) -> None:
        """
        Carrega addons instalados via API JSON do Kodi.
        """
        self.addons.clear()
        json_data = json_call('Addons.GetAddons', {'properties': ['name', 'thumbnail', 'path', 'enabled'], 'type': 'xbmc.addon.video'})
        if json_data and 'result' in json_data and 'addons' in json_data['result']:
            self.addons.extend(json_data['result']['addons'])

    def getAddonName(self, index: int) -> str:
        try:
            return self.addons[index]['name']
        except IndexError:
            return ""

    def getAddonThumb(self, index: int) -> str:
        try:
            return self.addons[index]['thumbnail']
        except IndexError:
            return ""

    def getAddonPath(self, index: int) -> str:
        try:
            return self.addons[index]['path']
        except IndexError:
            return ""

    def getAddonCommand(self, index: int) -> str:
        """
        Retorna o comando para executar o addon.
        """
        try:
            addon_id = self.addons[index]['addonid']
            return f"RunAddon({addon_id})"
        except IndexError:
            return ""

    def getThumbSizes(self) -> List[str]:
        return self.thumbsizes

    def getActionTypes(self) -> List[str]:
        return self.actiontypes
