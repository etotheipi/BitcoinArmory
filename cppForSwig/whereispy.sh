#! /bin/bash

whereispy=`whereis "python"`

echo 1>&2
echo 1>&2 "looking for python paths..."
echo 1>&2

v27="2.7"
v26="2.6"
pyv=""

sopath=""
apath=""
hpath=""
pythonver=""
pythonpath=""

for i in $whereispy; do
	
	if [[ "$apath" ]]; then 
		#kills the loop is a matching .a was found, keeps running if it can only find .so
		break
	fi

	if echo "$i" | grep -q "/lib"; then
		pyv=""
		if echo "$i" | grep -q "$v27"; then
			pyv=$v27
		elif echo "$i" | grep -q "$v26"; then
			pyv=$v26
		fi

		if [ "$pyv" ]; then
			possiblea=""
			possibleso=""
			libpath=`whereis "libpython$pyv".`
			for z in $libpath; do
				if echo "$z" | grep -q "$pyv.a"; then
					possiblea=$z
				elif echo "$z" | grep -q "$pyv.so"; then
					possibleso=$z
				fi
			done
		
			#whereis may not have found a lib but find can still land one
			if [ -z $possiblea ] || [ -z $possibleso ]; then
				pyroot=${i%/*}
				extralib=`find $pyroot | grep "libpython"$pyv`
				for t in $extralib; do
					if echo "$t" | grep -q "$pyv.a"; then
						possiblea=$t
					elif echo "$t" | grep -q "$pyv.so"; then
						possibleso=$t
					fi
				done
			fi

			if [[ "$possiblea" ]] || [[ "$possibleso" ]]; then
				for h in $whereispy; do
					if echo "$h" | grep "/include" | grep "$pyv" | grep -q -v '_d'; then
						if [[ "$possiblea" ]]; then 
							#found what we were looking for, make the file and quit
							pythonver=$pyv
							pythonpath=$i
							hpath=$h
							apath=$possiblea
							sopath=$possibleso
							break
						elif [[ "$pyv" > "$pythonver" ]]; then
							pythonver=$pyv
							pythonpath=$i
							hpath=$h
							apath=$possiblea
							sopath=$possibleso		
						fi
					fi
				done
			fi
		fi
	fi
done

failed="1"
if [[ "$apath" ]]; then
	failed=""
	echo 1>&2
	echo 1>&2 "found matching .a lib and include folder =)"
	echo "PYTHON_INCLUDE=$hpath
PYTHON_LIB=$apath
PYVER=python$pythonver" > ./pypaths.txt
elif [[ "$sopath" ]]; then
	echo
	while [ 1 ]; do	
		# Send stdout to stderr to make text visible from a Makefile.
		echo -n 1>&2 "Couldn't find static libpython (.a). Found the .so instead. Would you like to build with it? [y/n]"
		read ans
		if [ "$ans" == "n" ]; then
			break;
		elif [ "$ans" == "y" ]; then
			failed=""
			echo "PYTHON_INCLUDE=$hpath
PYTHON_LIB=$sopath
PYVER=python$pythonver" > ./pypaths.txt			
			break;
		fi
	done
fi

if [[ $failed == "1" ]]; then
echo "PYTHON_INCLUDE=
PYTHON_LIB=
PYVER=" > ./pypaths.txt

echo 1>&2
echo 1>&2 "Couldn't find matching versions of python and libpython ='("
echo 1>&2 "At this point the configure file will abort. To make Armory, you need to manually enter your python paths in ./pypaths.txt:"
echo 1>&2
echo 1>&2 "	'PYTHON_INCLUDE' is the path to the include python folder"
echo 1>&2 "	'PYTHON_LIB' is the path to the matching libpython .a or .so file"
echo 1>&2 "	'PYVER' is the the python version used (i.e. python2.6 or python2.7)"
echo 1>&2
echo 1>&2 "Once you have filled these, run make from the cppForSwig folder"
echo 1>&2 "Aborting build"
echo 1>&2
exit
fi
