DOCUMENTATION

********* ALTER TABLES *********
I have ALTER both database tables "Added UPTO TWO NEW Columns/Fields":

1) add field "id" as primary key, Int and autoincremented.
2) add field "update_flag", TINYINT default 0.

These changes done in both databases tables are:
1) "restaurant_price_and_qty_staging",
2) "yelp_staging",
3) "restaurant_detail_staging",
4) "price_and_quantity_staging",


******** ALTER TABLES *******
1) add one field "update_flag", TINYINT default 0.

Added "update_flag" field in both database tables are:
1) "business",
2) "product_staging"


******* DATABASE TABLES TRIGGERS *********
Live Database Tables TRIGGERS are defined in TEXT. Just to make sure you
what changes I have implemented.


******** RUNNING SCRIPTS & COMMANDS *******
** For Pushing Data to Live Database Please execute the Script "push_data_automation.py":
Run Command: python3 push_data_automation.py

** To Run Cron jobs | Schedule Scripts to run on daily please execute Script "cron_jobs.py":
Note: To run the script must open terminal in same directory where script is placed and type command.
Run Command: python3 cron_jobs.py

** To check which cron jobs are running on your server please type this command on terminal:
Run Command: python3 show_running_cron_jobs.py
OR
Run Command: crontab -l

** To remove all previous scheduled cron jobs please run script "stop_cron_jobs.py":
Run Command: python3 stop_cron_jobs.py

*********  DATA UPDATING FLAG's **********
update_flag field till now it has 4 values and their specific meanings:
update_flag = 0 : "0" means data is just fresh inserted into table by some script.
update_flag = 1 : "1" means data is formatted and cleaned.
update_flag = 2 : "2" means that is foramtted, cleaned & it have been moved to live database.
update_flag = 6 : "6" means it is bad data, May be some required fields are empty or   invalid,
irrelevant data or may it has some sort of bad data.

Best Regards,
https://www.fiverr.com/alifarslan/

Thank you!

🥳🥳🥳