#!/usr/local/bin/python3
# -*- coding: utf-8 -*-
import requests,mimetypes
from bs4 import BeautifulSoup
from PIL import Image
import processer
import settings
import sys,os,shutil,time,re,uuid

best=re.compile('Best match')

class Tee(object):
	def __init__(self, *files):
		self.files = files
	def write(self, *args, **kwargs):
		for f in self.files:
			f.write(*args, **kwargs)
			f.flush()

def iqdb_limit(filename):
	if os.path.getsize(filename)>settings.maxsize:
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
	payload = {'service[]' :settings.search_service,'url': ""}
	with open(filename,'rb') as imagefile:
		files={'file': ('img',imagefile,mimetypes.guess_type(filename)[0])}
		r=requests.post(settings.search_url,files=files,data=payload)
	parsed_html = BeautifulSoup(r.text,"html.parser")
	obj=parsed_html.body.find('div', attrs={'id':'pages'})
	if not obj:
		print('being banned, waiting....')
		time.sleep(10)
		return iqdb_check(filename)
	if best.search(obj.text):
		return processer.parse(obj)
	return False

if __name__ == "__main__":
	try:
		os.mkdir(settings.processed_dir)
		os.mkdir(settings.error_dir)
		os.mkdir(settings.output_dir)
	except FileExistsError:
		pass
	logger = Tee(sys.stdout, open(settings.log_path, 'a'))
	sys.stdout = logger
	exts=['.jpg', '.jpeg', '.png', '.bmp', '.gif']
	for f in os.listdir('.'):
		if os.path.isfile(f) and os.path.splitext(f)[1] in exts:
			try:
				if iqdb_check(f):
					shutil.move(f,os.path.join(settings.processed_dir,f))
				else:
					shutil.move(f,os.path.join(settings.error_dir,f))
					print(f,"ERROR NOT FOUND")
					time.sleep(1)
			except Exception as e:
				shutil.move(f,os.path.join(settings.error_dir,f))
				print("exception happened:",e)
				time.sleep(1)
	sys.stdout = sys.__stdout__