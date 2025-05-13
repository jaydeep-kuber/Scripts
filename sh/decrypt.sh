for file in `ls /home/tiaa/UPLOAD/*_complete`
do
  echo "file `basename $file` exists"
  fileName=`basename $file`
  # get prefix
  fileLength=`expr $fileName : '.*'`
  offSet=$((fileLength-9))
  prefix=`echo $fileName | cut -b 1-${offSet}`
  echo $prefix  gpg --output /home/tiaa/UPLOAD/${prefix}_tiaa_users.csv /home/tiaa/UPLOAD/${prefix}_users.csv
  touch /home/tiaa/UPLOAD/${prefix}_tiaa_complete
  mv /home/tiaa/UPLOAD/${prefix}_users.csv /home/tiaa/archive
  rm /home/tiaa/UPLOAD/${prefix}_complete

done

##################################################################
for file in `ls /home/kronos/UPLOAD/*_complete.csv.pgp`
do
  echo "file `basename $file` exists"
  fileName=`basename $file`
  # get prefix
  fileLength=`expr $fileName : '.*'`
  offSet=$((fileLength-17))
  prefix=`echo $fileName | cut -b 1-${offSet}`  gpg --output /home/kronos/UPLOAD/${prefix}_users.csv /home/kronos/UPLOAD/${prefix}_users.csv.pgp
  touch /home/kronos/UPLOAD/${prefix}_complete
  mv /home/kronos/UPLOAD/*.pgp /home/kronos/archive
done