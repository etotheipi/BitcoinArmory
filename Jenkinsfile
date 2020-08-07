// https://github.com/Rudd-O/shared-jenkins-libraries
@Library('shared-jenkins-libraries@master') _

def test_step() {
    return {
        println "Tests have been skipped."
    }
}


genericFedoraRPMPipeline(
	null,
	{
		sh 'cd src && ./autogen.sh && PYTHON=/usr/bin/python2 ./configure --prefix=/usr && make srpm'
	},
	['autoconf', 'automake', 'libtool', 'gcc-c++', 'swig', 'python2-devel', 'python2-psutil', 'python3-PyQt4-devel', 'qt-devel'],
	null,
	test_step()
)
