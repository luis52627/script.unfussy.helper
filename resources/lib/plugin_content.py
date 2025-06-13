#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import xbmcplugin
import xbmcgui
import json
from resources.lib.helper import *
from resources.lib.pvr_running_at import PVRRunningAt
from resources.lib.pvr_timers import PVRTimers
from resources.lib.pvr_channellist import PVRChannelList

#######################################################################################

class PluginContent:

    def __init__(self):
        self.resultlist = []

    def result(self):
        return self.resultlist

    def fetchNextEpisodes(self):
        inprogress_shows = self.getInprogressTVShows()
        for show in inprogress_shows:
            try:
                tvshowid = int(show['tvshowid'])
            except Exception as e:
                log(f"fetchNextEpisodes: invalid tvshowid in show {show}: {e}", xbmc.LOGWARNING)
                continue

            last_played_episode = self.getLastPlayedEpisode(tvshowid)
            if not last_played_episode:
                continue
            next_episode_id = self.getNextEpisode(tvshowid, last_played_episode)
            if next_episode_id > 0:
                next_episode = self.getEpisode(next_episode_id)
                if next_episode:
                    append_items(self.resultlist, [next_episode], type='episodes')

    def fetchActors(self, movie_id, tvshow):
        cast = []
        try:
            if movie_id:
                query = json_call('VideoLibrary.GetMovieDetails',
                                  properties=['cast'],
                                  params={'movieid': int(movie_id)})
                cast = query['result']['moviedetails'].get('cast', [])
            elif tvshow:
                query = json_call('VideoLibrary.GetTVShows',
                                  properties=['cast'],
                                  limit=1,
                                  query_filter={'operator': 'is', 'field': 'title', 'value': tvshow})
                cast = query['result']['tvshows'][0].get('cast', [])
        except Exception as e:
            log(f"fetchActors: error fetching cast: {e}", xbmc.LOGWARNING)

        append_items(self.resultlist, cast, type='cast')

    def fetchRunningAt(self, pointintime, channel_ids):
        running_at = PVRRunningAt()
        if not pvrAvailable():
            log("fetchRunningAt: pvr not available, aborting", xbmc.LOGWARNING)
            return

        try:
            # channel_ids may be JSON string or dict
            if isinstance(channel_ids, str):
                channel_ids_dict = json.loads(channel_ids.replace('-', ','))
            else:
                channel_ids_dict = channel_ids
        except Exception as e:
            log(f"fetchRunningAt: error parsing channel_ids: {e}", xbmc.LOGERROR)
            return

        broadcast_ids = []
        for channel_id in channel_ids_dict.values():
            try:
                bc = running_at.getBroadcastAt(pointintime, channel_id)
                if bc:
                    broadcast_ids.append({'broadcastid': bc['broadcastid'], 'channelid': channel_id})
            except Exception as e:
                log(f"fetchRunningAt: error getting broadcast at channel {channel_id}: {e}", xbmc.LOGWARNING)

        broadcasts = running_at.getBroadcastsById(broadcast_ids)
        append_items(self.resultlist, broadcasts, type='broadcasts')

    def fetchTimers(self):
        if not pvrAvailable():
            log("fetchTimers: pvr not available, aborting", xbmc.LOGWARNING)
            return
        try:
            ti = PVRTimers()
            timers = ti.fetchTimers()
            for t in timers:
                channel = ti.fetchChannel(t['channelid'])
                t['channelicon'] = channel['icon'] if channel else ''
            append_items(self.resultlist, timers, type='timers')
        except Exception as e:
            log(f"fetchTimers: error fetching timers: {e}", xbmc.LOGERROR)

    def fetchBroadcasts(self, channel_num, channel_ids):
        try:
            channel_ids_dict = json.loads(channel_ids) if isinstance(channel_ids, str) else channel_ids
            channel_id = channel_ids_dict.get(str(channel_num)) or channel_ids_dict.get(channel_num)
            if not channel_id:
                log(f"fetchBroadcasts: channel_num {channel_num} not found in channel_ids", xbmc.LOGWARNING)
                return
        except Exception as e:
            log(f"fetchBroadcasts: error parsing channel_ids or getting channel_id: {e}", xbmc.LOGERROR)
            return

        cl = PVRChannelList()
        broadcasts = cl.fetchBroadcasts(channel_id)
        append_items(self.resultlist, broadcasts, type='broadcasts_short')

    #######################################################################################
    # Private helper methods
    #######################################################################################

    def getInprogressTVShows(self):
        try:
            query = json_call('VideoLibrary.GetTVShows',
                              properties=[],
                              limit=25,
                              sort={"method": "lastplayed", "order": "descending"},
                              query_filter={'field': 'inprogress', 'operator': 'true', 'value': ''})
            tvshows = query['result'].get('tvshows', [])
            return tvshows
        except Exception:
            log('getInprogressTVShows: No Inprogress TVShows found or error.', xbmc.LOGWARNING)
            return []

    def getLastPlayedEpisode(self, tvshowid):
        try:
            query = json_call('VideoLibrary.GetEpisodes',
                              properties=['season', 'episodeid'],
                              limit=1,
                              sort={"method": "lastplayed", "order": "descending"},
                              query_filter={"field": "playcount", "operator": "isnot", "value": "0"},
                              params={'tvshowid': tvshowid})
            last_played = query['result'].get('episodes', [])
            if last_played:
                return last_played[0]
        except Exception:
            log('getLastPlayedEpisode: No Last Played Episode found or error.', xbmc.LOGWARNING)
        return None

    def getNextEpisode(self, tvshowid, last_played_episode):
        # Adjust logic to find next episode based on season and episode number
        try:
            current_season = last_played_episode.get('season', 0)
            current_episode_id = last_played_episode.get('episodeid')
            query = json_call('VideoLibrary.GetEpisodes',
                              properties=['episodeid', 'season'],
                              sort={"method": "episode"},
                              query_filter={"field": "season", "operator": "greaterthanorequal", "value": str(current_season)},
                              params={'tvshowid': tvshowid})
            episodes = query['result'].get('episodes', [])
            found = False
            for episode in episodes:
                if found:
                    return episode['episodeid']
                if episode['episodeid'] == current_episode_id:
                    found = True
            return 0
        except Exception as e:
            log(f"getNextEpisode: error fetching next episode: {e}", xbmc.LOGERROR)
            return 0

    def getEpisode(self, episodeid):
        try:
            query = json_call('VideoLibrary.GetEpisodeDetails',
                              properties=episode_properties,
                              params={'episodeid': episodeid})
            episode = query['result'].get('episodedetails', {})
            return episode
        except Exception as e:
            log(f"getEpisode: error fetching episode details for id {episodeid}: {e}", xbmc.LOGWARNING)
            return {}
