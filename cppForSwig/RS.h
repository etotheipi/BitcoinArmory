#ifndef RSPP
#define RSPP

#include <stdint.h>
#include <stdlib.h>
#include "AtomicInt32.h"

struct
{
   int symsize;
   int genpoly;
   int nroots;
   int packet_size; //(1 << symsize) -1 -nroots
} param_list[]
{
   {4, 0x13, 2, 13},
   {5, 0x25, 4, 27},
   {6, 0x43, 8, 55},
   {7, 0x89, 16, 111},
   {8, 0x187, 16, 239},
   {9, 0x211, 16, 495},
   {10, 0x409, 16, 1007}
};

class rs_params
{
	public:
		int 		mm;
		int 		nn;
		uint16_t	*alpha_to;
		uint16_t	*index_of;
		uint16_t	*genpoly;
		int 		nroots;
		int 		fcr;
		int 		prim;
		int 		iprim;
		int		gfpoly;
		int		(*gffunc)(int);
      int packet_size;

		int init;

		rs_params() 
		{
			init=0;

			alpha_to = 0;
			index_of = 0;
			genpoly = 0;
		}

		~rs_params()
		{
			if(alpha_to) free(alpha_to);
			if(index_of) free(index_of);
			if(genpoly)  free(genpoly);
		}

		void set_params(int Symsize, int Gfpoly, int(*Gffunc)(int), int Fcr, int Prim, int Nroots);
		int operator==(rs_params &rhs);
		int rs_modnn(int x);
		int rs_init();
};

class rs_control
{
	public:
		//This class builds the static RS parameters
		rs_params **rsp;
		int n_params;

		AtomicInt32 ai_init, ai_add;

		rs_params *rs_16; //(8, 0x187, 0, 0, 1, 16)

		rs_control()
		{
			rsp = (rs_params**)malloc(sizeof(rs_params*));

			rsp[0] = init(8, 0x187, 0, 0, 1, 16);
			rs_16 = rsp[0];
			n_params = 1;

			ai_init=0;
			ai_add=0;
		}

		~rs_control()
		{
			if(!rsp) return;
			for(int i=0; i<n_params; i++)
				delete rsp[i];
			free(rsp);
		}

		int add_params(rs_params *rsp_in);
		rs_params* init(int symsize, int gfpoly, int (*gffunc)(int), int fcr, int prim, int nroots);
		rs_params* init(rs_params *rsp_in);
};

class RS
{
	private:
      static rs_control rsc; //holds the static RS parameters
		rs_params *rscp;

      AtomicInt32 encode_flag;

      int *blocks;
      int nblocks;
      int data_len;
		
      void SetParams(rs_params *rsp_in);
      void PrepareData(int len);
      void CleanUp();
		
      int Encode(rs_params *rs, uint8_t *data, int len, uint16_t *par, 
                 uint16_t invmsk);
		int Decode(rs_params *rs, uint8_t *data, uint16_t *par, int len,
			   uint16_t *s, int no_eras, int *eras_pos, uint16_t invmsk,
			   uint16_t *corr);

	public:
      static void* (*rs_alloc)(size_t size);
      static void (*rs_free)(void* buffer);
		
      uint16_t *par;
		int par_len;

		RS() //constructor, defaults to (8, 0x187, 0, 0, 1, 16)
		{
			par = 0;
         blocks = 0;
         data_len = 0;
			SetParams(rsc.rs_16);
         encode_flag = 0;
		}

		RS(int parity_len)
		{
			par = 0;
         blocks = 0;
			SetParams(8, 0x187, 0, 0, 1, parity_len);
		}

		~RS()
		{
         CleanUp();
		}

		void SetParams(int Symsize, int Gfpoly, int(*Gffunc)(int), int Fcr, int Prim, int Nroots);
      void SetParity(uint16_t *parity, int data_length);
		int Encode(const void *data, int len_in_bytes);
		int Decode(uint8_t *data, int len_in_bytes);
      void WipeAndClean();
      
      uint16_t* GetParity() const
         {return par;}
};

#endif
