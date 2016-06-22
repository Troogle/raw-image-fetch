#!/usr/local/bin/python3
# -*- coding: utf-8 -*-
from PIL import Image
import os
Image.MAX_IMAGE_PIXELS = None

exts=['.jpg', '.jpeg', '.png', '.bmp', '.gif']
for f in os.listdir('.'):
	if os.path.isfile(f) and os.path.splitext(f)[1] in exts:
		v_image = Image.open(f)
		try:
			v_image.verify()
		except Exception as e:
			print("Invalid", f)