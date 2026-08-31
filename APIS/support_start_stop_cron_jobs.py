
import os
os.environ['OPENSSL_CONF']='/home/aikernel/src/configs/openssl.cnf'
from crontab import CronTab

def stop_all_cron_jobs():
    cron = CronTab(user=True)
    for job in cron:
        job.enable(False)
    cron.write()

def start_all_cron_jobs():
    cron = CronTab(user=True)
    for job in cron:
        job.enable(True)
    cron.write()

def restart_cron_service():
    os.system('sudo service cron restart')


class main():
    def main(self,action):
        if action == 'stop':
            stop_all_cron_jobs()
            restart_cron_service()
            print("All cron jobs have been stopped.")
        elif action == 'start':
            start_all_cron_jobs()
            restart_cron_service()
            print("All cron jobs have been started.")
        else:
            print("Invalid action. Please enter 'start' or 'stop'.")

# if __name__ == '__main__':
#     action = input("Enter 'start' to enable all cron jobs or 'stop' to disable all cron jobs: ").strip().lower()
#     main().main(action)