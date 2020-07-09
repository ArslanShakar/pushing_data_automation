from crontab import CronTab


def schedule_job():
    cron = CronTab(user=True)
    job1 = cron.new(command="python push_data_automation.py", comment="Pushing Data To Live Automation")
    job1.hour.every(4)
    cron.write()


schedule_job()
