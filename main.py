#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'ipetrash'


from collections import defaultdict
from urllib.parse import urljoin
from urllib.request import urlopen
import time
import re

from bs4 import BeautifulSoup, Tag


PATTERN_PAGE_FROM_CLASS = re.compile(r'cm_(\d+)')


def _get_number_page(page_el: Tag) -> int:
    # Example: 'hide cm_0 cm' -> 1
    page_class = ' '.join(page_el.get_attribute_list('class'))

    m = PATTERN_PAGE_FROM_CLASS.search(page_class)
    if not m:
        raise Exception(f'Not found page from class: {page_class}')

    # Страницы начинаются с 0
    return int(m.group(1)) + 1


def collect_user_comments(
    user: str,
    url_manga: str,
    handler_log_func=print,
    is_stop_func=lambda: False,
    handler_progress_func=lambda i: None,
    handler_max_progress_func=lambda max_val: None,
):
    """
    Скрипт ищет комментарии указанного пользователя сайта https://readmanga.live/ и выводит их.

    """

    number = 0

    log = lambda x=None: handler_log_func(x)

    try:
        is_stop = lambda x=None: is_stop_func()
        if is_stop():
            return

        progress_func = lambda i=None: handler_progress_func(i)

        while True:
            try:
                html = urlopen(url_manga).read()
                break
            except:
                log(f'[-] Проблема при обращении к "{url_manga}", ожидание 5 минут')
                time.sleep(5 * 60)

        root = BeautifulSoup(html, 'html.parser')

        # Из комбобокса вытаскиванием список всех глав
        all_option_list = root.select('#chapterSelectorSelect > option')
        number_chapters = len(all_option_list)

        handler_max_progress_func(number_chapters)

        for i, option in enumerate(reversed(all_option_list), 1):
            # Если функция is_stop_func определена и возвращает True, прерываем поиск
            if is_stop():
                return

            title = option.get_text(strip=True)

            # Относительную ссылку на главу делаем абсолютной
            volume_url = urljoin(url_manga, option['value'])
            log(f'Глава {title!r}: {volume_url}')

            while True:
                try:
                    html = urlopen(volume_url).read()
                    break
                except:
                    log(f'[-] Проблема при обращении к "{volume_url}", ожидание 5 минут')
                    time.sleep(5 * 60)

            root = BeautifulSoup(html, 'html.parser')
            page_by_comments = defaultdict(list)

            # Перебор страниц комментариев
            for div_page in root.select('#twitts > div.cm'):
                page = _get_number_page(div_page)

                # Перебор комментариев
                for div_comment in div_page.select('div.comm'):
                    comm_user = div_comment.a.get_text(strip=True)
                    if comm_user == user:
                        mess = div_comment.select_one('div.mess').get_text(strip=True)
                        page_by_comments[page].append((user, mess))

            # Если список не пуст
            if page_by_comments:
                # Сортировка по страницам
                page_by_comments_items = sorted(page_by_comments.items(), key=lambda x: x[0])

                for page, (comments) in page_by_comments_items:
                    number += len(comments)

                    log(f'    Страница {page}:')
                    for login, text in comments:
                        log(f'        {login}: {text!r}')

                log('')

            progress_func(i)

    finally:
        log('')
        log(f'Найдено {number} комментов {user!r}.')


if __name__ == '__main__':
    user = 'Rihoko7'
    url = 'https://mintmanga.live/tokiiskii_gul/vol1/1?mtr=1'
    collect_user_comments(user, url)
