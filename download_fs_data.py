# -*- coding: utf-8 -*-
"""
Created on Fri Jun 17 16:15:22 2016

@author: Nate Plumb

This file goes to the URL for the SEC's 'as submitted' financial statement
data: https://www.sec.gov/dera/data/financial-statement-data-sets.html.
Any data not currently in subdirectories of the working directory are 
downloaded and unzipped
"""

import urllib
import re
import os
import ssl
import zipfile
import StringIO

# get contents of page at URL
url = urllib.urlopen(
"https://www.sec.gov/dera/data/financial-statement-data-sets.html")
page_contents = url.read()
url.close()

# find zip files and compare to files in working directory
all_zip_files = re.findall('data.*zip"', page_contents)
for idx in range(len(all_zip_files)):
    all_zip_files[idx] = re.sub('"', '', all_zip_files[idx])

all_quarters = []
for zip_file in all_zip_files:
    quarter = re.findall("[0-9].*[0-9]", zip_file)
    all_quarters.append(quarter[0])
print "Available quarters:"
print all_quarters, "\n"

new_quarters = {}
for quarter in all_quarters:
    if not os.path.isdir(quarter):
        new_quarters[quarter] = "data/financial-statements/"+quarter+".zip"
print "New quarters:"
print new_quarters.keys(), "\n"

context = ssl._create_unverified_context() # necessary to avoid a CertificateError

sec_site = "http://www.sec.gov/"
for quarter in new_quarters:
    print "Extracting", quarter
    
    f = urllib.urlopen(sec_site+new_quarters[quarter], context = context)
    zf = zipfile.ZipFile(StringIO.StringIO(f.read()))
    zf.extractall(quarter)
    zf.close()    
    f.close()

print "All files up to date."


