#!/usr/bin/python
# -*- coding: utf-8 -*-
#
#     Copyright (C) 2013 Tristan Fischer (sphere@dersphere.de)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#

import json
from datetime import date
from urllib import quote
from urllib2 import urlopen, Request, HTTPError, URLError

API_URL = 'http://app.4players.de/services/app/data.php'


class NetworkError(Exception):
    pass


class XBMC4PlayersApi(object):

    USER_AGENT = 'XBMC4PlayersApi'

    def __init__(self):
        self._game_infos = {}
        pass

    def get_systems(self):
        return [{
            'id': system['shortname'],
            'name': system['longname']
        } for system in self.__api_call('getSysteme')['Systeme']]

    def get_latest_videos(self, limit=50, older_than=0):
        params = (
            0,  # video_id
            limit,  # limit
            0,  # newer_than
            older_than,  # older_than
            0,  # reviews_only
            0,  # system filter
            1,  # include spielinfo
        )
        videos = self.__api_call('getVideos', *params)['Video']
        return self.__format_videos(videos)

    def get_popular_videos(self, limit=50, page=1):
        offset = int(limit) * (int(page) - 1)
        params = (
            limit,  # limit
            offset,  # offset
            0,  # system filter
            1,  # include spielinfo
        )
        videos = self.__api_call('getVideosByViews', *params)['Video']
        return self.__format_videos(videos)

    def get_videos_by_game(self, game_id, limit=50, older_than=0):
        params = (
            game_id,  # game_id
            limit,  # limit
            0,  # newer_than
            older_than,  # older_than
        )
        videos = self.__api_call('getVideosBySpiel', *params)['Video']
        return self.__format_videos(videos)

    def get_games(self, search_string, limit=50):
        params = (
            search_string,  # search_string
            limit  # limit
        )
        games = self.__api_call('getSpieleBySuchbegriff', *params)['GameInfo']
        return self.__format_games(games)

    def _get_game_info(self, game_id):
        params = (
            game_id,  # game_id
            0,  # newer than
        )
        return self.__api_call('getSpielinfo', *params)['GameInfo']

    def __format_videos(self, raw_videos):
        videos = [{
            'id': video['id'],
            'video_title': video['beschreibung'],
            'rating': video['rating'],
            'ts': video['datum'],
            'date': self.__format_date(video['datum']),
            'duration': self.__format_duration(video['laufzeit']),
            'thumb': self.__format_thumb(video['thumb']),
            'game': self.__format_game(video['spielinfo']),
            'streams': {
                'normal': {
                    'url': video['url'],
                    'size': video['filesize']
                },
                'hq': {
                    'url': video['urlHQ'],
                    'size': video['filesizeHQ']
                }
            }
        } for video in raw_videos]
        return videos

    def __format_games(self, raw_games):
        games = [{
            'id': game['id'],
            'title': game['name'],
            'thumb': game['systeme'][0]['cover_big'],
            'genre': game['subgenre'],
            'studio': game['hersteller']
        } for game in raw_games]
        return games

    def __format_game(self, game_info):
        if not isinstance(game_info, list):
            game_id = game_info['id']
            if game_id in self._game_infos:
                game_info = self._game_infos[game_id]
            else:
                self._game_infos[game_id] = self._get_game_info(game_id)
            game_info = self._game_infos[game_id]
        else:
            self._game_infos[game_info[0]['id']] = game_info
        game = {
            'id': game_info[0]['id'],
            'title': game_info[0]['name'],
            'genre': game_info[0]['subgenre'],
            'studio': game_info[0]['hersteller'],
        }
        return game

    @staticmethod
    def __format_thumb(url):
        return url.replace('-thumb160x90.jpg', '-screenshot.jpg')

    @staticmethod
    def __format_date(timestamp):
        f = '%d.%m.%Y'
        return date.fromtimestamp(timestamp).strftime(f)

    @staticmethod
    def __format_duration(duration_str):
        if ':' in duration_str:
            m, s = duration_str.split(' ')[0].split(':', 1)
            return int(int(m) * 60 + int(s))
        else:
            return 0

    def __api_call(self, method, *params):
        parts = [API_URL, method] + [quote(str(p)) for p in params]
        url = '/'.join(parts)
        req = Request(url)
        req.add_header('User Agent', self.USER_AGENT)
        log('Opening URL: %s' % url)
        try:
            response = urlopen(req).read()
        except HTTPError, error:
            raise NetworkError('HTTPError: %s' % error)
        except URLError, error:
            raise NetworkError('URLError: %s' % error)
        log('got %d bytes' % len(response))
        json_data = json.loads(response)
        return json_data


def log(msg):
    print '[XBMC4PlayersApi]: %s' % msg
