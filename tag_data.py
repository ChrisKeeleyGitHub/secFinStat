# -*- coding: utf-8 -*-
"""
Created on Mon Jun 13 12:19:17 2016

@author: Nate Plumb

This file contains a function created for the financial statements data from 
SEC filings found at 
https://www.sec.gov/dera/data/financial-statement-data-sets.html.
The function extracts data from the tag.txt file, organizes the data and 
puts the data in the fs_db database.
"""

import csv
import MySQLdb
import time
import StringIO


# helper functions
def clean(esc_str):
    esc_str = list(esc_str)
    new_str = []
    for char in esc_str:
        if char == "'":
            new_str.append("\\'")
        elif char != "\\":
            new_str.append(char)
    return ''.join(new_str)
    
def convert_time(secs):
    time_str = ""
    hours = secs / 3600
    if hours > 0:
        time_str += (str(hours)+" hours, ")
    minutes = (secs % 3600) / 60
    if hours > 0 or minutes > 0:
        time_str += (str(minutes)+" minutes, ")
    seconds = secs % 60
    time_str += (str(seconds)+" seconds")
    return time_str
    

# primary function
def tag_data(sub_dir):
    # extract data
    tag = []
#    with open(sub_dir+"/tag.txt", "r") as f:
#        data = f.read()
#        new_data = data.replace('"', '')
#        reader = csv.reader(new_data, delimiter = "\t")
#        for row in reader:
#            tag.append(row)
    with open(sub_dir+"/tag.txt", 'rb') as f:
        content = f.read().replace('"', '')
        reader = csv.reader(StringIO.StringIO(content), delimiter = "\t", 
                            doublequote=False)
        for row in reader:
            tag.append(row)

# IMPORTANT NOTE
# Stray '"' was removed from the start of the 'doc' field at line 7501 of 
# tag.txt in 2009q3, line 7204 of 2009q4 and line 6983 of 2010q1 to avoid 
# complications when reading in data


    # print number of rows in data
    total_rows = len(tag)
    print "Rows in file:", total_rows, "\n"
                
    # arrange data by column
    header = tag[0]
    cols = []
    for col_idx in range(len(header)):
        data = []
        for row_idx in range(1, len(tag)):
            data.append(tag[row_idx][col_idx])
        cols.append(data)
    
    # organize data in dictionary
    orgd = {}
    idx = 0
    for field in header:
        orgd[field] = cols[idx]
        idx += 1

    # escape any "'" and remove extra backslashes
    for field in orgd:
        for idx in range(len(orgd[field])):
            orgd[field][idx] = clean(orgd[field][idx])
            
       
    # get mysql password
    f = open("pw.txt", "r")
    pw = f.read()
    f.close()
    
    # connect to mysql
    conn = MySQLdb.connect(host = "localhost", user = "root", passwd = pw, 
                           db = "fs_db")
    cur = conn.cursor()
    
    count = 1
    start_time = time.time()
    print "Entering data into database", "\n"
    for row in range(len(tag) - 1):

        # insert data into 'docs' table
        doc = orgd["doc"][row]
        if len(doc) > 2048:
            doc = doc[0:2048]

        cur.execute("INSERT INTO docs (doc) VALUES ('"+doc+"');")
        
        cur.execute("SELECT LAST_INSERT_ID();")
        doc_id_ti = str(cur.fetchone()[0])
       
        
        # insert data into 'tag_info' table
        tag, version = orgd["tag"][row], orgd["version"][row]                      
        abstract, tlabel = orgd["abstract"][row], orgd["tlabel"][row]
        custom = orgd["custom"][row]
        
        cur.execute("""INSERT INTO tag_info (tag, version, custom, abstract, 
        tlabel, doc_id_ti) VALUES (
        '"""+tag+"', '"+version+"', "+custom+", "+abstract+", '"+tlabel+"', "+doc_id_ti+");")
                
    
        # insert data into 'not_abs_tag_info' table
        if int(abstract) == False:
            datatype = orgd["datatype"][row]
            iord, crdr = orgd["iord"][row], orgd["crdr"][row]
            
            cur.execute("SELECT LAST_INSERT_ID();")            
            tag_info_id_noabs = str(cur.fetchone()[0])
            
            cur.execute("""INSERT IGNORE INTO not_abs_tag_info (
            tag_info_id_noabs, datatype, iord, crdr) VALUES (
            """+tag_info_id_noabs+", '"+datatype+"', '"+iord+"', '"+crdr+"');")
            
        # insert data into 'tags' table
        cur.execute("INSERT IGNORE INTO tags (tag) VALUES ('"+tag+"');")
        
        #insert data into 'versions' table
        cur.execute("""INSERT IGNORE INTO versions (version) VALUES (
        '"""+version+"');")
        
        if total_rows > 100:
            if count % (total_rows / 100) == 0:
                conn.commit()
                print count, "rows committed"
                cur_time = time.time()
                elapsed_time = cur_time - start_time
                total_time = elapsed_time * (float(total_rows) / float(count))
                remain_time = total_time - elapsed_time
                print "Elapsed time:", convert_time(int(elapsed_time))
                print "Estimated time to completion:", convert_time(int(remain_time)), "\n"
            
        count += 1
            
    
    conn.commit()
    
    conn.close()
        
