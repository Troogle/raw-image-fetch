#!/usr/local/bin/python3
# -*- coding: utf-8 -*-
processed_dir="processed"
error_dir="error"
output_dir="raw"
log_path="log.txt"

search_url='http://iqdb.org/'
#search_service=[1,2,3,4,5,6,10,11,12,13] #full
#search_service=[1,2,3] #tagged
search_service=[1,2,3,5,6] #supported
maxsize=8388608/2

exts=['.jpg', '.jpeg', '.png', '.bmp', '.gif']