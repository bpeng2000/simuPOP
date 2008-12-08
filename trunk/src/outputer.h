/***************************************************************************
*   Copyright (C) 2004 by Bo Peng                                         *
*   bpeng@rice.edu
*                                                                         *
*   $LastChangedDate$
*   $Rev$                                                    *
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

#ifndef _OUTPUTER_H
#define _OUTPUTER_H
/**
   \file
   \brief head file of class outputer: public baseOperator
 */
#include "utility.h"
#include "operator.h"
#include <iostream>

#include <iomanip>
using std::setw;
using std::hex;
using std::dec;

namespace simuPOP {
/**
   \brief Base class of all operators that out information.
   different format.

   @author Bo Peng
 */

class outputer : public baseOperator
{

public:
	/// constructor.
	outputer(string output = ">", string outputExpr = "",
		int stage = PostMating, int begin = 0, int end = -1, int step = 1, vectorl at = vectorl(),
		const repList & rep = repList(), const subPopList & subPop = subPopList(), const vectorstr & infoFields = vectorstr()) :
		baseOperator(output, outputExpr, stage, begin, end, step, at, rep, subPop, infoFields)
	{
	};

	/// destructor
	virtual ~outputer()
	{
	};

	virtual baseOperator * clone() const
	{
		return new outputer(*this);
	}


};

/// Output a given string
/**
   A common usage is to output a new line for the last replicate.
 */
class pyOutput : public outputer
{

public:
	/// Create a \c pyOutput operator that outputs a given string
	/**
	   \param str string to be outputted
	 */
	pyOutput(string str = "", string output = ">", string outputExpr = "",
		int stage = PostMating, int begin = 0, int end = -1, int step = 1, vectorl at = vectorl(),
		const repList & rep = repList(), const subPopList & subPop = subPopList(), const vectorstr & infoFields = vectorstr()) :
		outputer(output, outputExpr, stage, begin, end,
		         step, at, rep, subPop, infoFields), m_string(str)
	{
	}


	/// simply output some info
	virtual bool apply(population & pop)
	{
		ostream & out = this->getOstream(pop.dict());

		out << m_string;
		this->closeOstream();
		return true;
	}


	///// destructor
	virtual ~pyOutput()
	{
	}


	virtual baseOperator * clone() const
	{
		return new pyOutput(*this);
	}


	/// set output string.
	void setString(const string str)
	{
		m_string = str;
	}


	virtual string __repr__()
	{
		string reprStr;

		for (size_t i = 0; i < 10 && i < m_string.size(); ++i)
			if (m_string[i] != '\n')
				reprStr += m_string[i];
		if (m_string.size() > 10)
			reprStr += "... ";
		return "<simuPOP::output " + reprStr + "> " ;
	}


private:
	string m_string;
};


/// dump the content of a population.
class dumper : public outputer
{
public:
	/// dump a population
	/**
	   \param genotype Whether or not display genotype
	   \param structure Whether or not display genotypic structure
	   \param width number of characters to display an allele. Default to \c 1.
	   \param ancGen how many ancestral generations to display
	   \param chrom chromosome(s) to display
	   \param loci loci to display
	   \param subPop only display subpopulation(s)
	   \param indRange range(s) of individuals to display
	   \param max the maximum number of individuals to display. Default to \c 100.
	        This is to avoid careless dump of huge populations.
	   \param output output file. Default to the standard output.
	   \param outputExpr and other parameters: refer to help(baseOperator.__init__)

	 */
	dumper(bool genotype = true, bool structure = true, int ancGen = 0, int width = 1, UINT max = 100,
		const vectori & chrom = vectori(), const vectori & loci = vectori(), const vectoru & subPop = vectoru(),
		const vectorlu & indRange = vectorlu(),
		string output = ">", string outputExpr = "",
		int stage = PostMating, int begin = 0, int end = -1, int step = 1, vectorl at = vectorl(),
		const repList & rep = repList(),    // const subPopList & subPop = subPopList(),
		const vectorstr & infoFields = vectorstr()) :
		outputer(output, outputExpr, stage, begin, end, step, at, rep, subPopList(), infoFields),
		m_showGenotype(genotype), m_showStructure(structure), m_ancGen(ancGen), m_width(width),
		m_chrom(chrom), m_loci(loci), m_subPop(subPop), m_indRange(indRange), m_max(max)
	{
	}


	virtual baseOperator * clone() const
	{
		return new dumper(*this);
	}


	virtual bool apply(population & pop);

	virtual ~dumper()
	{
	};

	virtual string __repr__()
	{
		return "<simuPOP::dumper>" ;
	}


private:
	///
	bool m_showGenotype;

	///
	bool m_showStructure;

	///
	int m_ancGen;

	/// disp width when outputing alleles
	int m_width;

	///
	vectori m_chrom;

	///
	vectori m_loci;

	///
	vectoru m_subPop;

	///
	vectorlu m_indRange;

	/// only output first ... individuals. Good for large population
	UINT m_max;
};

/// save population to a file
class savePopulation : public outputer
{
public:
	/// save population
	/**
	    \param output output filename.
	    \param outputExpr An expression that will be evalulated dynamically to
	        determine file name. Parameter \c output will be ignored if this
	        parameter is given.
	    \param format obsolete parameter
	    \param compress obsolete parameter
	 */
	savePopulation(string output = "", string outputExpr = "",
		string format = "", bool compress = true, int stage = PostMating, int begin = 0, int end = -1,
		int step = 1, vectorl at = vectorl(), const repList & rep = repList(), const subPopList & subPop = subPopList(), const vectorstr & infoFields = vectorstr()) :
		outputer("", "", stage, begin, end, step, at, rep, subPop, infoFields),
		m_filename(output), m_filenameParser(outputExpr)
	{
		DBG_WARNING(!format.empty(), "Parameter format is now obsolete.");
		if (output == "" && outputExpr == "")
			throw ValueError("Please specify one of output and outputExpr.");
	}


	~savePopulation()
	{
	}


	virtual baseOperator * clone() const
	{
		return new savePopulation(*this);
	}


	virtual bool apply(population & pop);

	virtual string __repr__()
	{
		return "<simuPOP::save population>" ;
	}


private:
	/// filename,
	string m_filename;

	/// or an expression that will be evaluated dynamically
	Expression m_filenameParser;
};

}
#endif
