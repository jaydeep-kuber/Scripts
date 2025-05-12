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

# AUP diff checker diffChecker (previousfile, currentfile, threshold, server)

diffChecker() {
	# Input Args of Previous File, Current File
	diffCurrentCount=0;
    diffPrevCount=0;
	diffCount=0;
	diffRatio=0;
    myT=${3};
    server=${4};
    
    # Make temp files split by companyId
    cid=${COMPANYID[$index]};
    temp_p="/tmp/diffprevious_${cid}.csv";
    temp_c="/tmp/diffcurrent_${cid}.csv";

    # DB config path
    CONFIG=/home/ubuntu/allegoAdmin/scripts/prod.json
    # Delete tmp files
    rm ${temp_p};
    rm ${temp_c};

    # Copy files to tmp becauae dos2unix is annoying
	cp ${1} ${temp_p};
	cp ${2} ${temp_c};
	dos2unix ${temp_p};
	dos2unix ${temp_c};
	
	# Diff Previous File and Current File, get # of row diffs
	diffCount="$(comm -12 <(sort ${temp_p}) <(sort ${temp_c}) | wc -l | awk '{print $1}')"

	# Get Count of Total Rows in Both Files
	diffCurrentCount="$(wc -l ${temp_c} | awk '{print $1}')"
    #echo ${diffCurrentCount}

    diffPreviousCount="$(wc -l ${temp_p} | awk '{print $1}')"
    #echo ${diffPreviousCount}

	# Email Headers
	# SUBJECT="AUP Changeset Warning: ${server}";
	FROM="From: Ad-Hoc Reports System <no-reply@allego.com>";
	TO="jira@allego.atlassian.net";
	CC="operations@allego.com";
	DATE=$(date +"%F");

    # If a failure case is hit, return value and exit function.  Values selected are target values for fileWatcher
    # Failure Case 1: "Empty" File
    if [[ ${diffCurrentCount} -eq 0 ]]
    then
    CASE_1_SUBJECT="AUP Changeset Warning-Empty File: ${COMPANY[$index]} ${DATE}";
    CASE_1_BODY="Empty file Detected for Company: ${COMPANY[$index]}.  Check for a 0KB file or a _complete file without any paired users file."
		aws ses send-email --from email-admin@allego.com --destination '{"ToAddresses":["jira@allego.atlassian.net"]}' --message "{\"Subject\":{\"Data\":\"${CASE_1_SUBJECT}\"},\"Body\":{\"Text\":{\"Data\":\"${CASE_1_BODY}\"}}}" --region us-east-1 > /dev/null 2>&1
    # Set Company on hold until the issue resolves
    /usr/local/bin/python3.6 /home/ubuntu/allegoAdmin/scripts/setCompanyOnHold.py ${CONFIG} ${cid}

		#echo "Empty file Detected for Company: ${COMPANY[$index]}." | sudo mutt -s "${CASE_1_SUBJECT}" -e "my_hdr ${FROM}" "${TO}" -c "${CC}";
        echo 1;
        exit 1;
	fi;
	
    # Failure Case 2: Lots of missing Rows, not based on updates, very sensitive.
    if [[ ${diffPreviousCount} -gt ${diffCurrentCount} ]]
    then
        CASE_2_SUBJECT="AUP Changeset Warning-Lots of missing Rows: ${COMPANY[$index]} ${DATE}";
        diffRatio="$(awk -v d=$diffPreviousCount -v t=$diffCurrentCount 'BEGIN { printf "%d\n",((d-t)/d*100)}')";
        #echo ${diffRatio}
        if [[ ${diffRatio} -gt ${myT} ]]
        then
            CASE_2_BODY="Possible file truncation for company ${COMPANY[$index]}.  File size is significantly smaller than the last run file or is corrupted."
		        aws ses send-email --from email-admin@allego.com --destination '{"ToAddresses":["jira@allego.atlassian.net"]}' --message "{\"Subject\":{\"Data\":\"${CASE_2_SUBJECT}\"},\"Body\":{\"Text\":{\"Data\":\"${CASE_2_BODY}\"}}}" --region us-east-1 > /dev/null 2>&1
            # Set Company on hold until the issue resolves
            /usr/local/bin/python3.6 /home/ubuntu/allegoAdmin/scripts/setCompanyOnHold.py ${CONFIG} ${cid}

            #echo  "Possible file truncation for company ${COMPANY[$index]}" | sudo mutt -s "${CASE_2_SUBJECT}" -e "my_hdr ${FROM}" "${TO}" -c "${CC}";
            echo 1;
            exit 1;
        fi;
    fi;

    # Failure Case 3: Too many general changes
    # Compute Diffs/RowCount ratio, send value back to filewatcher to evaluate.
    diffRatio="$(awk -v d=$diffCount -v t=$diffCurrentCount 'BEGIN { printf "%d\n",((t-d)/t*100)}')";
    if [[ ${diffRatio} -gt ${myT} ]]
    	then
    	      CASE_3_SUBJECT="AUP Changeset Warning-Too many general changes: ${COMPANY[$index]} ${DATE}";
    	      CASE_3_BODY="Too many changes detected for company ${COMPANY[$index]}. ${diffRatio} percent of the file requires updating, which is greater than the current threshold value of ${myT} percent.";
    	      aws ses send-email --from email-admin@allego.com --destination '{"ToAddresses":["jira@allego.atlassian.net"]}' --message "{\"Subject\":{\"Data\":\"${CASE_3_SUBJECT}\"},\"Body\":{\"Text\":{\"Data\":\"${CASE_3_BODY}\"}}}" --region us-east-1 > /dev/null 2>&1
            # Set Company on hold until the issue resolves
            /usr/local/bin/python3.6 /home/ubuntu/allegoAdmin/scripts/setCompanyOnHold.py ${CONFIG} ${cid}

            #echo  "Too many changes detected for company ${COMPANY[$index]}, ${diffRatio} percent of the file requires updating, which is greater than the current threshold value of ${myT} percent." | sudo mutt -s "${CASE_3_SUBJECT}" -e "my_hdr ${FROM}" "${TO}" -c "${CC}";
            echo 1;
        	exit 1;
    fi;
    # Range of changes ok
    TO="lperrault@allego.com"
	  SUBJECT="AUP Safe Launch Notification: ${server}"
    echo "${diffRatio} percent of the userbase is changing, less than the current threshold of ${myT} percent. AUP now running for Company: ${COMPANY[$index]}" | sudo mutt -s "${SUBJECT}" -e "my_hdr ${FROM}" "${TO}";   		
    echo 0;
    exit 1;
}