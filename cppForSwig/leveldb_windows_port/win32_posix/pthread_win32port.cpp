////////////////////////////////////////////////////////////////////////////////
//                                                                            //
//  Copyright (C) 2011-2015, Armory Technologies, Inc.                        //
//  Distributed under the GNU Affero General Public License (AGPL v3)         //
//  See LICENSE-ATI or http://www.gnu.org/licenses/agpl.html                  //
//                                                                            //
////////////////////////////////////////////////////////////////////////////////

#include "pthread.h"

int pthread_mutex_init(pthread_mutex_t *mu, const int mutex_attr)
{
	InitializeCriticalSection(mu);

	return 0;
}

pthread_t pthread_self()
{
	return (void*)GetCurrentThreadId();
}

int pthread_mutex_lock(pthread_mutex_t *mu)
{
	EnterCriticalSection(mu);

	return 0;
}

int pthread_mutex_unlock(pthread_mutex_t *mu)
{
	LeaveCriticalSection(mu);

	return 0;
}

int pthread_mutex_destroy(pthread_mutex_t *mu)
{
	DeleteCriticalSection(mu);

	return 0;
}

int pthread_create(pthread_t *tid, pthread_attr_t *attr, void*(*start)(void*), void *arg)
{
	if(*tid = (pthread_t)CreateThread(NULL, NULL, (LPTHREAD_START_ROUTINE)start, arg, 0, 0)) return 0;

	return -1;
}

int pthread_cancel(pthread_t tid)
{
   return (!TerminateThread(tid, 0));
}

int pthread_join(pthread_t tid, void **value_ptr)
{
   WaitForSingleObject(tid, INFINITE);
   CloseHandle(tid);
   return 0;
}

int pthread_detach(pthread_t tid)
{
   return !CloseHandle(tid);
}


#ifdef USE_CONDVAR
int pthread_cond_init(pthread_cond_t *cond, const pthread_condattr_t *attr)
{
	InitializeConditionVariable(cond);

	return 0;
}

int pthread_cond_signal(pthread_cond_t *cond)
{
	WakeConditionVariable(cond);
	
	return 0;
}

int pthread_cond_broadcast(pthread_cond_t *cond)
{
	WakeAllConditionVariable(cond);
	
	return 0;
}

int pthread_cond_wait(pthread_cond_t *cond, pthread_mutex_t *mu)
{
	SleepConditionVariableCS(cond, mu, INFINITE);
	return 0;
}

int pthread_cond_timedwait(pthread_cond_t * cond, pthread_mutex_t *mutex, const ULONGLONG *tickcount64)
{
   const ULONGLONG now = GetTickCount64();
	
	if(now > *tickcount64)
		return 0;
	
   ULONGLONG diff = *tickcount64 - now;

   SleepConditionVariableCS(cond, mutex, (DWORD)diff);
	return 0;
}

int pthread_cond_destroy(pthread_cond_t *cond)
{
	return 0;
}


#else //in case it has to run on WinXP, condition variables aren't supported, have to implement them with oldschool WinAPI calls.
int pthread_cond_init(pthread_cond_t *cond, const pthread_condattr_t *attr)
{ 
	(*cond) = (pthread_cond_t_*)malloc(sizeof(pthread_cond_t_));

	(*cond)->Broadcast = 0;
	(*cond)->resetEvent = 0;
	(*cond)->mu = 0;
	(*cond)->EV = CreateEvent(NULL, 0, 0, NULL);
	
	return 0;
}

int pthread_cond_signal(pthread_cond_t *cond)
{
	SetEvent((*cond)->EV);
	return 0;
}

int pthread_cond_broadcast(pthread_cond_t *cond)
{
	_InterlockedExchange(&(*cond)->Broadcast, 1);
	SetEvent((*cond)->EV);
	
	return 0;
}

int pthread_cond_wait(pthread_cond_t *cond, pthread_mutex_t *mu)
{
	LeaveCriticalSection(mu);
	
	WaitForSingleObject((*cond)->EV, INFINITE);
	
	EnterCriticalSection(mu);
		
	if((*cond)->Broadcast)
			SetEvent((*cond)->EV);

	return 0;
}

int pthread_cond_timedwait(pthread_cond_t * cond, pthread_mutex_t *mutex, const ULONGLONG *tickcount64)
{
	LeaveCriticalSection(mutex);
	
	const ULONGLONG now = GetTickCount64();
	
	ULONGLONG diff = *tickcount64-now;
	if (diff > now)
		diff = 0;
	
	WaitForSingleObject((*cond)->EV, (DWORD)diff);
	
	EnterCriticalSection(mutex);
		
	if((*cond)->Broadcast)
			SetEvent((*cond)->EV);

	return 0;

}

int pthread_cond_destroy(pthread_cond_t *cond)
{
	CloseHandle((*cond)->EV);
	free(*cond);
	*cond = 0;
	return 0;
}
#endif

int pthread_once(pthread_once_t *once, void (*func)(void))
{
	while(*once!=1)
	{
		if(!InterlockedCompareExchange(once, 2, 0))
		{
			if(*once==2) func(); //consume once to prevent reordering
			*once=1;
			return 0;
		}
	}
	
	return 0;
}