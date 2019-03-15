// https://github.com/Rudd-O/shared-jenkins-libraries
@Library('shared-jenkins-libraries@master') _


genericFedoraRPMPipeline(
	null,
	{
		sh 'cd src && ./autogen.sh && PYTHON=/usr/bin/python2 ./configure --prefix=/usr && make srpm'
	},
	['autoconf', 'automake', 'libtool', 'gcc-c++', 'swig', 'python2-psutil', 'PyQt4-devel'],
)
