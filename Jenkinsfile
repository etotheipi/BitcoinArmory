// https://github.com/Rudd-O/shared-jenkins-libraries
@Library('shared-jenkins-libraries@master') _


def makesrpm() {
	return {
		sh 'make srpm'
	}
}

genericFedoraRPMPipeline(null, makesrpm)
