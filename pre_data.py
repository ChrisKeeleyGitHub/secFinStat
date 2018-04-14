# -*- coding: utf-8 -*-
"""
Created on Wed Jun 15 10:37:26 2016

@author: Nate Plumb

This file contains a function created for the financial statements data from 
SEC filings found at 
https://www.sec.gov/dera/data/financial-statement-data-sets.html.
The function extracts data from the pre.txt file, organizes the data and 
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
    

# primary function
def pre_data(sub_dir):
    # extract data
    pre = []
    with open(sub_dir+"/pre.txt", "r") as f:
        reader = csv.reader(f, delimiter = "\t")
        for row in reader:
            pre.append(row)
            
    # print number of rows in data
    total_rows = len(pre)
    print "Rows in file:", total_rows, "\n"
                
    # arrange data by column
    header = pre[0]
    cols = []
    for col_idx in range(len(header)):
        data = []
        for row_idx in range(1, len(pre)):
            data.append(pre[row_idx][col_idx])
        cols.append(data)
    
    # organize data in dictionary
    orgd = {}
    idx = 0
    for field in header:
        orgd[field] = cols[idx]
        idx += 1
    
    # escape any "'", remove extra backslashes and remove hyphens from adsh
    for field in orgd:
        for idx in range(len(orgd[field])):
            if field == "adsh":
                orgd[field][idx] = remove_hy(orgd[field][idx])
            orgd[field][idx] = clean(orgd[field][idx])
            
       
    # get mysql password
    f = open("pw.txt", "r")
    pw = f.read()
    f.close()
    
    # connect to mysql
    conn = MySQLdb.connect(host = "localhost", user = "root", passwd = pw, 
                           db = "fs_db")
    cur = conn.cursor()
    
    # insert data into 'presentations' table
    count = 1
    start_time = time.time()
    print "Entering data into database", "\n"
    for row in range(len(pre) - 1):
        report, line, adsh = orgd["report"][row], orgd["line"][row], orgd["adsh"][row]
        stmt, inpth, tag = orgd["stmt"][row], orgd["inpth"][row], orgd["tag"][row]
        plabel, version = orgd["plabel"][row], orgd["version"][row]
        
        cur.execute("SELECT sub_id FROM subs WHERE adsh = "+adsh+" LIMIT 1;")
        sub_id_pres = str(cur.fetchone()[0])
        
        cur.execute("SELECT tag_id FROM tags WHERE tag = '"+tag+"' LIMIT 1;")
        tag_id_pres = str(cur.fetchone()[0])
        
        cur.execute("""SELECT version_id FROM versions WHERE version = 
        '"""+version+"' LIMIT 1;")
        version_id_pres = str(cur.fetchone()[0])
        
        sql = """INSERT INTO presentations (sub_id_pres, report, line, stmt, 
        inpth, tag_id_pres, version_id_pres, plabel) VALUES (
        """+sub_id_pres+", +"+report+", "+line+", '"+stmt+"', "+inpth+", "+tag_id_pres+", "+version_id_pres+", '"+plabel+"');"
                
        cur.execute(sql)
        
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
    
    

