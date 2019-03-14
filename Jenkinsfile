// https://github.com/Rudd-O/shared-jenkins-libraries
@Library('shared-jenkins-libraries@master') _


genericFedoraRPMPipeline(null, {
	sh 'cd src && ./autogen.sh && ./configure --prefix=/usr && make srpm'
})
