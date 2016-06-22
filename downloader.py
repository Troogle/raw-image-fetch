#!/usr/local/bin/python3
# -*- coding: utf-8 -*-
from bs4 import BeautifulSoup
import wget
import requests
import cfscrape
import settings
import tempfile, os, shutil

def download(url,handler=requests):
	(fd, tmpfile) = tempfile.mkstemp(".tmp", prefix="", dir=".")
	response=handler.get(url,stream=True)
	response.raise_for_status()
	response.raw.decode_content = True
	with open(tmpfile,'wb') as fdobject:
		shutil.copyfileobj(response.raw,fdobject)
	os.close(fd)
	filename = wget.detect_filename(url, None, response.headers)
	filename = os.path.join(settings.output_dir,filename)
	if os.path.exists(filename):
		filename = wget.filename_fix_existing(filename)
	shutil.move(tmpfile, filename)
	print(filename,'downloaded')
	return filename

def sankaku_download(url):
	scraper=cfscrape.create_scraper()
	r=scraper.get(url)
	s=BeautifulSoup(r.text,"html5lib")
	parent=s.body.find('div',attrs={'id':'parent-preview'})
	if parent:
		parent_link="http://chan.sankakucomplex.com"+parent.find('a').attrs['href']
		print('Tracing Parent...:', parent_link)
		sankaku_check(parent_link)
		return
	section=s.body.find('a',attrs={'id':'highres'})
	downlink='http:'+section.attrs['href']
	download(downlink,scraper)

def shuushuu_download(url):
	r=requests.get(url)
	s=BeautifulSoup(r.text,"html.parser")
	section=s.body.find('a',attrs={'class':'thumb_image'})
	downlink='http://e-shuushuu.net'+section.attrs['href']
	download(downlink)

def danbooru_download(url):
	r=requests.get(url)
	s=BeautifulSoup(r.text,"html.parser")
	section=s.body.find('section',attrs={'id':'image-container'})
	parent=section.attrs['data-parent-id']
	if parent:
		parent_link='http://danbooru.donmai.us/posts/'+parent
		print('Tracing Parent...:',parent_link)
		danbooru_check(parent_link)
		return
	downlink='http://danbooru.donmai.us'+section.attrs['data-file-url']
	download(downlink)

down_defs={
	"sankaku" : sankaku_download,
	"shuushuu" : shuushuu_download,
	"danbooru" : danbooru_download
}