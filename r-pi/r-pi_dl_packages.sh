#! /bin/bash

packages="libqtcore4 libqt4-dev python-qt4 python-twisted libconfig-file-perl libqt4-designer 
	  libqt4-scripttools libqt4-help libqt4-test libqtassistantclient4 libqtwebkit4 libqt4-declarative libqt4-script
	  libqt4-xmlpatterns libqt4-dev-bin libqt4-qt3support libqt4-sql qt4-linguist-tools
          qt4-qmake
          python-psutil python-pyasn1 python-sip python-crypto python-openssl
          python-twisted-conch python-twisted-lore python-twisted-mail python-twisted-news python-twisted-runner 
	  python-twisted-words python-twisted-core python-twisted-web python-twisted-names python-twisted-bin
	  python-zope.interface
	  python-pkg-resources
	  "

arch="i386"

for i
do
	arg=$i
done

if [[ "$arg" == -* ]]; then
	arch=${i:1} 
fi

if  [ ! -d "$arch" ]; then 
	mkdir $arch
fi

cd $arch

for pkg in $packages; 
do
	apt-get -o APT::Architecture=$arch download $pkg
done

cd ..

exit
