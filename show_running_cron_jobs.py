from crontab import CronTab

cron_jobs = CronTab(user=True)
if not cron_jobs:
    print("NO CRON JOB FOUND")

for job in cron_jobs:
    print(job)
