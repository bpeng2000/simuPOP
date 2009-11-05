/***************************************************************************
 *   Copyright (C) 2004 by Bo Peng                                         *
 *   bpeng@rice.edu                                                        *
 *                                                                         *
 *   $LastChangedDate$
 *   $Rev$
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 *   This program is distributed in the hope that it will be useful,       *
 *   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
 *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
 *   GNU General Public License for more details.                          *
 *                                                                         *
 *   You should have received a copy of the GNU General Public License     *
 *   along with this program; if not, write to the                         *
 *   Free Software Foundation, Inc.,                                       *
 *   59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.             *
 ***************************************************************************/

#ifndef _INITIALIZER_H
#define _INITIALIZER_H
/**
\file
\brief head file of class initializer:public Operator
*/
#include "utility.h"
#include "operator.h"

#include <numeric>
using std::string;
using std::accumulate;

namespace simuPOP
{

	/// initialize alleles at the start of generation
	class initializer: public Operator
	{
		public:
			/// create an initializer. default to be always active
            /**
            Initializers are used to initialize populations before evolution.
            They are set to be \c PreMating operators by default. simuPOP provides
            three initializers, one assigns alleles by random, one assigns a fixed
            set of genotype, and the last one calls a user-defined function.
            */
			initializer( const vectoru& subPop=vectoru(),
				intMatrix indRange=intMatrix(),
				const vectoru& loci = vectoru(),
				int atPloidy = -1,
				double maleFreq=0.5, const vectori& sex = vectori(),
				int stage=PreMating, int begin=0, int end=-1, int step=1,
				vectorl at=vectorl(), int rep=REP_ALL, int grp=GRP_ALL, const vectorstr& infoFields=vectorstr())
				:Operator("","", stage, begin, end, step, at, rep, grp, infoFields),
				m_subPop(subPop), m_indRange(indRange),
				m_atLoci(loci), m_atPloidy(atPloidy),
				m_maleFreq(maleFreq), m_sex(sex)
			{
				for(size_t i = 0; i < m_indRange.size(); ++i)
				{
					// allow for singleton
					if( m_indRange[i].size() == 1)
						m_indRange[i].push_back( m_indRange[i][0]+1);

					if( m_indRange[i].size() != 2 || m_indRange[i][0] > m_indRange[i][1] )
						throw ValueError("Expecting a range.");
				}
				// no flags to set.
			}

			/// destructor
			virtual ~initializer()
			{
			}

			/// deep copy of an initializer
			virtual Operator* clone() const
			{
				return new initializer(*this);
			}

            /// used by Python print function to print out the general information of the initializer
			virtual string __repr__()
			{
				return "<simuPOP::initializer>";
			}

            /// set the range of a population \c pop???
			void setRanges(population& pop);

            /// ???
			void initSexIter()
			{
				if(! m_sex.empty())
					m_sexItr = m_sex.begin();
			}

            /// ???
			Sex nextSex();

		protected:

			/// applicable subpop
			vectoru m_subPop;

			/// ranges
			intMatrix m_indRange;

			/// init loci
			vectoru m_atLoci;

			/// at which ploidy, -1 means all
			int m_atPloidy;

			/// sex frequency
			double m_maleFreq;

			/// specify sex
			vectori m_sex;

			/// iterator to sex
			vectori::iterator m_sexItr;

			/// populaiton specific range
			intMatrix m_ranges;

	};

	/// initialize genotypes by given allele frequencies, and sex by male frequency
	class initByFreq: public initializer
	{
		public:
            /// randomly assign alleles according to given allele frequencies
			/** 			
            This operator accepts \c alleleFreq or \c alleleFreqs.??? The first one
            ignores subpopulation structure while the second one gives different initial
            allele frequencies to different \c subpop or ranges. Allele frequencies can
            differ in \c subpop. Sex is also assigned randomly.

			\param alleleFreq an array of allele frequencies. The sum of all the frequencies
                must be 1; or for a matrix of allele frequencies, each row corresponses to
                a subpopulation.
			\param subPop an array specifies applicable subpopulations
			\param indRange a <tt>[begin, end]</tt> pair of the range of absolute indices
                of individuals, for example, <tt>([1,2])</tt>; or an array of <tt>[begin, end]</tt>
                pairs, such as <tt>([[1,4],[5,6]])</tt>. This is how you can initialize individuals
                differently within subpopulations. Note that ranges are in the form of [a,b).
                I.e., range [4,6] will intialize individual 4, 5, but not 6. As a shortcut for [4,5],
                you can use [4] to specify one individual.
			\param identicalInds whether or not make individual genotypies identical
                in all subpopulation. If \c True, this operator will randomly generate genotype for
                an individual and spread it to the whole subpopulation in the given range.
			\param loci a vector of locus indices at which initialization will be done. If empty, apply to all loci.
            \param locus a shortcut to \c loci
			\param atPloidy initialize which copy of chromosomes. Default to all.
			\param maleFreq male frequency. Default to \c 0.5. Sex will be initialized with this parameter.
			\param sex an array of sex <tt>[Male, Female, Male...]</tt> for individuals. The length of sex will not
                be checked. If it is shorter than the number of individuals, sex will be reused from the beginning.
			\param stage default to \c PreMating
			*/
			initByFreq( const matrix& alleleFreq=matrix(),
				bool identicalInds=false,  const vectoru& subPop=vectoru(),
				intMatrix indRange = intMatrix(),
				const vectoru& loci=vectoru(), int atPloidy=-1,
				double maleFreq=0.5, const vectori& sex = vectori(),
				int stage=PreMating, int begin=0, int end=1, int step=1, vectorl at=vectorl(),
				int rep=REP_ALL, int grp=GRP_ALL, const vectorstr& infoFields=vectorstr())
				: initializer(subPop, indRange, loci,
				atPloidy, maleFreq, sex,
				stage, begin, end, step, at, rep, grp, infoFields),
				m_alleleFreq(alleleFreq), m_identicalInds(identicalInds)
			{

				DBG_FAILIF(  m_alleleFreq.empty(),
					IndexError, "Should specify one of alleleFreq, alleleFreqs");

				for(size_t i=0; i< m_alleleFreq.size(); ++i)
					if( fcmp_ne(accumulate(m_alleleFreq[i].begin(), m_alleleFreq[i].end(), 0.), 1.0))
						throw ValueError("Allele frequencies should add up to one.");
			}

			~initByFreq()
			{
			}

			/// deep copy of the operator \c initByFreq
			virtual Operator* clone() const
			{
				return new initByFreq(*this);
			}

            /// used by Python print function to print out the general information of the operator \c initByFreq
			virtual string __repr__()
			{
				return "<simuPOP::initByFreq>";
			}

            /// apply operator \c initByFreq???
			bool apply(population& pop);

		private:

			/// allele frequencies (assume all loci are the same for a subPop
			matrix m_alleleFreq;

			///
			bool m_identicalInds;

	};

	/// initialize genotype by value and then copy to all individuals
	class initByValue: public initializer
	{
		public:
            /// initialize populations by given alleles
			/**
            \c initByValue operator gets one copy of chromosomes or the whole
            genotype (or of those corresponds to \c loci) of an individual
            and copy them to all or a subset of individuals.
			This operator assign given alleles to specified individuals. Every
            individual will have the same genotype.The parameter combinations should be
			\li <tt>value - subPop / indRange</tt>: individual in
            \c subPop or in range(s) will be assigned genotype 'value';
			\li <tt>subPop /indRange</tt>: \c subPop or \c indRange should have
            the same length as values. Each item of values will be assigned to
            each \c subPop or \c indRange.
            
			\param value an array of genotypes of one individual, having the same
                length as the length of <tt>loci()</tt> or <tt>loci()*ploidy()</tt>
                or <tt>pop.genoSize()</tt> (whole genotype) or <tt>totNumLoci()</tt>
                (one copy of chromosome). This parameter can also be an array of arrays
                of genotypes of one individual. Should have length one or equal to \c subpop
                or ranges or proportion. If value is an array of values, it should have
                the same length as \c subpop, \c indRange or \c proportions.
			\param loci a vector of loci indices. If empty, apply to all loci.
            \param locus a shortcut to \c loci
			\param atPloidy initialize which copy of chromosomes. Default to all.
			\param subPop an array of applicable subpopulations. If values are given,
                should have equal length to values.
 			\param indRange a <tt>[begin, end]</tt> pair of range of individuals; or
                an array of <tt>[begin, end]</tt> pairs.
			\param proportions an array of percentages for each item in values. If given,
                assign given genotypes randomly.
			\param maleFreq male frequency
			\param sex an array of sex <tt>[Male, Female, Male...]</tt> for individuals.
                The length of sex will not be checked. If length of sex is shorter than
                the number of individuals, sex will be reused from the beginning.
			\param stages default to \c PreMating
			*/
			initByValue( intMatrix value=intMatrix(),
				vectoru loci=vectoru(), int atPloidy=-1,
				vectoru subPop=vectoru(), intMatrix indRange=intMatrix(),
				const vectorf& proportions = vectorf(),
				double maleFreq=0.5, const vectori& sex = vectori(),
				int stage=PreMating, int begin=0, int end=1, int step=1, vectorl at=vectorl(),
				int rep=REP_ALL, int grp=GRP_ALL, const vectorstr& infoFields=vectorstr())
				: initializer(subPop, indRange, loci, atPloidy, maleFreq, sex,
				stage, begin, end, step, at, rep, grp, infoFields),
				m_value(value), m_proportion(proportions)
			{
				DBG_FAILIF( maleFreq < 0 || maleFreq > 1 ,
					IndexError, "male frequency in the population should be in the range of [0,1]");

				DBG_FAILIF( m_value.empty() , ValueError,
					"Please specify an array of alleles in the order of chrom_1...chrom_n for all copies of chromosomes");

				DBG_FAILIF( !m_proportion.empty() && m_proportion.size() != m_value.size(), ValueError,
					"If proportions are given, its length should match that of values.");

				DBG_FAILIF( !m_proportion.empty() && fcmp_ne(accumulate(m_proportion.begin(), m_proportion.end(), 0.0), 1),
					ValueError, "Proportion should add up to one.");
			}

			~initByValue(){}

			/// deep copy of the operator \c initByValue
			virtual Operator* clone() const
			{
				return new initByValue(*this);
			}

            /// used by Python print function to print out the general information of the operator \c initByValue
			virtual string __repr__()
			{
				return "<simuPOP::initByValue>";
			}

            /// apply operator \c initByValue???
			bool apply(population& pop);

		private:
			/// allele frequencies (assume all loci are the same
			intMatrix m_value;

			/// if assign randomly
			vectorf m_proportion;
	};

	/// initialize genotype by value and then copy to all individuals

	class spread:public Operator
	{
		public:
			/// copy genotypes of \c ind to all individuals in \c subPop
            /**
            The default value of \c subPop is the subpopulation where \c ind resides.
            */
			spread(ULONG ind, vectoru subPop=vectoru(),
				int stage=PreMating, int begin=0, int end=1, int step=1, vectorl at=vectorl(),
				int rep=REP_ALL, int grp=GRP_ALL, const vectorstr& infoFields=vectorstr())
				: Operator("","", stage, begin, end, step, at, rep, grp, infoFields),
				m_ind(ind), m_subPop(subPop)
			{
			}

			~spread(){}

			/// deep copy of the operator \c spread
			virtual Operator* clone() const
			{
				return new spread(*this);
			}

            /// used by Python print function to print out the general information of the operator \c spread
			virtual string __repr__()
			{
				return "<simuPOP::spread genotype>";
			}

            /// apply operator \c spread???
			bool apply(population& pop)
			{
				std::pair<UINT, ULONG> p = pop.subPopIndPair(m_ind);

				if(m_subPop.empty())
					m_subPop.resize(1, p.first);

				GenoIterator srcBegin = pop.indGenoBegin(m_ind),
					srcEnd=pop.indGenoEnd(m_ind);

				for(vectoru::iterator sp=m_subPop.begin(); sp != m_subPop.end(); ++sp)
				{
					for(ULONG i = pop.subPopBegin(*sp); i < pop.subPopEnd(*sp); ++i)
						if( i != m_ind)
							copy(srcBegin, srcEnd, pop.indGenoBegin(i));
				}

				return true;
			}

		private:
			ULONG m_ind;
			vectoru m_subPop;

	};

	class pyInit:public initializer
	{

        /// initialize populations using given user function        
		public:
			/**
			\c pyInit is a hybrid initializer. User should define a function with parameters
            allele, ploidy and subpop indices, and return an allele value. 
			Users of this operator must supply a Python function with parameter 
			<tt>(index, ploidy, subpop)</tt>.
			This operator will loop through all individual in each subpopulation and call this function
			to initialize populations. The arrange of parameters allows different initialization scheme for each subpop.

			\param func a Python function with parameter <tt>(index, ploidy, subpop)</tt>, where
                \li \c index is the allele index ranging from \c 0 to <tt>totNumLoci(-1)</tt>,
                \li \c ploidy is the index of the copy of chromosomes)
                \li \c subpop is the subpopulation index.

                The return value of this function should be an integer.
			\param loci a vector of loci indices. If empty, apply to all loci.
			\param locus a shortcut to \c loci
			\param atPloidy initialize which copy of chromosomes. Default to all.
			\param stage default to \c PreMating
			*/
			pyInit(PyObject * func,  vectoru subPop=vectoru(),
				vectoru loci=vectoru(), int atPloidy=-1,
				intMatrix indRange=intMatrix(),
				double maleFreq=0.5, const vectori& sex = vectori(),
				int stage=PreMating, int begin=0, int end=1, int step=1, vectorl at=vectorl(),
				int rep=REP_ALL, int grp=GRP_ALL, const vectorstr& infoFields=vectorstr())
				: initializer(subPop, indRange, loci, atPloidy, maleFreq, sex,
				stage, begin, end, step, at, rep, grp, infoFields)
			{
				DBG_FAILIF( maleFreq < 0 || maleFreq > 1 ,
					IndexError, "male frequency in the population should be in the range of [0,1]");
				DBG_ASSERT( PyCallable_Check(func),
					ValueError, "Func is not a Python function");

				Py_XINCREF(func);
				m_func = func;
			}

			~pyInit()
			{
				if( m_func != NULL)
					Py_DECREF(m_func);
			}

			/// CPPONLY
			pyInit(const pyInit& rhs):initializer(rhs), m_func(rhs.m_func)
			{
				if( m_func != NULL)
					Py_INCREF(m_func);
			}

			/// deep copy of the operator \c pyInit
			virtual Operator* clone() const
			{
				return new pyInit(*this);
			}

            /// used by Python print function to print out the general information of the operator \c pyInit
			virtual string __repr__()
			{
				return "<simuPOP::pyInit>";
			}

            ///  apply operator \c pyInit???
			bool apply(population& pop);

		private:
			/// the python function with parameter (ind, ploidy, subpop)
			PyObject* m_func;

	};

}
#endif