from crontab import CronTab

my_cron = CronTab(user=True)

for job in my_cron:
    if job.comment == "push_data_automation":
        my_cron.remove(job)

# my_cron.remove_all()
my_cron.write()
print("All CRON JOBS has been removed successfully")
