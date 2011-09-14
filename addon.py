from xbmcswift import Plugin
import resources.lib.scraper as scraper

plugin = Plugin('4Players Videos', 'plugin.video.4players', __file__)


@plugin.route('/', default=True)
def show_filters():
    filters = scraper.getFilters()
    items = [{'label': filter,
              'url': plugin.url_for('filter', filter=filter, page='1'),
             } for filter in filters]
    return plugin.add_items(items)


@plugin.route('/filter/<filter>/<page>/', name='filter')
def show_videos(filter, page):
    videos, last_page_num = scraper.getVideos(filter, page)
    items = [{'label': video['title'],
              'thumbnail': video['image'],
              'info': {'duration': video['length'],
                       'releasedate': video['date']},
              'url': plugin.url_for('watch_video', url=video['url']),
              'is_folder': False,
              'is_playable': True,
             } for video in videos]
    if int(page) < int(last_page_num):
        next_page = str(int(page) + 1)
        items.append({'label': '>> Page %s >>' % next_page,
                      'url': plugin.url_for('filter',
                                            filter=filter,
                                            page=next_page)})
    if int(page) > 1:
        prev_page = str(int(page) - 1)
        items.insert(0, {'label': '<< Page %s <<' % prev_page,
                         'url': plugin.url_for('filter',
                                               filter=filter,
                                               page=prev_page)})
    return plugin.add_items(items)


@plugin.route('/watch/<url>/')
def watch_video(url):
    video_url = scraper.getVideoFile(url)
    return plugin.set_resolved_url(video_url)


if __name__ == '__main__':
    plugin.run()
