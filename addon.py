from xbmcswift2 import Plugin
from resources.lib.api import XBMC4PlayersApi, NetworkError

STRINGS = {
    'latest_videos': 30000,
    'next': 30001,
    'popular_videos': 30002,
    'network_error': 30200,
    'videos_by_game': 30003,
}

plugin = Plugin()
api = XBMC4PlayersApi()


@plugin.route('/')
def show_root_menu():
    items = [
        {'label': _('latest_videos'),
         'path': plugin.url_for('latest_videos')},
        {'label': _('popular_videos'),
         'path': plugin.url_for('popular_videos')},
    ]
    return plugin.finish(items)


@plugin.route('/latest_videos/')
@plugin.route('/latest_videos/<game_id>/', name='videos_by_game')
def latest_videos(game_id=None):
    older_than = int(plugin.request.args.get('older_than', [0])[0])
    if game_id:
        videos = api.get_videos_by_game(older_than=older_than, game_id=game_id)
    else:
        videos = api.get_latest_videos(older_than=older_than)
    most_recent_ts = min((v['ts'] for v in videos))
    items = __format_videos(videos)
    if not game_id:
        items.append({
            'label': '>> %s >>' % _('next'),
            'path': plugin.url_for(
                endpoint='latest_videos',
                older_than=most_recent_ts
            )
        })
    finish_kwargs = {
        'update_listing': 'older_than' in plugin.request.args
    }
    if plugin.get_setting('force_viewmode') == 'true':
        finish_kwargs['view_mode'] = 'thumbnail'
    return plugin.finish(items, **finish_kwargs)


@plugin.route('/popular_videos/')
def popular_videos():
    page = int(plugin.request.args.get('page', ['1'])[0])
    videos = api.get_popular_videos(page=page)
    items = __format_videos(videos)
    items.append({
        'label': '>> %s >>' % _('next'),
        'path': plugin.url_for(
            endpoint='popular_videos',
            page=(page + 1)
        )
    })

    finish_kwargs = {
        'update_listing': 'page' in plugin.request.args
    }
    if plugin.get_setting('force_viewmode') == 'true':
        finish_kwargs['view_mode'] = 'thumbnail'
    return plugin.finish(items, **finish_kwargs)


@plugin.route('/play/<url>/')
def play_video(url):
    return plugin.set_resolved_url(url)


def __format_videos(videos):
    quality = ('normal', 'hq')[int(plugin.get_setting('quality'))]
    videos = [{
        'label': '%s: %s' % (video['game']['title'], video['video_title']),
        'thumbnail': video['thumb'],
        'info': {
            'original_title': video['game']['title'],
            'tagline': video['video_title'],
            'size': video['streams'][quality]['size'],
            'date': video['date'],
            'genre': video['game']['genre'],
            'studio': video['game']['studio'],
            'count': i,
        },
        'is_playable': True,
        'context_menu': [(
            _('videos_by_game'),
            'Container.Update(%s)' % plugin.url_for(
                endpoint='videos_by_game',
                game_id=str(video['game']['id'])
            )
        )],
        # 'stream_info': {
        #     'video': {'duration': video['duration']}
        # },
        'path': plugin.url_for(
            endpoint='play_video',
            url=video['streams'][quality]['url']
        ),
    } for i, video in enumerate(videos)]
    return videos


def _(string_id):
    if string_id in STRINGS:
        return plugin.get_string(STRINGS[string_id])
    else:
        plugin.log.warning('String is missing: %s' % string_id)
        return string_id


if __name__ == '__main__':
    try:
        plugin.run()
    except NetworkError:
        plugin.notify(msg=_('network_error'))
