# secFinStat
Repo for apps and analyses using SEC financial statement data found at https://www.sec.gov/dera/data/financial-statement-data-sets.html.

Contains the following items:

*	download_fs_data.py - downloads and unzips all data at the above url not currently in the working directory
*	fs_db_diag.png - EER diagram of database used to organize and store data, fs_db
*	tables_by_file.txt - simple list of tables in fs_db organized by the files which contain relevant data
*	sub_data.py - extracts data from sub.txt files and adds to fs_db
*	tag_data.py - extracts data from tag.txt files and adds to fs_db
*	num_data.py - extracts data from num.txt files and adds to fs_db
*	pre_data.py - extracts data from pre.txt files and adds to fs_db
*	insert_fs_data.py - calls all four files above to extract and add data for a specified list of quarters or all quarters
in working directory which are not already in db

This project is under re-evaluation.
