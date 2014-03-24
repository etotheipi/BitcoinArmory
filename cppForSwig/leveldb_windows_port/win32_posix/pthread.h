/***
Minimal pthread port for leveldb purpose
Cancelation isn't supported
***/

#ifndef PTHREADS
#define PTHREADS

#include <Windows.h>
#include <intrin.h>

#ifdef DeleteFile
#undef DeleteFile
#endif


#pragma intrinsic(_ReadWriteBarrier)

typedef CRITICAL_SECTION pthread_mutex_t;
typedef DWORD pthread_t;
typedef int pthread_attr_t;
#ifdef USE_CONDVAR
	typedef CONDITION_VARIABLE pthread_cond_t;
#else
	struct pthread_cond_t_
	{
		volatile long Broadcast;
		volatile long resetEvent;
		HANDLE mu;
		HANDLE EV;
	};

	typedef struct pthread_cond_t_ * pthread_cond_t;

#endif
typedef int * pthread_condattr_t;

#define PTHREAD_ONCE_INIT 0
typedef volatile long pthread_once_t;

int pthread_mutex_init(pthread_mutex_t *mu, const int mutex_attr);
int pthread_mutex_lock(pthread_mutex_t *mu);
int pthread_mutex_unlock(pthread_mutex_t *mu);
int pthread_mutex_destroy(pthread_mutex_t *mu);

int pthread_create(pthread_t *tid, pthread_attr_t *attr, void*(*start)(void*), void *arg);

int pthread_cond_init(pthread_cond_t *cond, const pthread_condattr_t *attr);
int pthread_cond_signal(pthread_cond_t *cond);
int pthread_cond_broadcast(pthread_cond_t *cond);
int pthread_cond_wait(pthread_cond_t *cond, pthread_mutex_t *mu);
int pthread_cond_destroy(pthread_cond_t *cond);

DWORD pthread_self();

int pthread_once(pthread_once_t *once, void (*func)(void));

#endif
