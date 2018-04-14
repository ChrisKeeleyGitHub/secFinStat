# -*- coding: utf-8 -*-
"""
Created on Fri Jun 10 07:57:21 2016

@author: Nate Plumb

This file contains a function created for the financial statements data from 
SEC filings found at 
https://www.sec.gov/dera/data/financial-statement-data-sets.html.
The function extracts data from the sub.txt file, organizes the data and 
puts it in the fs_db database.
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
    
def has_partial(aciks):
    flag = False
    aciks = aciks.split(" ")
    for cik in aciks:
        if cik == "PARTIAL":
            flag = True
    return flag
    
def check_range(year):
    if year == "":
        year = 1901
    elif int(year) < 1901 or int(year) > 2155:
        year = 1901
    return str(year)
    
def check_null_date(nnv):
    if nnv == "":
        nnv = "0000"
    return nnv

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
def sub_data(sub_dir):
    # extract data          
    sub = []
    with open(sub_dir+"/sub.txt", "r") as f:
        reader = csv.reader(f, delimiter = "\t")
        for row in reader:
            sub.append(row)  

    # print number of rows in data
    total_rows = len(sub)
    print "Rows in file:", total_rows, "\n"
    
    # arrange data by column
    header = sub[0]
    cols = []
    for col_idx in range(len(header)):
        data = []
        for row_idx in range(1, len(sub)):
            data.append(sub[row_idx][col_idx])
        cols.append(data)
    
    # organize data in dictionary
    orgd = {}
    idx = 0
    for field in header:
        orgd[field] = cols[idx]
        idx += 1
    
    # escape any "'", remove extra backslashes, remove hyphens from adsh,
    # check for null fye and check for out of range years in fy
    for field in orgd:
        for idx in range(len(orgd[field])):
            orgd[field][idx] = clean(orgd[field][idx])
            if field == "adsh":
                orgd[field][idx] = remove_hy(orgd[field][idx])
            elif field == "fye":
                orgd[field][idx] = check_null_date(orgd[field][idx]) 
            elif field == "fy":
                orgd[field][idx] = check_range(orgd[field][idx])
            
        
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
    for row in range(len(sub) - 1):
        
        # insert data into 'forms' table
        form = orgd["form"][row]
        cur.execute("INSERT IGNORE INTO forms (type) VALUES ('"+form+"');")
    
    
        # insert data into 'firms_current' table
        cik, name, sic = orgd["cik"][row], orgd["name"][row], orgd["sic"][row]
        countryinc, stprinc = orgd["countryinc"][row], orgd["stprinc"][row]
        
        sql = """INSERT IGNORE INTO firms_current (cik, name, sic, countryinc, 
        stprinc) VALUES ("""+cik+", \""+name+"\", '"+sic+"', '"+countryinc+"', '"+stprinc+"');"        

        cur.execute(sql)
 
    
        # insert data into 'subs' table
        detail, afs, wksi = orgd["detail"][row], orgd["afs"][row], orgd["wksi"][row]
        nciks, period, fye = orgd["nciks"][row], orgd["period"][row], orgd["fye"][row]
        fp, filed, fy = orgd["fp"][row], orgd["filed"][row], orgd["fy"][row]
        accepted, prevrpt = orgd["accepted"][row], orgd["prevrpt"][row]
        adsh = orgd["adsh"][row]
        
        aciks_partial = str(has_partial(orgd["aciks"][row]))
    
        cur.execute("""SELECT firm_id FROM firms_current WHERE cik = 
        """+cik+" LIMIT 1;")
        firm_id = str(cur.fetchone()[0])
        
        cur.execute("""SELECT form_id FROM forms WHERE type = 
        '"""+form+"' LIMIT 1;")
        form_id = str(cur.fetchone()[0])
        
        sql = """INSERT IGNORE INTO subs (adsh, firm_id_subs, form_id_subs, 
        afs, wksi, fye, period, fy, fp, filed, accepted, prevrpt, detail, nciks, 
        aciks_partial) VALUES (
        """+adsh+", "+firm_id+", "+form_id+", '"+afs+"', "+wksi+", '"+fye+"', "+period+", "+fy+", '"+fp+"', "+filed+", '"+accepted+"', "+prevrpt+", "+detail+", "+nciks+", "+aciks_partial+");"
                        
        cur.execute(sql)
        
        count += 1
        

        # insert data into 'firms_past' table
        if orgd["former"][row] != "":
            changed, former = orgd["changed"][row], orgd["former"][row]

            sql = """INSERT IGNORE INTO firms_past (firm_id_fp, former, changed) 
            VALUES ("""+firm_id+", '"+former+"', "+changed+");"

            cur.execute(sql)
            

        # insert data into 'aciks' table
        if nciks > 1:
            cur.execute("""SELECT sub_id FROM subs WHERE adsh = 
            """+adsh+" LIMIT 1;")
            sub_id = str(cur.fetchone()[0])
            
            aciks = orgd["aciks"][row].split(" ")
            for sub_cik in aciks:
                sub_cik = str(sub_cik)
                if sub_cik != "":
                    while len(sub_cik) < 10:
                        sub_cik = "0"+sub_cik
                    sql = """SELECT firm_id FROM firms_current WHERE cik = 
                    """+sub_cik+" LIMIT 1;"
                    cur.execute(sql)
                    
                    try:
                        firm_id_subsid = str(cur.fetchone()[0])
                        sql = """INSERT IGNORE INTO aciks (sub_id_aciks, 
                        firm_id_parent, firm_id_subsid) VALUES (
                        """+sub_id+", "+firm_id+", "+firm_id_subsid+");"
                        cur.execute(sql)
                        
                    except TypeError:
                        sql = """INSERT IGNORE INTO aciks (sub_id_aciks, 
                        firm_id_parent, cik_subsid) VALUES (
                        """+sub_id+", "+firm_id+", "+sub_cik+");"

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
    
                
    
    