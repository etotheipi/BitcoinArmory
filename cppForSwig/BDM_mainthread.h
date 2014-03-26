#include "BlockUtils.h"
#include "pthread.h"

class BDM_CallBack
{
   public:
      virtual ~BDM_CallBack() {};
      virtual void run(int action, int arg) {};
};

class Caller {
private:
	static BDM_CallBack* _callback;
public:
	Caller() {}
	~Caller() { delCallback(); }
	void delCallback() { delete _callback; _callback = 0; }
	void setCallback(BDM_CallBack *cb) { delCallback(); _callback = cb; }
	void call(int action, int arg) { if (_callback) _callback->run(action, arg); }
};

void startBDM(int mode);
