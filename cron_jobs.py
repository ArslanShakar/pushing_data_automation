from crontab import CronTab


def schedule_job():
    cron = CronTab(user=True)
    job1 = cron.new(command="python push_data_automation.py", comment="push_data_automation")
    job1.hour.every(6)
    cron.write()


schedule_job()
