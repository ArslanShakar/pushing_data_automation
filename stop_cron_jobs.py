from crontab import CronTab

my_cron = CronTab(user=True)
my_cron.remove_all()
my_cron.write()
print("All CRON JOBS has been removed successfully")
