#!/bin/sh

#
# supported companies
#
NUMBER_OF_COMPANIES=3
COMPANY[0]=solarcity
COMPANY[1]=sunovion
COMPANY[2]=fatty

COMPANYID[0]=14
COMPANYID[1]=13
COMPANYID[2]=17

#
#  misc settings (random | miscellaneous)
#
ALLEGO_HOME=/home/ubuntu/allegoAdmin
SLEEP_INTERVAL=60
SOURCE_PARENT_DIR=/home/
TARGET_PARENT_DIR=/home/ubuntu/allegoAdmin/workdir/
MYSQL_CMD="mysql AllegoCoreDB -u <user> -p <password> -h <DB-URL>"
export MYSQL_CMD
