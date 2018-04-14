# -*- coding: utf-8 -*-
"""
Created on Mon Jun 13 14:34:47 2016

@author: Nate Plumb

This file contains a function created for the financial statements data from 
SEC filings found at 
https://www.sec.gov/dera/data/financial-statement-data-sets.html.
The function extracts data from the tag.txt file, organizes the data and 
puts the data in the fs_db database.
"""

import csv
import MySQLdb
import re
import time


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

def remove_hy(adsh):
    adsh = re.sub("-", "", adsh)
    return adsh

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
    

# main function
def num_data(sub_dir):
    # extract data
    num = []
    with open(sub_dir+"/num.txt", "r") as f:
        reader = csv.reader(f, delimiter = "\t")
        for row in reader:
            num.append(row)
            
    # print number of rows in data
    total_rows = len(num)
    print "Rows in file:", total_rows, "\n"
                
    # arrange data by column
    header = num[0]
    cols = []
    for col_idx in range(len(header)):
        data = []
        for row_idx in range(1, len(num)):
            data.append(num[row_idx][col_idx])
        cols.append(data)
    
    # organize data in dictionary
    orgd = {}
    idx = 0
    for field in header:
        orgd[field] = cols[idx]
        idx += 1
    
    # escape any "'", remove extra backslashes, remove hyphens from adsh and
    # make nulls in 'value' mysql readable
    for field in orgd:
        for idx in range(len(orgd[field])):
            orgd[field][idx] = clean(orgd[field][idx])
            if field == "adsh":
                orgd[field][idx] = remove_hy(orgd[field][idx])
            elif field == "value":
                if orgd[field][idx] == "":
                    orgd[field][idx] = "0.0000"
                
            
       
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
    for row in range(len(num) - 1):
        # insert data into 'numbers' table
        value, ddate, tag = orgd["value"][row], orgd["ddate"][row], orgd["tag"][row]
        qtrs, uom, adsh = orgd["qtrs"][row], orgd["uom"][row], orgd["adsh"][row]
        version, coreg = orgd["version"][row], orgd["coreg"][row]        
        footnote = orgd["footnote"][row]
        
        have_fn = str(footnote != "")
                
        cur.execute("SELECT sub_id FROM subs WHERE adsh = "+adsh+" LIMIT 1;")
        sub_id_num = str(cur.fetchone()[0])

        cur.execute("SELECT tag_id FROM tags WHERE tag = '"+tag+"' LIMIT 1;")
        tag_id_num = str(cur.fetchone()[0])
        
        cur.execute("""SELECT version_id FROM versions WHERE version = 
        '"""+version+"' LIMIT 1;")
        version_id_num = str(cur.fetchone()[0])
        
        sql = """INSERT INTO numbers (sub_id_num, tag_id_num, version_id_num, 
        coreg, ddate, qtrs, uom, value, have_fn) VALUES (
        """+sub_id_num+", "+tag_id_num+", "+version_id_num+", '"+coreg+"', "+ddate+", "+qtrs+", '"+uom+"', "+value+", "+have_fn+");"
        
        cur.execute(sql)
        
        # insert data into 'footnotes' table
        if have_fn == "True":
            cur.execute("SELECT LAST_INSERT_ID();")
            value_id_fn = str(cur.fetchone()[0])
            
            cur.execute("""INSERT INTO footnotes (value_id_fn, footnote) 
            VALUES ("""+value_id_fn+", '"+footnote+"');")
            
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
    
    
    

