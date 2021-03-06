#!/usr/local/bin/python3
# -*- coding: utf-8 -*-
from bs4 import BeautifulSoup
from wget import detect_filename
import urllib.request
import requests
import cfscrape
import settings
import tempfile, os, shutil, re

def filename_fix_existing(filename, dirname='.'):
	"""Expands name portion of filename with numeric ' (x)' suffix to
	return filename that doesn't exist already.
	from wget
	"""
	if not os.path.exists(filename):
		return filename
	path, name = os.path.split(filename)
	name, ext = os.path.splitext(name)
	names = [x for x in os.listdir(dirname) if x.startswith(name)]
	names = [x.rsplit('.', 1)[0] for x in names]
	suffixes = [x.replace(name, '') for x in names]
	# filter suffixes that match ' (x)' pattern
	suffixes = [x[2:-1] for x in suffixes
				   if x.startswith(' (') and x.endswith(')')]
	indexes  = [int(x) for x in suffixes
				   if set(x) <= set('0123456789')]
	idx = 1
	if indexes:
		idx += sorted(indexes)[-1]
	name = '%s (%d)%s' % (name, idx, ext)
	return os.path.join(path, name)

def safe_filename(filename):
	# for NTFS-win32 only
	unsafe = "".join(chr(x) for x in range(32))
	unsafe += '/\\:*?"<>|'
	return ''.join(c for c in filename if not c in unsafe)

def download(url,handler=requests):
	(fd, tmpfile) = tempfile.mkstemp(".tmp", prefix="", dir=".")
	response=handler.get(url,stream=True)
	response.raise_for_status()
	with open(tmpfile, 'wb') as fdobject:
		for chunk in response.iter_content(1024):
			fdobject.write(chunk)
	os.close(fd)
	filename = detect_filename(url, None, response.headers)
	filename = urllib.request.unquote(filename)
	filename = safe_filename(filename)
	filename = os.path.join(settings.output_dir,filename)
	filename = filename_fix_existing(filename,settings.output_dir)
	shutil.move(tmpfile, filename)
	print(filename,'downloaded')
	return filename

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
		danbooru_download(parent_link)
		return
	downlink='http://danbooru.donmai.us'+section.attrs['data-file-url']
	download(downlink)

def sankaku_download(url):
	scraper=cfscrape.create_scraper()
	r=scraper.get(url)
	s=BeautifulSoup(r.text,"html5lib")
	parent=s.body.find('div',attrs={'id':'parent-preview'})
	if parent:
		parent_link="http://chan.sankakucomplex.com"+parent.find('a').attrs['href']
		print('Tracing Parent...:', parent_link)
		sankaku_download(parent_link)
		return
	section=s.body.find('a',attrs={'id':'highres'})
	downlink='http:'+section.attrs['href']
	download(downlink,scraper)

parent_re=re.compile("<a href=\"(.+?)\">parent post</a>")

def yande_download(url):
	scraper=cfscrape.create_scraper()
	r=scraper.get(url)
	s=BeautifulSoup(r.text,"html5lib")
	parent=parent_re.search(r.text)
	if parent:
		parent_link="https://yande.re"+parent.group(1)
		print('Tracing Parent...:', parent_link)
		yande_download(parent_link)
		return
	section=s.body.find('a',attrs={'id':'png'})
	if not section:
		section=s.body.find('a',attrs={'id':'highres'})
	downlink=section.attrs['href']
	download(downlink,scraper)

def konachan_download(url):
	scraper=cfscrape.create_scraper()
	r=scraper.get(url)
	s=BeautifulSoup(r.text,"html5lib")
	parent=parent_re.search(r.text)
	if parent:
		parent_link="http://konachan.com"+parent.group(1)
		print('Tracing Parent...:', parent_link)
		konachan_download(parent_link)
		return
	section=s.body.find('a',attrs={'id':'png'})
	if not section:
		section=s.body.find('a',attrs={'id':'highres'})
	downlink=section.attrs['href']
	download(downlink,scraper)



down_defs={
	"sankaku" : sankaku_download,
	"shuushuu" : shuushuu_download,
	"danbooru" : danbooru_download,
	"konachan" : konachan_download,
	"yande" : yande_download
}