#include "RS.h"
#include "CustomAlloc.h"

void rs_params::set_params(int Mm, int Gfpoly, int(*Gffunc)(int), int Fcr, int Prim, int Nroots)
{
	mm = Mm;
	gfpoly = Gfpoly;
	gffunc = Gffunc;
	fcr = Fcr;
	prim = Prim;
	nroots = Nroots;
	init = 1;
}

int rs_params::operator==(rs_params &rhs)
{
	if(!init) return 0;
		
	if(this->mm      != rhs.mm) return 0;
	if(this->gfpoly  != rhs.gfpoly)  return 0;
	if(this->gffunc  != rhs.gffunc)  return 0;
	if(this->fcr     != rhs.fcr)     return 0;
	if(this->prim    != rhs.prim)    return 0;
	if(this->nroots  != rhs.nroots)  return 0;

	return 1;
}

int rs_params::rs_modnn(int x)
{
	while (x >= nn) 
	{
		x -= nn;
		x = (x >> mm) + (x & nn);
	}
	return x;
}

int rs_params::rs_init()
{
	int i, j, sr, root, iprim;

	nn = (1 << mm) - 1;

	/* Allocate the arrays */
	alpha_to = (uint16_t*)malloc(sizeof(uint16_t) * (nn + 1));
	if (alpha_to == NULL) return -1;

	index_of = (uint16_t*)malloc(sizeof(uint16_t) * (nn + 1));
	if (index_of == NULL) return -1;

	genpoly = (uint16_t*)malloc(sizeof(uint16_t) * (nroots + 1));
	if(genpoly == NULL) return -1;
	
	/* Generate Galois field lookup tables */
	index_of[0] = nn;	/* log(zero) = -inf */
	alpha_to[nn] = 0;	/* alpha**-inf = 0 */
	if (gfpoly) 
	{
		sr = 1;
		for (i = 0; i < nn; i++) 
		{
			index_of[sr] = i;
			alpha_to[i] = sr;
			sr <<= 1;
			if (sr & (1 << mm))
				sr ^= gfpoly;
			sr &= nn;
		}
	} 
	else 
	{
		sr = gffunc(0);
		for (i = 0; i < nn; i++)
		{
			index_of[sr] = i;
			alpha_to[i] = sr;
			sr = gffunc(sr);
		}
	}
	/* If it's not primitive, exit */
	if(sr != alpha_to[0]) return -1;

	/* Find prim-th root of 1, used in decoding */
	for(iprim = 1; (iprim % prim) != 0; iprim += nn);
	/* prim-th root of 1, index form */
	this->iprim = iprim / prim;

	/* Form RS code generator polynomial from its roots */
	genpoly[0] = 1;
	for (i = 0, root = fcr * prim; i < nroots; i++, root += prim) 
	{
		genpoly[i + 1] = 1;
		/* Multiply rs->genpoly[] by  @**(root + x) */
		for (j = i; j > 0; j--) 
		{
			if (genpoly[j] != 0) 
			{
				genpoly[j] = genpoly[j -1] ^
				alpha_to[rs_modnn(index_of[genpoly[j]] + root)];
			} 
			else genpoly[j] = genpoly[j - 1];
		}
		/* rs->genpoly[0] can never be zero */
		genpoly[0] = alpha_to[rs_modnn(index_of[genpoly[0]] + root)];
	}
	/* convert rs->genpoly[] to index form for quicker encoding */
	for (i = 0; i <= nroots; i++)
		genpoly[i] = index_of[genpoly[i]];

	return 0;
}


int rs_control::add_params(rs_params *rsp_in)
{
	if(!ai_add.CompareExchange(1, 0))
	{
		while(ai_init!=0)
			Sleep(1);

		rsp = (rs_params**)realloc(rsp, sizeof(rs_params*)*(n_params+1));
				
		rsp[n_params] = rsp_in;
		int rt = n_params;
		n_params++;
		ai_add = 0;
		return rt;
	}

	init(rsp_in);
	return -1;
}

rs_params* rs_control::init(int symsize, int gfpoly, int (*gffunc)(int), int fcr, int prim, int nroots)
{
	rs_params *rsp_c = new rs_params;
	rsp_c->set_params(symsize, gfpoly, gffunc, fcr, prim, nroots);

	return init(rsp_c);
}

rs_params* rs_control::init(rs_params *rsp_c)
{
	while(ai_add!=0)
		Sleep(1);
	
	ai_init++;

	int i=0;
	for(i; i<n_params; i++)
	{
		if(*rsp[i]==*rsp_c)
		{
			delete rsp_c;
			ai_init--;
			return rsp[i];
		}
	}
	ai_init--;

	//build params
	add_params(rsp_c);
	rsp_c->rs_init();
	
	return rsp_c;
}

rs_control RS::rsc;

void *(*RS::rs_alloc)(size_t) = CustomAlloc::CAllocStatic::alloc_;
void  (*RS::rs_free) (void*)  = CustomAlloc::CAllocStatic::free_;

void RS::CleanUp()
{
   if(par) rs_free(par);
   if(blocks) free(blocks);

   par=0;
   blocks=0;

   nblocks=0;
   data_len=0;
   par_len=0;
}

void RS::WipeAndClean()
{
   if(par_len) memset(par, 0, par_len*sizeof(uint16_t));
   CleanUp();
}

void RS::SetParams(int Symsize, int Gfpoly, int(*Gffunc)(int), int Fcr, int Prim, int Nroots)
{
	SetParams(rsc.init(Symsize, Gfpoly, Gffunc, Fcr, Prim, Nroots));
}

void RS::SetParams(rs_params *rsp_in)
{
   CleanUp();
	rscp = rsp_in;
}

void RS::PrepareData(int len)
{
   CleanUp();

   if(len)
   {
      nblocks = len / 223;
      if(len %223) nblocks++;
   
      int blocksize = len / nblocks;
      if(len % nblocks) blocksize++;

      data_len = len;
      par_len = nblocks*rscp->nroots;

      blocks = (int*)malloc(sizeof(int)*nblocks);
      par = (uint16_t*)rs_alloc(sizeof(uint16_t)*par_len);

      for(int i=0; i<nblocks; i++)
      {
         blocks[i] = (blocksize < len ? blocksize : len);
         len -= blocksize;
      }
      memset(par, 0, sizeof(uint16_t)*par_len);
   }
}

void RS::SetParity(uint16_t *parity, int data_length)
{
   PrepareData(data_length);
   memcpy(par, parity, sizeof(uint16_t)*par_len);
}

int RS::Encode(const void *data, int len_in_bytes)
{
   while(encode_flag.Fetch_Or(1));

   int rt = 0, i = 0, count;   
   if(data_len != len_in_bytes) PrepareData(len_in_bytes);
   else memset(par, 0, par_len*sizeof(uint16_t));

   count = 0;
   for(i; i<nblocks; i++)
   {
	   rt += Encode(rscp, (uint8_t*)data +count, blocks[i], par +rscp->nroots*i, 0);
      count += blocks[i];
   }

   encode_flag = 0;
   return rt;
}

int RS::Encode(rs_params *rs, uint8_t *data, int len, uint16_t *par, uint16_t invmsk)
{
	int i, j, pad;
	int nn = rs->nn;
	int nroots = rs->nroots;
	uint16_t *alpha_to = rs->alpha_to;
	uint16_t *index_of = rs->index_of;
	uint16_t *genpoly = rs->genpoly;
	uint16_t fb;
	uint16_t msk = (uint16_t) rs->nn;

	/* Check length parameter for validity */
	pad = nn - nroots - len;
	if (pad < 0 || pad >= nn)
		return -1;

	for (i = 0; i < len; i++) 
	{
		fb = index_of[((((uint16_t) data[i])^invmsk) & msk) ^ par[0]];
		/* feedback term is non-zero */
		if (fb != nn) 
		{
			for (j = 1; j < nroots; j++)
				par[j] ^= alpha_to[rs->rs_modnn(fb +genpoly[nroots - j])];
		}
		/* Shift */
		memmove(&par[0], &par[1], sizeof(uint16_t) * (nroots - 1));
			
		if (fb != nn) par[nroots - 1] = alpha_to[rs->rs_modnn(fb +genpoly[0])];
		else par[nroots - 1] = 0;
	}
	return 0;
}

int RS::Decode(uint8_t *data, int len_in_bytes)
{
   while(encode_flag!=0);

   if(data_len != len_in_bytes) return -1;
   int rt=0, i=0, count=0, vrt, err=0;

   for(i; i<nblocks; i++)
   {
      vrt = Decode(rscp, data +count, par+ rscp->nroots*i, blocks[i], 0, 0, 0, 0, 0);
      
      if(vrt>-1) rt+=vrt;
      else err--;

      count += blocks[i];
   }
   
   if(err) return err;
   return rt;
}

int RS::Decode(rs_params *rs, uint8_t *data, uint16_t *par, int len,
	       uint16_t *s, int no_eras, int *eras_pos, uint16_t invmsk,
	       uint16_t *corr)
{
	int deg_lambda, el, deg_omega;
	int i, j, r, k, pad;
	int nn = rs->nn;
	const int nroots = rs->nroots;
	int fcr = rs->fcr;
	int prim = rs->prim;
	int iprim = rs->iprim;
	uint16_t *alpha_to = rs->alpha_to;
	uint16_t *index_of = rs->index_of;
	uint16_t u, q, tmp, num1, num2, den, discr_r, syn_error;
	/* Err+Eras Locator poly and syndrome poly The maximum value
	 * of nroots is 8. So the necessary stack size will be about
	 * 220 bytes max.
	 */
	uint16_t *lambda = new uint16_t[nroots + 1];
	uint16_t *syn = new uint16_t[nroots];
	uint16_t *b = new uint16_t[nroots + 1];
	uint16_t *t = new uint16_t[nroots + 1];
	uint16_t *omega = new uint16_t[nroots + 1];
	uint16_t *root = new uint16_t[nroots];
	uint16_t *reg = new uint16_t[nroots + 1];
	uint16_t *loc = new uint16_t[nroots];

	int count = 0;
	uint16_t msk = (uint16_t) rs->nn;

	/* Check length parameter for validity */
	pad = nn - nroots - len;
	if(pad < 0 || pad >= nn) return -1;

	/* Does the caller provide the syndrome ? */
	if (s != NULL)
		goto decode;

	/* form the syndromes; i.e., evaluate data(x) at roots of
	 * g(x) */
	for (i = 0; i < nroots; i++)
		syn[i] = (((uint16_t) data[0]) ^ invmsk) & msk;
	
	for (j = 1; j < len; j++) 
	{
		for (i = 0; i < nroots; i++) 
		{
			if (syn[i] == 0) syn[i] = (((uint16_t) data[j]) ^ invmsk) & msk;
			else syn[i] = ((((uint16_t) data[j]) ^ invmsk) & msk) ^ alpha_to[rs->rs_modnn(index_of[syn[i]] + (fcr + i) * prim)];
		}
	}

	for (j = 0; j < nroots; j++) 
	{
		for (i = 0; i < nroots; i++) 
		{
			if (syn[i] == 0) syn[i] = ((uint16_t) par[j]) & msk;
			else syn[i] = (((uint16_t) par[j]) & msk) ^ alpha_to[rs->rs_modnn(index_of[syn[i]] + (fcr+i)*prim)];
		}
	}
	s = syn;

	/* Convert syndromes to index form, checking for nonzero condition */
	syn_error = 0;
	for (i = 0; i < nroots; i++) 
	{
		syn_error |= s[i];
		s[i] = index_of[s[i]];
	}

		
	if (!syn_error) 
	{
		/* if syndrome is zero, data[] is a codeword and there are no
		 * errors to correct. So return data[] unmodified
		 */
		count = 0;
		goto finish;
	}

	 decode:
		memset(&lambda[1], 0, nroots * sizeof(lambda[0]));
		lambda[0] = 1;

		if (no_eras > 0) 
		{
			/* Init lambda to be the erasure locator polynomial */
			lambda[1] = alpha_to[rs->rs_modnn(prim * (nn - 1 - eras_pos[0]))];
			for (i = 1; i < no_eras; i++) 
			{
				u = rs->rs_modnn(prim * (nn - 1 - eras_pos[i]));
				for (j = i + 1; j > 0; j--) 
				{
					tmp = index_of[lambda[j - 1]];
					if (tmp != nn) lambda[j] ^= alpha_to[rs->rs_modnn(u + tmp)];
				}
			}
		}

		for (i = 0; i < nroots + 1; i++)
			b[i] = index_of[lambda[i]];

		/*
		 * Begin Berlekamp-Massey algorithm to determine error+erasure
		 * locator polynomial
		 */
		r = no_eras;
		el = no_eras;
		while (++r <= nroots) 
		{	
			/* r is the step number */
			/* Compute discrepancy at the r-th step in poly-form */
			discr_r = 0;
			for (i = 0; i < r; i++) 
			{
				if ((lambda[i] != 0) && (s[r - i - 1] != nn)) 
					discr_r ^= alpha_to[rs->rs_modnn(index_of[lambda[i]] +s[r - i - 1])];
			}
			
			discr_r = index_of[discr_r];	/* Index form */
			if (discr_r == nn) 
			{
				/* 2 lines below: B(x) <-- x*B(x) */
				memmove (&b[1], b, nroots * sizeof (b[0]));
				b[0] = nn;
			} 
			else 
			{
				/* 7 lines below: T(x) <-- lambda(x)-discr_r*x*b(x) */
				t[0] = lambda[0];
				for (i = 0; i < nroots; i++) 
				{
					if (b[i] != nn) t[i + 1] = lambda[i + 1] ^alpha_to[rs->rs_modnn(discr_r +b[i])];
					else t[i + 1] = lambda[i + 1];
				}
				if (2 * el <= r + no_eras - 1) 
				{
					el = r + no_eras - el;
					/*
					 * 2 lines below: B(x) <-- inv(discr_r) *
					 * lambda(x)
					 */
					for (i = 0; i <= nroots; i++) 
						b[i] = (lambda[i] == 0) ? nn : rs->rs_modnn(index_of[lambda[i]] - discr_r + nn);
				} 
				else 
				{
					/* 2 lines below: B(x) <-- x*B(x) */
					memmove(&b[1], b, nroots * sizeof(b[0]));
					b[0] = nn;
				}
				memcpy(lambda, t, (nroots + 1) * sizeof(t[0]));
			}
		}

		/* Convert lambda to index form and compute deg(lambda(x)) */
		deg_lambda = 0;
		for (i = 0; i < nroots + 1; i++) 
		{
			lambda[i] = index_of[lambda[i]];
			if (lambda[i] != nn)
				deg_lambda = i;
		}
		/* Find roots of error+erasure locator polynomial by Chien search */
		memcpy(&reg[1], &lambda[1], nroots * sizeof(reg[0]));
		count = 0;		/* Number of roots of lambda(x) */
		for (i = 1, k = iprim - 1; i <= nn; i++, k = rs->rs_modnn(k + iprim)) 
		{
			q = 1;		/* lambda[0] is always 0 */
			for (j = deg_lambda; j > 0; j--) 
			{
				if (reg[j] != nn) 
				{
					reg[j] = rs->rs_modnn(reg[j] + j);
					q ^= alpha_to[reg[j]];
				}
			}
			if (q != 0)
				continue;	/* Not a root */
			/* store root (index-form) and error location number */
			root[count] = i;
			loc[count] = k;
			/* If we've already found max possible roots,
			 * abort the search to save time
			 */
			if (++count == deg_lambda)
				break;
		}
		if (deg_lambda != count) 
		{
			/*
			 * deg(lambda) unequal to number of roots => uncorrectable
			 * error detected
			 */
			count = -74; // -EBADMSG
			/* count = -EBADMSG; */
			goto finish;
		}
		/*
		 * Compute err+eras evaluator poly omega(x) = s(x)*lambda(x) (modulo
		 * x**nroots). in index form. Also find deg(omega).
		 */
		deg_omega = deg_lambda - 1;
		for (i = 0; i <= deg_omega; i++) 
		{
			tmp = 0;
			for (j = i; j >= 0; j--) 
			{
				if ((s[i - j] != nn) && (lambda[j] != nn))
					tmp ^= alpha_to[rs->rs_modnn(s[i - j] + lambda[j])];
			}
			omega[i] = index_of[tmp];
		}

		/*
		 * Compute error values in poly-form. num1 = omega(inv(X(l))), num2 =
		 * inv(X(l))**(fcr-1) and den = lambda_pr(inv(X(l))) all in poly-form
		 */
		for (j = count - 1; j >= 0; j--) 
		{
			num1 = 0;
			for (i = deg_omega; i >= 0; i--) 
			{
				if (omega[i] != nn)
					num1 ^= alpha_to[rs->rs_modnn(omega[i] +i * root[j])];
			}
			num2 = alpha_to[rs->rs_modnn(root[j] * (fcr - 1) + nn)];
			den = 0;

			/* lambda[i+1] for i even is the formal derivative
			 * lambda_pr of lambda[i] */
			/* for (i = min(deg_lambda, nroots - 1) & ~1; i >= 0; i -= 2) { */
			for (i = ((deg_lambda <= nroots - 1) ? deg_lambda : nroots - 1) & ~1; i >= 0; i -= 2) 
			{
				if (lambda[i + 1] != nn) 
					den ^= alpha_to[rs->rs_modnn(lambda[i + 1] +i * root[j])];
			}
			/* Apply error to data */
			if (num1 != 0 && loc[j] >= pad) 
			{
				uint16_t cor = alpha_to[rs->rs_modnn(index_of[num1] +index_of[num2] +nn - index_of[den])];
				/* Store the error correction pattern, if a
				 * correction buffer is available */
				if (corr) corr[j] = cor;
				else
				{
					/* If a data buffer is given and the
					 * error is inside the message,
					 * correct it */
					if (data && (loc[j] < (nn - nroots))) data[loc[j] - pad] ^= cor;
				}
			}
		}

	finish:
		if (eras_pos != NULL) 
		{
			for (i = 0; i < count; i++)
				eras_pos[i] = loc[i] - pad;
		}

		delete [] lambda;
		delete [] syn;
		delete [] b;
		delete [] t;
		delete [] omega;
		delete [] root;
		delete [] reg;
		delete [] loc;

		return count;
	}
