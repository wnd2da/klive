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
        cls.login_data = Wavve.do_login(source_id, source_pw)

    @classmethod
    def get_channel_list(cls):
        try:
            data = Wavve.live_all_channels()
            ret = []
            for item in data['list']:
                c = ModelChannel(cls.source_name, item['channelid'], item['channelname'], 'https://' + item['tvimage'], (item['type']=='video'))
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
    def get_url(cls, source_id, quality, mode):
        try:
            data = Wavve.streaming('live', source_id, quality, cls.login_data)
            surl = None
            if data is not None:
                surl = data['playurl']
            if ModelSetting.get('wavve_streaming_type') == '2':
                return 'redirect', surl
            return 'return_after_read', surl
        except Exception as e:
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())


    @classmethod
    def get_return_data(cls, source_id, url, mode):
        try:
            data = requests.get(url).content
            temp = url.split('live.m3u8')
            new_data = data.replace('live_', '%slive_' % temp[0])
            if mode == 'web_play':
                pass
            else:
                from logic import Logic
                if ModelSetting.get('wavve_streaming_type') == '0': #
                    return new_data
            return cls.change_redirect_data(new_data)
        except Exception as e:
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())
        return data


















    # EPG
    def MakeEPG(self, prefix, channel_list=None):
        list = self.GetChannelList()
        import datetime
        startDate = datetime.datetime.now()
        startParam = startDate.strftime('%Y/%m/%d')
        endDate = startDate + datetime.timedelta(days=2)
        endParam = endDate.strftime('%Y/%m/%d')

        str = ''
        count = 100
        type_count = 0
        for item in list:
            count += 1
            channel_number = count
            channel_name = item['title']
            if channel_list is not None:
                if len(channel_list['POOQ']) == type_count: break
                if item['id'] in channel_list['POOQ']:
                    type_count += 1
                    channel_number = channel_list['POOQ'][item['id']]['num']
                    if len(channel_list['POOQ'][item['id']]['name']) is not 0: channel_name = channel_list['POOQ'][item['id']]['name']
                else:
                    continue
            
            str += '\t<channel id="POOQ|%s" video-src="%slc&type=POOQ&id=%s" video-type="HLS2">\n' % (item['id'], prefix, item['id'])
            str += '\t\t<display-name>%s</display-name>\n' % channel_name
            str += '\t\t<display-name>%s</display-name>\n' % channel_number
            str += '\t\t<display-number>%s</display-number>\n' % channel_number
            str += '\t\t<icon src="%s" />\n' % item['img']
            str += '\t</channel>\n'

            url = 'http://wapie.pooq.co.kr/v1/epgs30/%s/?deviceTypeId=pc&marketTypeId=generic&apiAccessCredential=EEBE901F80B3A4C4E5322D58110BE95C&drm=WC&country=KOR&offset=0&limit=1000&startTime=%s+00:00&pooqzoneType=none&credential=none&endTime=%s+00:00' % (item['id'], startParam, endParam)
            
            request = urllib2.Request(url)
            response = urllib2.urlopen(request)
            data = json.load(response, encoding='utf8')

            for epg in data['result']['list']:
                ep_startDate = datetime.datetime.strptime(epg['startDate'].replace('-',''), "%Y%m%d").date()
                startTime = '%s%s' % (epg['startDate'].replace('-',''), epg['startTime'].replace(':', ''))
                temp_startTime = int(epg['startTime'].replace(':', ''))
                temp_endTime = int(epg['endTime'].replace(':', ''))
                if temp_startTime > temp_endTime:
                    ep_startDate = ep_startDate + datetime.timedelta(days=1)
                endTime = '%s%s' % (ep_startDate.strftime("%Y%m%d"), epg['endTime'].replace(':', ''))
                if long(startTime) >= long(endTime) : continue
                str += '\t<programme start="%s00 +0900" stop="%s00 +0900" channel="POOQ|%s">\n' %  (startTime, endTime, item['id'])
                #str += '\t\t<title lang="kr"><![CDATA[%s]]></title>\n' % epg['programTitle']
                str += '\t\t<title lang="kr">%s</title>\n' % epg['programTitle'].replace('<',' ').replace('>',' ')
                str += '\t\t<icon src="http://img.pooq.co.kr/BMS/program_poster/201802/%s_210.jpg" />\n' % epg['programId']
                
                age_str = '%s세 이상 관람가' % epg['age'] if epg['age'] != '0' else '전체 관람가'
                str += '\t\t<rating system="KMRB"><value>%s</value></rating>\n' % age_str
                desc = '등급 : %s\n' % age_str

                staring = epg['programStaring'].strip() if 'programStaring' in epg and epg['programStaring'] is not None else None
                if staring is not None and staring != '':
                    temp = staring.split(',')
                    if len(temp) > 0:
                        str += '\t\t<credits>\n'
                        for actor in temp:
                            str += '\t\t\t<actor>%s</actor>\n' % actor.strip().replace('<',' ').replace('>',' ')
                        str += '\t\t</credits>\n'
                        desc += '출연 : %s\n' % epg['programStaring'] 
                if 'programSummary' in epg and epg['programSummary'] is not None:
                    #desc += epg['programSummary'].replace('<','&lt').replace('>','&gt')
                    #desc += epg['programSummary']
                    desc = epg['programSummary'] + '\n' + desc
                    desc == desc.strip()
                str += '\t\t<desc lang="kr">%s</desc>\n' % desc.strip().replace('<',' ').replace('>',' ')
                str += '\t</programme>\n'
            time.sleep(SLEEP_TIME)
        return str

    # 공중파에서 호출하며 하나의 ID에 대한 <programme> 태그만 넘긴다
    def MakeEPG_ID(self, wavve_id, original_type_id):
        import datetime
        startDate = datetime.datetime.now()
        startParam = startDate.strftime('%Y/%m/%d')
        endDate = startDate + datetime.timedelta(days=2)
        endParam = endDate.strftime('%Y/%m/%d')

        str = ''
        url = 'http://wapie.pooq.co.kr/v1/epgs30/%s/?deviceTypeId=pc&marketTypeId=generic&apiAccessCredential=EEBE901F80B3A4C4E5322D58110BE95C&drm=WC&country=KOR&offset=0&limit=1000&startTime=%s+00:00&pooqzoneType=none&credential=none&endTime=%s+00:00' % (wavve_id, startParam, endParam)
            
        request = urllib2.Request(url)
        response = urllib2.urlopen(request)
        data = json.load(response, encoding='utf8')

        for epg in data['result']['list']:
            ep_startDate = datetime.datetime.strptime(epg['startDate'].replace('-',''), "%Y%m%d").date()
            startTime = '%s%s' % (epg['startDate'].replace('-',''), epg['startTime'].replace(':', ''))
            temp_startTime = int(epg['startTime'].replace(':', ''))
            temp_endTime = int(epg['endTime'].replace(':', ''))
            if temp_startTime > temp_endTime:
                ep_startDate = ep_startDate + datetime.timedelta(days=1)
            endTime = '%s%s' % (ep_startDate.strftime("%Y%m%d"), epg['endTime'].replace(':', ''))
            if long(startTime) >= long(endTime) : continue
            str += '\t<programme start="%s00 +0900" stop="%s00 +0900" channel="%s">\n' %  (startTime, endTime, original_type_id)
                #str += '\t\t<title lang="kr"><![CDATA[%s]]></title>\n' % epg['programTitle']
            str += '\t\t<title lang="kr">%s</title>\n' % epg['programTitle'].replace('<',' ').replace('>',' ')
            str += '\t\t<icon src="http://img.pooq.co.kr/BMS/program_poster/201802/%s_210.jpg" />\n' % epg['programId']
                
            age_str = '%s세 이상 관람가' % epg['age'] if epg['age'] != '0' else '전체 관람가'
            str += '\t\t<rating system="KMRB"><value>%s</value></rating>\n' % age_str
            desc = '등급 : %s\n' % age_str

            staring = epg['programStaring'].strip() if 'programStaring' in epg and epg['programStaring'] is not None else None
            if staring is not None and staring != '':
                temp = staring.split(',')
                if len(temp) > 0:
                    str += '\t\t<credits>\n'
                    for actor in temp:
                        str += '\t\t\t<actor>%s</actor>\n' % actor.strip().replace('<',' ').replace('>',' ')
                    str += '\t\t</credits>\n'
                    desc += '출연 : %s\n' % epg['programStaring'] 
            if 'programSummary' in epg and epg['programSummary'] is not None:
                    #desc += epg['programSummary'].replace('<','&lt').replace('>','&gt')
                    #desc += epg['programSummary']
                desc = epg['programSummary'] + '\n' + desc
                desc == desc.strip()
            str += '\t\t<desc lang="kr">%s</desc>\n' % desc.strip().replace('<',' ').replace('>',' ')
            str += '\t</programme>\n'
        time.sleep(SLEEP_TIME)
        return str