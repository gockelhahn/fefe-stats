#!/usr/bin/env python3

import os
import subprocess
from lxml import html

url_month = 'https://blog.fefe.de/?mon='
url_post = 'https://blog.fefe.de/?ts='
startyear = 2005
startmonth = 3
endyear = 2017
endmonth = 2

month_directory = 'month'
post_directory = 'post'

links = []

if not os.path.exists(month_directory):
    os.makedirs(month_directory)
    
if not os.path.exists(post_directory):
    os.makedirs(post_directory)

for year in range(startyear, endyear + 1):
    for month in range (1, 13):
        ''' check valid date '''
        if (year == startyear and month < startmonth) or (year == endyear and month > endmonth):
            continue
        
        # assemble url
        param = str(year) + str(month).zfill(2)
        url = url_month + param
        
        # assemble filename
        filename = os.path.join(month_directory, param)
        
        # continue if file already exists
        if os.path.isfile(filename):
            continue;
        
        # download month and save it locally in month_directory/param:
        with open(os.devnull, 'w') as devnull:
            subprocess.run(["wget", url, "-O", filename], stdout=devnull, stderr=subprocess.STDOUT)

for filename in os.listdir(month_directory):
    # read file and extract all post links and add to array "links"
    tree = html.parse(os.path.join(month_directory, filename))
    links += tree.xpath('//a[text()=\'[l]\']/@href')

for link in links:
    # get post parameter from link
    param = str(link)[4:]
    # assemble url
    url = url_post + param
    
    # assemble filename
    filename = os.path.join(post_directory, param)
    
    # continue if file already exists
    if os.path.isfile(filename):
        continue;
    
    # download post and save it locally in post_directory/param:
    with open(os.devnull, 'w') as devnull:
        subprocess.run(["wget", url, "-O", filename], stdout=devnull, stderr=subprocess.STDOUT)
