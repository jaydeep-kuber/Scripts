## FileWatcherExpress
- This is main script file. 

<hr>

- setting logs
```bash 
    exec >> /home/ubuntu/logs/filewatcher.log.`date +"%Y.%m.%d"`
    exec 2>&1
    echo "one shell behavioiur echo occuring before compay log file will save in fw.log file no indentation matters"
    # and 

    exec >> /home/ubuntu/logs/filewatcher.log.${COMPANY[$index]}.`date +"%Y.%m.%d"`
    exec 2>&1
    echo "but once it encounter other log file like above then it makes it the new log file and start writing in this file, here also indentation not matters"
``` 
- there is single log dir

```text
/home/ubuntu/
        └── logs/
            ├── fwSh.log.2025.05.21
            ├── fwSh.log.2025.05.22
            ├── fwSh.log.Google.2025.05.22
            ├── fwSh.log.AWS.2025.05.22
            └── ...
```

- import libs and load envs
```bash
    ## set default env vars
    . /home/ubuntu/allegoAdmin/scripts/fileWatcherEnv.sh

    ## Import Helper Functions
    . /home/ubuntu/allegoAdmin/scripts/fwLibrary.sh
```

- loading env if passed
```bash
if [ -n "$1" ]
then
. $1
fi
```

- thresold
```bash
    if [ -z ${threshold} ]; 
    then 
        echo "threshold is unset, defaulting to 101"; 
        threshold=101; 
    else 
        echo "threshold is set to '$threshold'"; 
    fi
```
- set log file to company file: `filewatcher.log.${COMPANY[$index]}.`date +"%Y.%m.%d" `
- now all the logs puts here.

- While **looping** on range `number_of_company`

``` bash
    index=0;
    while [ $index -lt $NUMBER_OF_COMPANIES ]
    do
    # ...
```

- Inner for loop
```bash
    # for file in 'ls /home/AWS/UPLOAD/*_complete'
    for file in `ls ${SOURCE_PARENT_DIR}${COMPANY[$index]}/UPLOAD/*_complete`
	do
    # ...
```

>   Assumption
>      - `_complete` file always be there. 
>     **Q: but what i need to do if it is not there?**

- **get prefix**
- `usersCSV=${SOURCE_PARENT_DIR}${COMPANY[$index]}/UPLOAD/${prefix}_users.csv`
    - > Assmption 
      > this  file is exists but **Q what i need to do if not there** 
- **go for UTF-8 check**
- **GAME STARTS**
```bash
	previousCheck=${TARGET_PARENT_DIR}${COMPANY[$index]}/users.csv
    previousManualCheck=${TARGET_PARENT_DIR}${COMPANY[$index]}/manual_users.csv
```
- vars to hold path for a file, just hold path

- **legacy implementation**
- check if second flag is there and also it have value as "legacy" only
- **if** legacy is there. 
```bash 
    # ...
    threshold=101
	# Make blank previous file to reset the system
	previousCheck=${TARGET_PARENT_DIR}${COMPANY[$index]}/blank.csv
    previousManualCheck=${TARGET_PARENT_DIR}${COMPANY[$index]}/manual_blank.csv
    # ...
```
- **else**

- checking if `previousCheck` and `previousManualCheck` is there, if not then make a blank

- copy `user.csv` to `previous.csv`

```bash 
    cp $previousCheck ${TARGET_PARENT_DIR}${COMPANY[$index]}/previous.csv
       previousFile=${TARGET_PARENT_DIR}${COMPANY[$index]}/previous.csv
```

- upload file in channel : `/usr/local/bin/python3.6 /home/ubuntu/allegoAdmin/scripts/channels/AUPChannelUploader.py ${channelid} ${usersCSV}`

- Check estimated differences first CASE is based on exit codes. Skip if threshold = 101

- **time to call Diffchecker** if threshol < 101 else skip.
```bash 
if [[ ${threshold} -lt 101 ]]
    	then
    		percent=$(diffChecker ${previousFile} ${usersCSV} ${threshold} ${LOCATION})
			if [[ ${percent} -eq 1 ]]
			then
				echo "Diff Checker has stopped AUP"
				rm -rf ${SOURCE_PARENT_DIR}${COMPANY[$index]}/UPLOAD/*_complete
				mv ${usersCSV} ${TARGET_PARENT_DIR}/aupFailureArchive/${prefix}_${COMPANY[$index]}
				exit 1
			else
				echo "Diff Checker has passed."
			fi
		fi
```
> `mv ${usersCSV} ${TARGET_PARENT_DIR}/aupFailureArchive/${prefix}_${COMPANY[index]}`
> Q: in this line prefix is company name and _${COMPANY[index]} too so what does it mean?


- copy `manual_user.csv` to `manual_previous.csv`

```bash
    cp $previousManualCheck ${TARGET_PARENT_DIR}${COMPANY[$index]}/manual_previous.csv
        previousManualFile=${TARGET_PARENT_DIR}${COMPANY[$index]}/manual_previous.csv
```

- `usersCSV=${SOURCE_PARENT_DIR}${COMPANY[$index]}/UPLOAD/${prefix}_users.csv`
``` bash
# usersCSV=${SOURCE_PARENT_DIR}${COMPANY[$index]}/UPLOAD/${prefix}_users.csv
        if [ -f ${usersCSV} ]
        then
		    mv ${usersCSV} ${TARGET_PARENT_DIR}${COMPANY[$index]}/users.csv.${prefix}
	        
            tail -n +2 ${TARGET_PARENT_DIR}${COMPANY[$index]}/users.csv.${prefix} > ${TARGET_PARENT_DIR}${COMPANY[$index]}/users.csv
            
            dos2unix ${TARGET_PARENT_DIR}${COMPANY[$index]}/users.csv ${TARGET_PARENT_DIR}${COMPANY[$index]}/users.csv
        fi
```
- move to a temp file : `users.csv.${prefix}` for backup. 
- remove headers using tail
- convert to unix format using `dos2unix`

> Vague line: # If users.csv was blank from Step 1, addUpdate.csv should be a 1:1 copy of users.csv and disable.csv should be empty.

```bash
    addUpdateCSV=${TARGET_PARENT_DIR}${COMPANY[$index]}/addUpdate.csv
    disableCSV=${TARGET_PARENT_DIR}${COMPANY[$index]}/disable.csv
```

- `addUpdateCSV` : just save path no care of file. 
- `disableCSV` : just save path no care of file.

- rename above file
```bash
    if [ -f ${addUpdateCSV} ]
    then
        mv ${addUpdateCSV} ${addUpdateCSV}.${prefix}
    fi
    if [ -f ${disableCSV} ]
    then
        mv ${disableCSV} ${disableCSV}.${prefix}
    fi
```

- count diff 

```bash 
    comm -13 <(sort $previousFile) <(sort ${TARGET_PARENT_DIR}${COMPANY[$index]}/users.csv) > ${TARGET_PARENT_DIR}${COMPANY[$index]}/addUpdate.csv
    comm -23 <(sort $previousFile) <(sort ${TARGET_PARENT_DIR}${COMPANY[$index]}/users.csv) > ${TARGET_PARENT_DIR}${COMPANY[$index]}/disable.csv
```
- preform mv , remove header for blow files.
    - `groupsCSV=${SOURCE_PARENT_DIR}${COMPANY[$index]}/UPLOAD/${prefix}_groups.csv`
    - `userGroupMembershipCSV=${SOURCE_PARENT_DIR}${COMPANY[$index]}/UPLOAD/${prefix}_userGroupMembership.csv`
    - `fbtUsersCSV=${SOURCE_PARENT_DIR}${COMPANY[$index]}/UPLOAD/${prefix}_fbt_users.csv`
    - `manualUsersCSV=${SOURCE_PARENT_DIR}${COMPANY[$index]}/UPLOAD/${prefix}_manual_users.csv`

- manual upadte Step 3 - Manual Files
    - `manualUpdateCSV=${TARGET_PARENT_DIR}${COMPANY[$index]}/manual_update.csv`
``` bash   
    
    if [ -f ${manualUpdateCSV} ]
    then
        mv ${manualUpdateCSV} ${manualUpdateCSV}.${prefix}
    fi
    comm -13 <(sort $previousManualFile) <(sort ${TARGET_PARENT_DIR}${COMPANY[$index]}/manual_users.csv) > ${TARGET_PARENT_DIR}${COMPANY[$index]}/manual_update.csv
	rm ${SOURCE_PARENT_DIR}${COMPANY[$index]}/UPLOAD/${prefix}_complete
```

- **now run the script to load the data into staging tables in the db**

these steps are not too ...
<hr>

#### flow - what is going on and what i need to do?

1. redirect all output to logs
2. set default env vars and Import Helper Functions
3. check for override of env vars passed in as an arg that means i if user passes `env file` in `arg` i have to use this file. so i need to make fucntion accordingly.
> - ways: 
    1. create a funtion with default path, if user pass then it override this path.
4. checking for thresold 101 in order to ignore function
5. log setting for company now sh points to new file `compnay.file` each echo will log there from onwards.

### ( ) looping 
- **while loop**
    
    - iterate till number of compay
    > Q: what does number of company var val mean ? like if company are less then value of number of company then it cause problem.  
        - solution: i have to stop process if numberOfCompany != company != companyid

    - **for loop** (inner loop)
        - this loop loops over `_complete` file.

        - Tsk-1 : get prefix of current file in **src** from name we will extract `_complete` for prefix

        - Tsk-2 : make `usersCSV` file path and store it.
            > usersCSV=${SOURCE_PARENT_DIR}${COMPANY[$index]}/UPLOAD/${prefix}_users.csv
            > i need to buld this path and store in `usersCSV` not care if file is there or not

        - Tsk-3 : Check UTF8 files 
        
        ### Game starts from here.
        
        - Instructions 
            > By comparisons -> previous run's version of `users.csv`. 
            > Make two new target files, `addUpdate.csv` and `disable.csv`.
            
            > If no users.csv file exists in this workdirectory
            > make blank file. i.e. first run. This routine also needs to be done for manual files 
            
            > Get previous file. At this step, it should always be users.csv inside the workdir
            > If it doesn't exist, touch a blank one.
            > If user provides "legacy" flag, make a blank `previous.csv` to reset

        > target: `/home/ubuntu/allegoAdmin/workdir/`
        - Tsk-1 : `previousCheck` : `/home/ubuntu/allegoAdmin/workdir/company` path of `user.csv` in target dir `previousManualCheck` : `/home/ubuntu/allegoAdmin/workdir/company` path of `manual_users.csv` in target dir 


#### Problems assumed
> 1 

- now addUpadate file and disable file is creating and renaming... 
- so these files need to be there is these files not there then error boom. 
- so in first itern file is renamed so in sec day if files wont be there then error boom.

> 2

```bash
	mv ${groupsCSV} ${TARGET_PARENT_DIR}${COMPANY[$index]}/groups.csv.${prefix}
            tail -n +2 ${TARGET_PARENT_DIR}${COMPANY[$index]}/groups.csv.${prefix} > ${TARGET_PARENT_DIR}${COMPANY[$index]}/groups.csv
```
