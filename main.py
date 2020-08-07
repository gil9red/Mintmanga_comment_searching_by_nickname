#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'ipetrash'


from urllib.parse import urljoin
from urllib.request import urlopen

import time

from lxml import etree


# TODO: сделать вебсервер
# TODO: указывать страницу коммента
# TODO: заменить handler_range_progress_func на handler_max_progress_func,
# т.к. "range" в данной функции всегда начинается с 0
def collect_user_comments(
        user, url_manga,
        handler_log_func=print,
        is_stop_func=None,
        handler_progress_func=None,
        handler_range_progress_func=None,
    ):
    """Скрипт ищет комментарии указанного пользователя сайта https://readmanga.live/ и выводит их.

    :param user:
    :param url_manga:
    :param handler_log_func:
    :param is_stop_func:
    :param handler_progress_func:
    :param handler_range_progress_func:
    """

    number = 0

    try:
        is_stop = lambda x=None: is_stop_func and is_stop_func()
        if is_stop():
            return

        log = lambda x=None: handler_log_func and handler_log_func(x)
        progress_func = lambda i=None: handler_progress_func and handler_progress_func(i)

        while True:
            try:
                html = urlopen(url_manga).read()
                break

            except:
                log('Проблема при обращении к "{}", ожидание 5 минут'.format(url_manga))

                import time
                time.sleep(5 * 60)

        root = etree.HTML(html)

        # Из комбобокса вытаскиванием список всех глав
        all_option_list = root.xpath('//*[@id="chapterSelectorSelect"]/option')
        number_chapters = len(all_option_list)

        handler_range_progress_func and handler_range_progress_func(0, number_chapters)

        for i, option in enumerate(reversed(all_option_list), 1):
            # Если функция is_stop_func определена и возвращает True, прерываем поиск
            if is_stop():
                return

            title = option.text

            # Относительную ссылку на главу делаем абсолютной
            volume_url = urljoin(url_manga, option.attrib['value'])
            log('Глава "{}": {}'.format(title, volume_url))

            while True:
                try:
                    html = urlopen(volume_url).read()
                    break

                except:
                    log('Проблема при обращении к "{}", ожидание 5 минут'.format(volume_url))
                    time.sleep(5 * 60)

            root = etree.HTML(html)

            comments = list()

            # Сбор всех комментариев главы
            for div in root.xpath('//*[@id="twitts"]/div/div'):
                a = div.xpath('a')
                span = div.xpath('div[@class="mess"]')

                # Возможны div без комментов внутри, поэтому проверяем наличие тегов a (логин) и span (текст)
                if a and span:
                    a = a[0]
                    span = span[0]

                    if a.text == user:
                        comments.append((a.text, span.text))

            # Если список не пуст
            if comments:
                number += len(comments)

                for login, text in comments:
                    log('  {}: {}'.format(login, text))

                log('')

            progress_func(i)

    finally:
        log('')
        log('Найдено {} комментов "{}".'.format(number, user))


if __name__ == '__main__':
    user = 'Rihoko7'
    url = 'http://mintmanga.com/tokyo_ghoul/vol1/1?mature=1'
    collect_user_comments(user, url)
