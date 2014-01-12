#! /bin/bash

distro=`uname -v | grep -oi 'debian'`

if [ ${distro,,} = "debian" ]; then
echo ${distro,,}
exit 1
else
distro=`uname -v | grep -oi 'ubuntu'`
if [ ${distro,,} = "debian" ]; then
echo "debian"
exit 1
fi 
fi

echo "other"
exit 0
