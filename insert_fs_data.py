# -*- coding: utf-8 -*-
"""
Created on Fri Jun 17 10:14:24 2016

@author: Nate Plumb

This file calls sub_data.py, tag_data.py, num_data.py and pre_data.py on files
in the specified directory or list of directories, 'DIRS'.  If no 
directory is specified, it iteratively operates on all directories in the 
current directory.
"""

import os
import MySQLdb
import sub_data as sub
import tag_data as tag
import num_data as num
import pre_data as pre


DIRS = ["Specify desired quarter(s) here.  DIRS must remain a list."]
FILES = ["sub.txt", "tag.txt", "num.txt", "pre.txt"]
    

if DIRS == []: 
    # create list of all subdirectories
    path = '.'
    all_subs = [os.path.join(path, entry) for entry in os.listdir(path) if 
    os.path.isdir(os.path.join(path, entry))]
    
    # create list of only relevant subdirectories    
    for directory in all_subs:        
        if set(FILES).issubset(set(os.listdir(directory))):
            DIRS.append(directory[2:])

DIRS.sort()

for directory in DIRS:
    # get mysql password
    f = open("pw.txt", "r")
    pw = f.read()
    f.close()
    
    # connect to mysql
    conn = MySQLdb.connect(host = "localhost", user = "root", passwd = pw, 
                           db = "fs_db")
    cur = conn.cursor()
    
    # check if directory contents are already in database
    cur.execute("SELECT * FROM quarters WHERE quarter = '"+directory+"';")
    try:
        status = cur.fetchall()[0]
        already_in, completed = status[1], status[2]
        print already_in, "already in database" 
        if not completed:
            print "Warning: not all data from", already_in, "currently in database"
        conn.close()
    except IndexError:
        cur.execute("""INSERT INTO quarters (quarter, insert_completed) VALUES (
        '"""+directory+"', False);")
        conn.commit()
        conn.close()

        print "Processing sub.txt file from", directory, "\n"
        sub.sub_data(directory)
        print "Processing tag.txt file from", directory, "\n"
        tag.tag_data(directory)
        print "Processing num.txt file from", directory, "\n"
        num.num_data(directory)
        print "Processing pre.txt file from", directory, "\n"
        pre.pre_data(directory)
        
         # reconnect to mysql
        conn = MySQLdb.connect(host = "localhost", user = "root", passwd = pw, 
                           db = "fs_db")
        cur = conn.cursor()
        
        # update insert_completed status
        cur.execute("""UPDATE quarters SET insert_completed = True WHERE 
        quarter = '"""+directory+"';")
        conn.commit()
        conn.close()
        
print "All requested data have been added to the database."