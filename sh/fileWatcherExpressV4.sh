#!/bin/bash


# * ===========================================================================
# * Copyright 2015, Allego Corporation, MA USA
# *
# * This file and its contents are proprietary and confidential to and the sole
# * intellectual property of Allego Corporation.  Any use, reproduction,
# * redistribution or modification of this file is prohibited except as
# * explicitly defined by written license agreement with Allego Corporation.
# * ===========================================================================

# * ===========================================================================
# fileWatcher.sh
#
# watch a set of directories for inbound files used for user provisioning.
# when files come in, move to a separate directory, and kick off import scripts
# * ===========================================================================


#
# redirect all output to logs
# these lines ensure that all output (normal and error) generate by this script
# in daily log file.
#

# ===============[LOG SETTINGS] =========================
exec >> /home/ubuntu/logs/filewatcher.log.`date +"%Y.%m.%d"`
exec 2>&1

echo "running filewatcher `date`"


# ===============[ENVIRONMENT SETTINGS] =========================
## this line sources the environment variables from `fileWatcherEnv.sh` file
## `fileWatcherEnv.sh` needs to present on sys location.
. /home/ubuntu/allegoAdmin/scripts/fileWatcherEnv.sh

## Import Helper Functions
. /home/ubuntu/allegoAdmin/scripts/fwLibrary.sh



## check for override of env vars passed in as an arg
## This snippet allows the script to dynamically load the environment variables
## if we need to use other env vars just pass the file as an argument1.
if [ -n "$1" ]
then
. $1
fi

# ================== [THRESHOLD SETTINGS] =========================
## Default threshold if not set to 101 in order to ignore threshold functions
if [ -z ${threshold} ]; 
then 
	echo "threshold is unset, defaulting to 101"; threshold=101; 
else 
	echo "threshold is set to '$threshold'"; 
fi

## no longer loop forever, rely on cron instead
## while [ 1 -ne 0 ]
## do
#exec >> /home/ubuntu/logs/filewatcher.log.`date +"%Y.%m.%d"`

# ================= [COMPANY SPECIFIC LOG SETTINGS] =========================
exec >> /home/ubuntu/logs/filewatcher.log.${COMPANY[$index]}.`date +"%Y.%m.%d"`
exec 2>&1
	# (!) this is in between script so 'log.${COMPANY[$index]}.' is seted by other'
	index=0; # Q: (!) what is the purpose of this while loop?
	while [ $index -lt $NUMBER_OF_COMPANIES ]
	do
		echo "Checking ${index} `date`" # Checking 0 Tue Apr 29 14:30:00 UTC 2025 ? what this line means?
   		echo "${COMPANY[$index]}"
   		echo "${COMPANYID[$index]}"
   		
		#
   		# check to see if complete file is present
   		#
		
   		for file in `ls ${SOURCE_PARENT_DIR}${COMPANY[$index]}/UPLOAD/*_complete` # /home/solaris/UPL
   		do
   			echo "file `basename $file` exists"
   			fileName=`basename $file`
   			# get prefix
   			fileLength=`expr $fileName : '.*'`
   			echo "File name length: ${fileLength}"
   			offSet=$((fileLength-9))
   			echo "Offset: ${offSet}"
			prefix=`echo $fileName | cut -b 1-${offSet}`
   			echo "Prefix: ${prefix}"

            usersCSV=${SOURCE_PARENT_DIR}${COMPANY[$index]}/UPLOAD/${prefix}_users.csv

			# Check UTF8 files - put this in a f(x)
	    	case ${COMPANYID[$index]} in
			218|120) # (!) Q: why 218 and 120? fil hal patiya chhe.. but mare dynamic karva nu chhe.
				utfCheck=`iconv -f UTF-8 ${usersCSV} -o /dev/null; echo $?`
            	echo "Checking UTF8 format"
				if [ "$utfCheck" -ne "0" ]
   			echo
	    		then
            		echo "UTF 8 Formatting has invalid characters; exiting"
                	exit 1
            	fi
            	echo "UTF 8 Check Passed"
				;;
	    		*)
				;;
			esac

	    	# FileWatcherExpress updates are part of AAR-1339

            # FileWatcherExpressEnhancement Step 1
            
			# Make two new target files, 
				# addUpdate.csv
				# disable.csv 
			# by comparisons to the previous run's version of users.csv.

            # If no users.csv file exists in this workdirectory
			#	(first run of AUP or a hard reset), touch one as blank.

            # This routine also needs to be done for manual files 
			# 	so support proper manual usage and legacy functions

            # Get previous file.  At this step, 
				# it should always be users.csv inside the workdir 
				# (minus the header). If it doesn't exist, touch a blank one.
            
			# If user provides "legacy" flag, 
				# make a blank previous.csv to reset
            
			previousCheck=${TARGET_PARENT_DIR}${COMPANY[$index]}/users.csv
            previousManualCheck=${TARGET_PARENT_DIR}${COMPANY[$index]}/manual_users.csv
            if [[ -n "$2" && "$2" == "legacy" ]]
            then
                echo "Running Legacy Version with full file"
                # Legacy runs as manual; override Threshold
				threshold=101

				# Make blank previous file to reset the system
				previousCheck=${TARGET_PARENT_DIR}${COMPANY[$index]}/blank.csv
                previousManualCheck=${TARGET_PARENT_DIR}${COMPANY[$index]}/manual_blank.csv
                touch $previousCheck
                touch $previousManualCheck
            else
                if [ -f ${previousCheck} ]
                then
                    echo "A previous Users.csv run as been detected"
                    echo $previousCheck
                else
                    echo "Createing blank Users.csv previous file for first run"
                    touch $previousCheck
                fi

                if [ -f ${previousManualCheck} ]
                then
                    echo "A previous manual_Users.csv run as been detected"
                    echo $previousManualCheck
                else
                    echo "Createing blank manual_Users.csv previous file for first run"
                    touch $previousManualCheck
                fi
            fi

            # Copy previous users.csv 
			# 	(or blank one you just touched, or blank one you forced in there),
			#	as previous.csv
            cp $previousCheck ${TARGET_PARENT_DIR}${COMPANY[$index]}/previous.csv
            previousFile=${TARGET_PARENT_DIR}${COMPANY[$index]}/previous.csv

         
            # Upload usersCSV file to channel in AUP Company
            /usr/local/bin/python3.6 /home/ubuntu/allegoAdmin/scripts/channels/AUPChannelUploader.py ${channelid} ${usersCSV}
            
			
			# Check estimated differences first CASE is based on exit codes. Skip if threshold = 101
			if [[ ${threshold} -lt 101 ]]
        	then
        		percent=$(diffChecker ${previousFile} ${usersCSV} ${threshold} ${LOCATION})
				if [[ ${percent} -eq 1 ]]
				then
					echo "Diff Checker has stopped AUP"
					# Remove complete file and archive Users file when AUP fails
					rm -rf ${SOURCE_PARENT_DIR}${COMPANY[$index]}/UPLOAD/*_complete
					mv ${usersCSV} ${TARGET_PARENT_DIR}/aupFailureArchive/${prefix}_${COMPANY[index]}
				    	#mv ${usersCSV} ${TARGET_PARENT_DIR}/aupFailureArchive
					exit 1
				else
					echo "Diff Checker has passed."
				fi
			fi

            # Copy previous manual_users.csv 
			#	(or blank one you just touched, or blank one you forced in there), 
			#	as manual_previous.csv
            cp $previousManualCheck ${TARGET_PARENT_DIR}${COMPANY[$index]}/manual_previous.csv
            previousManualFile=${TARGET_PARENT_DIR}${COMPANY[$index]}/manual_previous.csv

            # End FileWatcherExpressEnhancement Step 1

            # Create expected users.csv from new file
            # Run dos2unix here to clean up hidden character else the match will fail
            # usersCSV set further up for UTF8 checks
	    	# usersCSV=${SOURCE_PARENT_DIR}${COMPANY[$index]}/UPLOAD/${prefix}_users.csv
            if [ -f ${usersCSV} ]	
            then
                echo ${usersCSV}
				#${ALLEGO_HOME}/scripts/copyToAUPViewer.sh "${COMPANY[$index]}" "${usersCSV}"
			#/usr/local/bin/python3.6 /home/ubuntu/allegoAdmin/scripts/gdrive/gdrive_uploader2.py ${gdriveFolder} ${usersCSV}

			mv ${usersCSV} ${TARGET_PARENT_DIR}${COMPANY[$index]}/users.csv.${prefix}
		        tail -n +2 ${TARGET_PARENT_DIR}${COMPANY[$index]}/users.csv.${prefix} > ${TARGET_PARENT_DIR}${COMPANY[$index]}/users.csv
                	dos2unix ${TARGET_PARENT_DIR}${COMPANY[$index]}/users.csv ${TARGET_PARENT_DIR}${COMPANY[$index]}/users.csv
            fi

            # FileWatcherExpressEnhancement Step 2
            # Compare new users.csv and previous.csv to populate staging tables.
            # If users.csv was blank from Step 1, addUpdate.csv should be a 1:1 copy of users.csv and disable.csv should be empty.

            addUpdateCSV=${TARGET_PARENT_DIR}${COMPANY[$index]}/addUpdate.csv
            disableCSV=${TARGET_PARENT_DIR}${COMPANY[$index]}/disable.csv

            if [ -f ${addUpdateCSV} ]
            then
                mv ${addUpdateCSV} ${addUpdateCSV}.${prefix}
            fi
            if [ -f ${disableCSV} ]
            then
                mv ${disableCSV} ${disableCSV}.${prefix}
            fi

            comm -13 <(sort $previousFile) <(sort ${TARGET_PARENT_DIR}${COMPANY[$index]}/users.csv) > ${TARGET_PARENT_DIR}${COMPANY[$index]}/addUpdate.csv
            comm -23 <(sort $previousFile) <(sort ${TARGET_PARENT_DIR}${COMPANY[$index]}/users.csv) > ${TARGET_PARENT_DIR}${COMPANY[$index]}/disable.csv

            # End FileWatcherExpressEnhancement Step 2

            # Older implementatiosn of groups.csb and userGroupMemberShip.csv
            groupsCSV=${SOURCE_PARENT_DIR}${COMPANY[$index]}/UPLOAD/${prefix}_groups.csv
			if [ -f ${groupsCSV} ]
			then
   				mv ${groupsCSV} ${TARGET_PARENT_DIR}${COMPANY[$index]}/groups.csv.${prefix}
                tail -n +2 ${TARGET_PARENT_DIR}${COMPANY[$index]}/groups.csv.${prefix} > ${TARGET_PARENT_DIR}${COMPANY[$index]}/groups.csv
   			fi

   			userGroupMembershipCSV=${SOURCE_PARENT_DIR}${COMPANY[$index]}/UPLOAD/${prefix}_userGroupMembership.csv
			if [ -f ${userGroupMembershipCSV} ]
			then
   				mv ${userGroupMembershipCSV} ${TARGET_PARENT_DIR}${COMPANY[$index]}/userGroupMembership.csv.${prefix}
                                tail -n +2 ${TARGET_PARENT_DIR}${COMPANY[$index]}/userGroupMembership.csv.${prefix} > ${TARGET_PARENT_DIR}${COMPANY[$index]}/userGroupMembership.csv
   			fi

   			# sunovion Legacy implementation
   			fbtUsersCSV=${SOURCE_PARENT_DIR}${COMPANY[$index]}/UPLOAD/${prefix}_fbt_users.csv
			if [ -f ${fbtUsersCSV} ]
			then
   				mv ${fbtUsersCSV} ${TARGET_PARENT_DIR}${COMPANY[$index]}/fbt_users.csv.${prefix}
				tail -n +2 ${TARGET_PARENT_DIR}${COMPANY[$index]}/fbt_users.csv.${prefix} > ${TARGET_PARENT_DIR}${COMPANY[$index]}/fbt_users.csv
   			fi

            # Manual File Support
   			manualUsersCSV=${SOURCE_PARENT_DIR}${COMPANY[$index]}/UPLOAD/${prefix}_manual_users.csv

            # Normal Process
            if [ -f ${manualUsersCSV} ]
			then
   				#${ALLEGO_HOME}/scripts/copyToAUPViewer.sh "${COMPANY[$index]}" "${manualUsersCSV}" 
				mv ${manualUsersCSV} ${TARGET_PARENT_DIR}${COMPANY[$index]}/manual_users.csv.${prefix}
				tail -n +2 ${TARGET_PARENT_DIR}${COMPANY[$index]}/manual_users.csv.${prefix} > ${TARGET_PARENT_DIR}${COMPANY[$index]}/manual_users.csv
   			fi

            # FileWatcherExpressEnhancement Step 3 - Manual Files
            manualUpdateCSV=${TARGET_PARENT_DIR}${COMPANY[$index]}/manual_update.csv
            if [ -f ${manualUpdateCSV} ]
            then
                mv ${manualUpdateCSV} ${manualUpdateCSV}.${prefix}
            fi
            comm -13 <(sort $previousManualFile) <(sort ${TARGET_PARENT_DIR}${COMPANY[$index]}/manual_users.csv) > ${TARGET_PARENT_DIR}${COMPANY[$index]}/manual_update.csv

   			rm ${SOURCE_PARENT_DIR}${COMPANY[$index]}/UPLOAD/${prefix}_complete
 
   			#
   			# now run the script to load the data into staging tables in the db
   			#
			stageScript=${ALLEGO_HOME}/conf/import/customer/${COMPANY[$index]}/setup_${COMPANY[$index]}.sql
			echo calling ${stageScript} ${TARGET_PARENT_DIR}${COMPANY[$index]}
			${stageScript} 	${TARGET_PARENT_DIR}${COMPANY[$index]}

   			#
   			# now run the script to load from staging into production - run this one asynchronously
   			#
            loadScript=${ALLEGO_HOME}/scripts/import.sh
            echo calling ${loadScript} ${COMPANYID[$index]}
            ${loadScript} ${COMPANYID[$index]} &
   		done

   		index=$((index+1))
	done
#	echo "sleeping for this many secs: ${SLEEP_INTERVAL}"
#	sleep $SLEEP_INTERVAL
## done
