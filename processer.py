#!/usr/local/bin/python3
# -*- coding: utf-8 -*-
from downloader import *
import settings
import re, collections

parse_regexs = collections.OrderedDict((
	("danbooru",re.compile('danbooru\.donmai\.us')),		#parent, tag
	("konachan",re.compile('konachan\.com')),				#parent, tag
	("yande",re.compile('yande\.re')),						#parent, tag
	("sankaku",re.compile('chan\.sankakucomplex\.com')),	#parent
	("shuushuu",re.compile('e-shuushuu\.net'))				#
))

def parse(htmlobj):
	for processor in parse_regexs:

		regex=parse_regexs[processor]
		downloader=down_defs[processor]

		for links in htmlobj.find_all('a'):
			link=links.attrs['href']
			if not link.startswith("http"):
				link="http:"+link
			if regex.search(link):
				try:
					print("Using %s as source..." % processor)
					downloader(link)
					print("Success!")
					return True
				except Exception as e:
					print("exception happened:",e)
	return False