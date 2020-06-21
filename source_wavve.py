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

# third-party
from sqlitedict import SqliteDict
import requests

# sjva 공용
from framework import app, db, scheduler, path_app_root, path_data

# 패키지
from .plugin import logger, package_name
from .model import ModelSetting, ModelChannel
from .source_base import SourceBase
import framework.wavve.api as Wavve

#########################################################



class SourceWavve(SourceBase):
    @classmethod
    def prepare(cls, source_id, source_pw, arg):
        cls.login_data = None
        if ModelSetting.get('wavve_credential') == '':
            if source_id != '' and source_pw != '':
                cls.login_data = Wavve.do_login(source_id, source_pw)
                ModelSetting.set('wavve_credential', cls.login_data)
        else:
            cls.login_data = ModelSetting.get('wavve_credential')

    @classmethod
    def get_channel_list(cls):
        try:
            data = Wavve.live_all_channels()
            ret = []
            for item in data['list']:
                img = 'https://' + item['tvimage'] if item['tvimage'] != '' else ''
                if img != '':
                    tmp = img.split('/')
                    tmp[-1] = urllib.quote(tmp[-1].encode('utf8'))
                    img = '/'.join(tmp)
                c = ModelChannel(cls.source_name, item['channelid'], item['channelname'], img, (item['type']=='video'))
                c.current = item['title']
                ret.append(c)
                #logger.debug('%s - %s', item['channelname'], item['tvimage'])
                #if item['channelname'] in ['MBC', 'SBS']:
                #    logger.debug(item)
        except Exception as e:
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())
        return ret

    @classmethod
    def get_url(cls, source_id, quality, mode, retry=True):
        try:
            proxy = None
            if ModelSetting.get_bool('wavve_use_proxy'):
                proxy = ModelSetting.get('wavve_proxy_url')
            try:
                data = Wavve.streaming('live', source_id, quality, cls.login_data, proxy=proxy)
                surl = None
                if data is not None:
                    surl = data['playurl']
                if surl is None:
                    raise Exception('no url')
            except:
                if retry:
                    logger.debug('RETRY')
                    cls.login_data = Wavve.do_login(ModelSetting.get('wavve_id'), ModelSetting.get('wavve_pw'))
                    ModelSetting.set('wavve_credential', cls.login_data)
                    return cls.get_url(source_id, quality, mode, retry=False)

            if ModelSetting.get('wavve_streaming_type') == '2':
                return 'redirect', surl
            return 'return_after_read', surl
        except Exception as e:
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())


    @classmethod
    def get_return_data(cls, source_id, url, mode):
        try:
            proxy = None
            if ModelSetting.get_bool('wavve_use_proxy'):
                proxy = ModelSetting.get('wavve_proxy_url')

            proxies = None
            if proxy is not None:
                proxies={"https": proxy, 'http':proxy}

            data = requests.get(url, proxies=proxies).content
            temp = url.split('live.m3u8')
            new_data = data.replace('live_', '%slive_' % temp[0])
            if mode == 'web_play':
                pass
            else:
                from logic import Logic
                if ModelSetting.get('wavve_streaming_type') == '0': #
                    return new_data
            proxy = None
            if ModelSetting.get_bool('wavve_use_proxy'):
                proxy = ModelSetting.get('wavve_proxy_url')
            return cls.change_redirect_data(new_data, proxy=proxy)
        except Exception as e:
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())
        return data

