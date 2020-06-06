# -*- coding: utf-8 -*-
#########################################################
# python
import os
import sys
import logging
import traceback
import json
# third-party
import requests
# sjva 공용
from framework import app, db, scheduler, path_app_root, path_data

# 패키지
from .plugin import logger, package_name
from .model import ModelSetting, ModelChannel
from source_base import SourceBase
import framework.tving.api as Tving

#########################################################


class SourceTving(SourceBase):
    @classmethod
    def prepare(cls, source_id, source_pw, arg):
        cls.login_data = Tving.do_login(source_id, source_pw, '0')
        logger.debug(cls.login_data)
        
    @classmethod
    def get_channel_list(cls):
        try:
            data = Tving.get_live_list(list_type='both')
            ret = []
            for item in data:
                if item['free']:
                    if item['title'].startswith('CH.'):
                        continue
                    #C04601 : 채널CGV, ocn, super action, ytn life, ocn                        
                    if item['id'] in ['C04601', 'C07381', 'C07382', 'C01101']:
                        continue
                    c = ModelChannel(cls.source_name, item['id'], item['title'], item['img'], True)
                    c.current = item['episode_title']
                    ret.append(c)
        except Exception as e:
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())
        return ret

    @classmethod
    def get_url(cls, source_id, quality, mode):
        logger.debug('tving get_url:%s %s %s', source_id, quality, cls.login_data)
        try:
            quality = Tving.get_quality_to_tving(quality)
            c_id = source_id
            if source_id.startswith('V'):
                c_id = source_id[1:]
            proxy = None
            if ModelSetting.get_bool('tving_use_proxy'):
                proxy = ModelSetting.get('tving_proxy_url')
            data, url = Tving.get_episode_json(c_id, quality, cls.login_data, proxy=proxy)
            if source_id.startswith('V'):
                return 'redirect', url
            else:
                return 'return_after_read', url
        except Exception as e:
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())
        

    @classmethod
    def get_return_data(cls, source_id, url, mode):
        try:

            data = requests.get(url).content
            #logger.debug(data)
            temp = url.split('playlist.m3u8')
            rate = ['chunklist_b5128000.m3u8', 'chunklist_b1628000.m3u8', 'chunklist_b1228000.m3u8', 'chunklist_b1128000.m3u8', 'chunklist_b628000.m3u8', 'chunklist_b378000.m3u8']
            for r in rate:
                if data.find(r) != -1:
                    url1 = '%s%s%s' % (temp[0], r, temp[1])
                    data1 = requests.get(url1).content
                    data1 = data1.replace('media', '%smedia' % temp[0]).replace('.ts', '.ts%s' % temp[1])
                    #logger.debug(data1)
                    if mode == 'web_play':
                        data1 = cls.change_redirect_data(data1)
                    return data1
            #logger.debug(url)
            return url
        except Exception as e:
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())
        return ret








