# -*- coding: utf-8 -*-
#########################################################
# python
import os
import sys
import logging
import traceback
import json
import re
import urllib
import requests
import threading

# third-party
from lxml import html, etree

# sjva 공용

# 패키지
from .plugin import logger, package_name
from .model import ModelSetting, ModelChannel
from source_base import SourceBase

#########################################################

class YoutubedlItem:
    ch_list = None

    def __init__(self, id, title, url):
        self.id = id.strip()
        self.title = title.strip()
        self.url = url.strip()
        YoutubedlItem.ch_list[id] = self

class SourceYoutubedl(SourceBase):
    channel_list = None

    @staticmethod
    def install():
        try:
            def func():
                import system
                import framework.common.util as CommonUtil
                commands = [
                    ['msg', u'잠시만 기다려주세요.'],
                    ['pip', 'install', '--upgrade', 'pip'],
                    ['pip', 'install', '--upgrade', 'setuptools'],
                    ['pip', 'install', '--upgrade', 'youtube-dl'],
                    ['msg', u'설치가 완료되었습니다.']
                ]
                system.SystemLogicCommand.start('설치', commands)
            t = threading.Thread(target=func, args=())
            t.setDaemon(True)
            t.start()
        except Exception as e: 
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())


    @staticmethod
    def is_installed():
        try:
            import youtube_dl
            return True
        except Exception as e: 
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())
        return False


    @classmethod
    def get_channel_list(cls):
        try:
            tmp = ModelSetting.get('youtubedl_list')
            YoutubedlItem.ch_list = {}
            ret = []
            for item in tmp.split('\n'):
                if item.strip() == '':
                    continue
                tmp2 = item.split('|')
                if len(tmp2) != 3:
                    continue
                c = ModelChannel(cls.source_name, tmp2[0], tmp2[1], None, True)
                YoutubedlItem(tmp2[0], tmp2[1], tmp2[2])
                c.current = ''
                ret.append(c)
        except Exception as e:
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())
        return ret

    @classmethod
    def get_url(cls, source_id, quality, mode):
        try:
            logger.debug('source_id:%s, quality:%s, mode:%s', source_id, quality, mode)
            import youtube_dl
            ydl_opts = {}
            if ModelSetting.get_bool('youtubedl_use_proxy'):
                ydl_opts['proxy'] = ModelSetting.get('youtubedl_proxy_url')
            ydl = youtube_dl.YoutubeDL(ydl_opts)
            target_url = YoutubedlItem.ch_list[source_id].url

            logger.debug(target_url)
            if target_url.startswith('YOUTUBE_'):
                target_idx = int(target_url.split('_')[1]) - 1
                live_home = 'https://www.youtube.com/playlist?list=PLU12uITxBEPGpEPrYAxJvNDP6Ugx2jmUx'
                data = requests.get(live_home).content
                root = html.fromstring(data)
                tags = root.xpath('//ytd-playlist-video-renderer//a[@class="yt-simple-endpoint style-scope ytd-playlist-video-renderer"]')
                target_url = 'https://www.youtube.com' + tags[target_idx].attrib['href'].split('&')[0]
            result = ydl.extract_info(target_url, download=False)
            logger.debug('Formats len : %s', len(result['formats']))
            if 'formats' in result:
                #formats = result['formats']
                url = result['formats'][-1]['url']
            if mode == 'web_play':
                return 'return_after_read', url 
            return 'redirect', url
        except Exception as e:
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())
        return

    @classmethod
    def get_return_data(cls, source_id, url, mode):
        try:
            data = requests.get(url).content
            return cls.change_redirect_data(data)
        except Exception as e:
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())
        return data
















