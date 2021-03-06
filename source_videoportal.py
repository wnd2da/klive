# -*- coding: utf-8 -*-
#########################################################
# python
import os
import sys
import logging
import traceback
import json
import urllib
import urllib2
import ssl
import datetime
import xml.etree.ElementTree as ET
import re

# third-party
from sqlitedict import SqliteDict
import requests
# sjva 공용
from framework.logger import get_logger
from framework import app, db, scheduler, path_app_root, path_data
from system.logic import SystemLogic

# 패키지
from system.model import ModelSetting as SystemModelSetting
from .model import ModelSetting, ModelChannel
from source_base import SourceBase

# 로그
package_name = __name__.split('.')[0]
logger = get_logger(package_name)
#########################################################


class SourceVideoportal(SourceBase):
    @classmethod
    def prepare(cls, source_id, source_pw, arg):
        pass
   
    
    @classmethod
    def get_channel_list(cls):
        try:
            stamp = str(datetime.datetime.today().strftime('%Y%m%d%H%M%S'))
            url = 'http://123.140.104.150/api/epg/v1/channel/virtual?access_key=C4A0697007C3548D389B&cp_id=S_LGU_HYUK0920&system_id=HDTV&SA_ID=500053434041&STB_MAC=v000.5343.4041&NSC_TYPE=LTE&BASE_GB=Y&BASE_CD=W172.017&YOUTH_YN=N&ORDER_GB=N&POOQ_YN=N&HDTV_VIEW_GB=R&SID=001010005638&CLIENT_IP=172.17.100.15&OS_INFO=android_4.4.2&NW_INFO=WIFI&APP_TYPE=ROSA&DEV_MODEL=SM-N935F&CARRIER_TYPE=E&UI_VER=04.38.04&NOW_PAGE=25&PRE_PAGE=&MENU_NM=&CONTS_GB=&TERM_BINVER=3.8.118.0106'
            ret = []
            request = urllib2.Request(url)
            response = urllib2.urlopen(request)
            tree = ET.parse(response)
            root = tree.getroot()
            for item in root.findall('list'):
                #info = {}
                #info['id'] = item.findtext('service_id')
                #info['title'] = item.findtext('service_name').strip()
                #info['img'] = item.findtext('img_url') + item.findtext('img_file_name')
                #info['summary'] = item.findtext('description')
                #url = item.findtext('live_server1') + item.findtext('live_file_name1')
                #info['url']  = '%s?VOD_RequestID=v2M2-0101-1010-7272-5050-0000%s;LTE;480p;WIFI&APPNAME=hdtv&ALBUM_ID=%s&ma=D0:17:C2:CE:D7:A1' % (url, stamp, info['id'])
                #if item.findtext('live_file_name1') != '' and item.findtext('genre_name') != u'성인':
                #	result.append(info)
                import system

                
                if item.findtext('service_id') in ['628', '629', '743']:
                    if not SystemModelSetting.get_bool('videoportal_adult'):
                        continue

                c = ModelChannel(cls.source_name, 
                    item.findtext('service_id'), 
                    item.findtext('service_name').strip(), 
                    item.findtext('img_url') + item.findtext('img_file_name'),
                    True)
                c.current = item.findtext('description')
                ret.append(c)

        except Exception as e:
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())
        return ret

    @classmethod
    def get_url(cls, source_id, quality, mode):
        #logger.debug('VIDEOPORTAL get_url:%s %s', source_id, quality)
        try:
            live_server1 = 'http://1.214.67.74:80/'
            live_file_name = '%sHN.m3u8' % source_id
            stamp = str(datetime.datetime.today().strftime('%Y%m%d%H%M%S'))
            url = '%s%s?VOD_RequestID=v2M2-0101-1010-7272-5050-0000%s;LTE;1080p;WIFI&APPNAME=hdtv&ALBUM_ID=%s&ma=D0:17:C2:CE:D7:A1' % (live_server1, live_file_name, stamp, source_id)
            #http://211.170.95.74/vod/68201.m3u8?VOD_RequestID=v050-0202-0606-1212-0000-979720200704125108;LTE;720p;WIFI
            #http://211.170.95.74/vod/74701.m3u8?VOD_RequestID=v050-0202-0606-1212-0000-979720200704125108;LTE;720p;WIFI
            
            #if mode == 'url':
            if True:
                data = requests.get(url).content
                # 밴드 선택
                rate_list = re.compile(r'http(.*?)$', re.MULTILINE).finditer(data)
                for rate in rate_list:
                    url = rate.group(0)
                    #return 'return_after_read', url
                    return 'redirect', url
            else:
                return 'redirect', url
            return 'redirect', url
        except Exception as e:
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())
        

    
    @classmethod
    def get_return_data(cls, source_id, url, mode):
        try:
            data = requests.get(url).content
            logger.debug(url)

            logger.debug(data)
            
            if mode == 'web_play':
                data = cls.change_redirect_data(data)
            return data
        except Exception as e:
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())
        return ret

   
    """
    def MakeEPG(self, prefix, channel_list=None):
		str = ''
		list = self.GetChannelList()
		count = 600
		type_count = 0
		for item in list:
			print('VIDEOPORTAL-1 %s / %s make EPG' % (count, len(list)))
			count += 1
			channel_number = count
			channel_name = item['title']
			if channel_list is not None:
				if len(channel_list['VIDEOPORTAL']) == type_count: break
				if item['id'] in channel_list['VIDEOPORTAL']:
					type_count += 1
					channel_number = channel_list['VIDEOPORTAL'][item['id']]['num']
					if len(channel_list['VIDEOPORTAL'][item['id']]['name']) is not 0: channel_name = channel_list['VIDEOPORTAL'][item['id']]['name']
				else:
					continue
			str += '\t<channel id="VIDEOPORTAL|%s" video-src="%surl&type=VIDEOPORTAL&id=%s" video-type="HLS">\n' % (item['id'], prefix, item['id'])
			str += '\t\t<display-name>%s</display-name>\n' % channel_name
			str += '\t\t<display-name>%s</display-name>\n' % channel_number
			str += '\t\t<display-number>%s</display-number>\n' % channel_number
			str += '\t\t<icon src="%s" />\n' % item['img']
			str += '\t</channel>\n'


			url = 'http://123.140.104.150/api/epg/v1/schedule/virtual?access_key=CE45020A8BC704127A6C&cp_id=S_LGU_HYUK0920&system_id=HDTV&SA_ID=M20110725000&STB_MAC=v201.1072.5000&NSC_TYPE=LTE&TC_IN=-1&TC_OUT=3&YOUTH_YN=N&POOQ_YN=N&HDTV_VIEW_GB=R&SERVICE_ID=&EPG_SDATE=&EPG_EDATE=&SID=001010005638&CLIENT_IP=192.168.0.1&OS_INFO=android_4.4.2&NW_INFO=WIFI&APP_TYPE=ROSA&DEV_MODEL=SM-N935F&CARRIER_TYPE=E&UI_VER=04.38.04&NOW_PAGE=25&PRE_PAGE=&MENU_NM=&CONTS_GB=&TERM_BINVER=3.8.118.0106'
			request = urllib2.Request(url)
			response = urllib2.urlopen(request)
			tree = ET.parse(response)
			root = tree.getroot()
			idx = 0
			for item in root.findall('list'):

				#continue
				if channel_list is not None:
					if item.findtext('service_id') not in channel_list['VIDEOPORTAL']: continue
				

				idx += 1
				print('VIDEOPORTAL-1 %s / %s make EPG' % (idx, len(root.findall('list'))))
				if long(item.findtext('start_time')) >= long(item.findtext('end_time')): continue
				str += '\t<programme start="%s +0900" stop="%s +0900" channel="VIDEOPORTAL|%s">\n' %  (item.findtext('start_time'), item.findtext('end_time'), item.findtext('service_id'))
				str += '\t\t<title lang="kr">%s</title>\n' % item.findtext('program_title').replace('<',' ').replace('>',' ')
				if item.findtext('thm_img_file') is not '':
					str += '\t\t<icon src="%s%s" />\n' % (item.findtext('thm_img_url') ,item.findtext('thm_img_file') )

				#age_str = '%s세 이상 관람가' % epg['ratingCd'] if epg['ratingCd'] != '0' and epg['ratingCd'] != '1' else '전체 관람가'
				#str += '\t\t<rating system="KMRB"><value>%s</value></rating>\n' % age_str
				#desc = '등급 : %s\n' % age_str
				desc = ''

				actorName = item.findtext('act').strip()				
				actorName = actorName if actorName != '' else None
				if actorName is not None: 
					str += '\t\t<credits>\n'
					temp = actorName.split(',')
					for actor in temp: str += '\t\t\t<actor>%s</actor>\n' % actor.strip().replace('<',' ').replace('>',' ')
					desc += '출연 : %s\n' % actorName
					str += '\t\t</credits>\n'
				if item.findtext('sid').strip() != '': desc += '%s\n' % item.findtext('sid').strip()
				desc += '%s' % item.findtext('program_synopsis')
				str += '\t\t<desc lang="kr">%s</desc>\n' % desc.strip().replace('<',' ').replace('>',' ')
				str += '\t</programme>\n'
				time.sleep(SLEEP_TIME)
				
		return str
    """
