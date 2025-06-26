
exec >> ./home/ubuntu/logs/filewatcher.log.`date +"%Y.%m.%d"`
exec 2>&1

echo "running filewatcher `date`"
echo "this is log need to show in fw log file. not in company file "

    exec >> ./home/ubuntu/logs/filewatcher.log.company_name.`date +"%Y.%m.%d"`
    exec 2>&1
    echo "Checking index `date`"
    echo "this is log need to show in company file. not in fw log file. "

echo "this is anonymus log file need to figure where to go"