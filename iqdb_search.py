#!/usr/local/bin/python3
# -*- coding: utf-8 -*-
import requests,mimetypes
from bs4 import BeautifulSoup
import cfscrape
import wget
from PIL import Image
import sys,os,shutil,time,re,uuid,tempfile

best=re.compile('Best match')
danbooru=re.compile('danbooru\.donmai\.us')
shuushuu=re.compile('e-shuushuu\.net')
sankaku=re.compile('chan\.sankakucomplex\.com')
maxsize=8388608

#defs
processed_dir="processed"
error_dir="error"
output_dir="raw"
search_url='http://iqdb.org/'
log_path="G:\\log.txt"
#search_service=[1,2,3,4,5,6,10,11,12,13]
search_service=[1,5,6]

class Tee(object):
	def __init__(self, *files):
		self.files = files
	def write(self, *args, **kwargs):
		for f in self.files:
			f.write(*args, **kwargs)
			f.flush()

def download(url,handler=requests):
	prefix = wget.detect_filename(url, None)
	(fd, tmpfile) = tempfile.mkstemp(".tmp", prefix=prefix, dir=".")
	response=handler.get(url,stream=True)
	response.raise_for_status()
	response.raw.decode_content = True
	with open(tmpfile,'wb') as fdobject:
		shutil.copyfileobj(response.raw,fdobject)
	os.close(fd)
	filename = wget.detect_filename(url, None, response.headers)
	filename = os.path.join(output_dir,filename)
	if os.path.exists(filename):
		filename = wget.filename_fix_existing(filename)
	shutil.move(tmpfile, filename)
	print(filename,'downloaded')
	return filename

def sankaku_check(url):
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

def shuushuu_check(url):
	r=requests.get(url)
	s=BeautifulSoup(r.text,"html.parser")
	section=s.body.find('a',attrs={'class':'thumb_image'})
	downlink='http://e-shuushuu.net'+section.attrs['href']
	download(downlink)

def danbooru_check(url):
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

def iqdb_limit(filename):
	if os.path.getsize(filename)*2>maxsize:
		return True
	with Image.open(filename) as im:
		height, width=im.size
		if height>7500:
			return True
		if width>7500:
			return True
	return False

def iqdb_check(filename):
	print("Checking",filename)
	if os.path.getsize(filename)==0:
		return False
	if iqdb_limit(filename):
		newname=uuid.uuid4().hex+'.jpg'
		try:
			with Image.open(filename) as im:
				im.thumbnail(tuple(int(x*0.5) for x in im.size), Image.ANTIALIAS)
				im.save(newname)
				print("iqdb limit exist, newname:",newname)
				ret=iqdb_check(newname)
		except Exception as e:
			print("exception happened:",e)
			ret=False
		finally:
			if os.path.exists(newname):
				os.remove(newname)
			return ret
	payload = {'MAX_FILE_SIZE' : maxsize, 'service[]' :search_service,'url': ""}
	with open(filename,'rb') as imagefile:
		files={'file': ('img',imagefile,mimetypes.guess_type(filename)[0])}
		r=requests.post(search_url,files=files,data=payload)
	parsed_html = BeautifulSoup(r.text,"html.parser")
	obj=parsed_html.body.find('div', attrs={'id':'pages'})
	if not obj:
		print('being banned, waiting....')
		time.sleep(10)
		return iqdb_check(filename)
	operation=[danbooru_check,sankaku_check,shuushuu_check]
	name=["danbooru","sankaku","shuushuu"]
	result=["","",""]
	if best.search(obj.text):
		for links in obj.find_all('a'):
			link=links.attrs['href']
			if not link.startswith("http"):
				link="http:"+link
			if danbooru.search(link) and result[0]=="":
				result[0]=link
			elif sankaku.search(link) and result[1]=="":
				result[1]=link
			elif shuushuu.search(link) and result[2]=="":
				result[2]=link
		for i in range(len(result)):
			if result[i]!="":
				try:
					print("Using",name[i],"as source")
					operation[i](result[i])
					return True
				except Exception as e:
					print("exception happened:",e)
					return False
	return False

if __name__ == "__main__":
	try:
		os.mkdir(processed_dir)
		os.mkdir(error_dir)
		os.mkdir(output_dir)
	except FileExistsError:
		pass
	sys.stdout = Tee(sys.stdout, open(log_path, 'w'))
	selfname=os.path.basename(__file__)
	for f in os.listdir('.'):
		if os.path.isfile(f) and f!=selfname:
			try:
				if iqdb_check(f):
					shutil.move(f,os.path.join(processed_dir,f))
				else:
					shutil.move(f,os.path.join(error_dir,f))
					print(f,"ERROR NOT FOUND")
					time.sleep(1)
			except Exception as e:
				shutil.move(f,os.path.join(error_dir,f))
				print("exception happened:",e)
				time.sleep(1)
	sys.stdout = sys.__stdout__