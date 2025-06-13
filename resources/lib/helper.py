#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import xbmc
import xbmcaddon
import xbmcgui
import json
import time
from datetime import datetime, timedelta

########################

ADDON = xbmcaddon.Addon()
ADDON_ID = ADDON.getAddonInfo('id')

LOG_ENABLED = ADDON.getSettingBool('log')
DEBUGLOG_ENABLED = ADDON.getSettingBool('debuglog')

########################

def log(txt, loglevel=xbmc.LOGINFO, force=False):
    if ((loglevel in [xbmc.LOGINFO, xbmc.LOGWARNING] and LOG_ENABLED) or 
        (loglevel == xbmc.LOGDEBUG and DEBUGLOG_ENABLED) or force):
        message = f'[ {ADDON_ID} ] {txt}'
        xbmc.log(message, level=loglevel)

def json_call(method, properties=None, sort=None, query_filter=None, limit=None, params=None, item=None):
    json_string = {'jsonrpc': '2.0', 'id': 1, 'method': method, 'params': {}}

    if properties is not None:
        json_string['params']['properties'] = properties
    if limit is not None:
        json_string['params']['limits'] = {'start': 0, 'end': limit}
    if sort is not None:
        json_string['params']['sort'] = sort
    if query_filter is not None:
        json_string['params']['filter'] = query_filter
    if item is not None:
        json_string['params']['item'] = item
    if params is not None:
        json_string['params'].update(params)

    json_string = json.dumps(json_string)
    result = xbmc.executeJSONRPC(json_string)
    result = json.loads(result)

    log(f'json-string: {json_string}', xbmc.LOGDEBUG)
    log(f'json-result: {result}', xbmc.LOGDEBUG)

    return result

def visible(condition):
    return xbmc.getCondVisibility(condition)

def pvrAvailable():
    retries = 0
    num_retries = 50
    while retries < num_retries:
        channels = json_call('PVR.GetChannels', limit=1, params={'channelgroupid': 'alltv'})
        try:
            channel_id = channels['result']['channels'][0]['channelid']
            broadcast = json_call('PVR.GetBroadcasts', params={'channelid': channel_id}, limit=1)
            if 'broadcasts' in broadcast['result']:
                xbmc.sleep(200)
                log("pvrAvailable: success...continue")
                return True
        except Exception:
            retries += 1
            log("pvrAvailable: retrying...", xbmc.LOGWARNING)
            xbmc.sleep(500)
    return False

def getTimeFromString(str_time, format, utc_offset=None):
    try:
        dt = datetime.strptime(str_time, format)
        if utc_offset:
            dt += utc_offset
        return dt
    except ValueError:
        return None

def getUtcOffset():
    return datetime.now() - datetime.utcnow()

########################
# Additional Functions and Data Lists
########################

movie_properties = [
    'title', 'originaltitle', 'votes', 'playcount', 'year', 'genre', 'studio',
    'country', 'tagline', 'plot', 'runtime', 'file', 'plotoutline', 'lastplayed',
    'trailer', 'rating', 'resume', 'art', 'streamdetails', 'mpaa', 'director',
    'writer', 'cast', 'dateadded', 'imdbnumber'
]

def append_items(li, json_query, type):
    parsers = {
        'movies': parse_movies,
        'tvshows': parse_tvshows,
        'seasons': parse_seasons,
        'episodes': parse_episodes,
        'broadcasts': parse_broadcast,
    }
    if type in parsers:
        for item in json_query:
            parsers[type](li, item)
    else:
        log(f"append_items: unsupported type '{type}'", xbmc.LOGWARNING)

def parse_movies(li, item):
    cast = [c['name'] for c in item.get('cast', [])]
    resume = item.get('resume', {})
    li_item = xbmcgui.ListItem(label=item['title'])
    li_item.setInfo('video', {
        'Title': item['title'],
        'OriginalTitle': item.get('originaltitle', ''),
        'Year': item.get('year', ''),
        'Genre': ', '.join(item.get('genre', [])),
        'Studio': ', '.join(item.get('studio', [])),
        'Country': ', '.join(item.get('country', [])),
        'Plot': item.get('plot', ''),
        'Rating': str(item.get('rating', '')),
        'Votes': item.get('votes', ''),
        'MPAA': item.get('mpaa', ''),
        'Playcount': item.get('playcount', 0),
        'Cast': cast,
        'Trailer': item.get('trailer', ''),
    })
    li_item.setProperty('resumetime', str(resume.get('position', 0)))
    li_item.setProperty('totaltime', str(resume.get('total', 0)))
    li_item.setArt(item.get('art', {}))
    li.append((item['file'], li_item, False))

def parse_tvshows(li, item):
    li_item = xbmcgui.ListItem(label=item['title'])
    li_item.setInfo('video', {
        'Title': item['title'],
        'Year': item.get('year', ''),
        'Genre': ', '.join(item.get('genre', [])),
        'Plot': item.get('plot', ''),
        'Rating': str(item.get('rating', '')),
        'Votes': item.get('votes', ''),
        'MPAA': item.get('mpaa', ''),
        'Playcount': item.get('playcount', 0),
        'Season': item.get('season', 0),
        'Episode': item.get('episode', 0),
    })
    li_item.setArt(item.get('art', {}))
    li.append((f'videodb://tvshows/titles/{item["tvshowid"]}/', li_item, True))

def parse_broadcast(li, item):
    li_item = xbmcgui.ListItem(label=item['title'])
    li_item.setInfo('video', {
        'Title': item['title'],
        'Plot': item.get('plot', ''),
    })
    li_item.setArt({'icon': item.get('thumbnail', '')})
    li.append(('', li_item, False))

########################
# Main Execution Block
########################
if __name__ == "__main__":
    log("Script for Kodi 21 initialized", xbmc.LOGINFO)
