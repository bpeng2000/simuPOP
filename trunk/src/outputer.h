/**
 *  $File: outputer.h $
 *  $LastChangedDate$
 *  $Rev$
 *
 *  This file is part of simuPOP, a forward-time population genetics
 *  simulation environment. Please visit http://simupop.sourceforge.net
 *  for details.
 *
 *  Copyright (C) 2004 - 2009 Bo Peng (bpeng@mdanderson.org)
 *
 *  This program is free software: you can redistribute it and/or modify
 *  it under the terms of the GNU General Public License as published by
 *  the Free Software Foundation, either version 3 of the License, or
 *  (at your option) any later version.
 *
 *  This program is distributed in the hope that it will be useful,
 *  but WITHOUT ANY WARRANTY; without even the implied warranty of
 *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *  GNU General Public License for more details.
 *
 *  You should have received a copy of the GNU General Public License
 *  along with this program. If not, see <http://www.gnu.org/licenses/>.
 */

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

/** This operator outputs a given string when it is applied to a population.
 */
class pyOutput : public baseOperator
{

public:
	/** Creates a \c pyOutput operator that outputs a string \e msg to
	 *  \e output (default to standard terminal output) when it is applied
	 *  to a population. Please refer to class \c baseOperator for a detailed
	 *  description of common operator parameters such as \e stage, \e begin
	 *  and \e output.
	 */
	pyOutput(const string & msg = string(), const stringFunc & output = ">",
		int begin = 0, int end = -1, int step = 1, const intList & at = vectori(),
		const intList & reps = intList(), const subPopList & subPops = subPopList(),
		const stringList & infoFields = vectorstr()) :
		baseOperator(output, begin, end, step, at, reps, subPops, infoFields),
		m_string(msg)
	{
	}


	/// simply output some info
	virtual bool apply(population & pop);

	/// destructor
	virtual ~pyOutput()
	{
	}


	/// Deep copy of a \e pyOutput operator.
	virtual baseOperator * clone() const
	{
		return new pyOutput(*this);
	}


	/// HIDDEN
	string description()
	{
		string reprStr;

		for (size_t i = 0; i < 10 && i < m_string.size(); ++i)
			if (m_string[i] != '\n')
				reprStr += m_string[i];
		if (m_string.size() > 10)
			reprStr += "... ";
		return "<simuPOP.output " + reprStr + "> " ;
	}


private:
	string m_string;
};


/** This operator dumps the content of a population in a human readable format.
 *  Because this output format is not structured and can not be imported back
 *  to simuPOP, this operator is usually used to dump a small population to a
 *  terminal for demonstration and debugging purposes.
 */
class dumper : public baseOperator
{
public:
	/** Create a operator that dumps the genotype structure (if \e structure is
	 *  \c True) and genotype (if \e genotype is \c True) to an \e output (
	 *  default to standard terminal output). Because a population can be large,
	 *  this operator will only output the first 100 (parameter \e max)
	 *  individuals of the present generation (parameter \e ancGen). All loci
	 *  will be outputed unless parameter \e loci are used to specify a subset
	 *  of loci. If a list of (virtual) subpopulations are specified, this
	 *  operator will only output individuals in these outputs. Please refer to
	 *  class \c baseOperator for a detailed explanation for common parameters
	 *  such as \e output and \e stage.
	 */
	dumper(bool genotype = true, bool structure = true, int ancGen = 0,
		int width = 1, UINT max = 100, const uintList & loci = vectoru(), const stringFunc & output = ">",
		int begin = 0, int end = -1, int step = 1, const intList & at = vectori(),
		const intList & reps = intList(), const subPopList & subPops = subPopList(),
		const stringList & infoFields = vectorstr()) :
		baseOperator(output, begin, end, step, at, reps, subPops, infoFields),
		m_showGenotype(genotype), m_showStructure(structure), m_ancGen(ancGen), m_width(width),
		m_loci(loci.elems()), m_max(max)
	{
	}


	/// Deep copy of a dumper operator.
	virtual baseOperator * clone() const
	{
		return new dumper(*this);
	}


	/// Apply a dumper operator to population \e pop.
	virtual bool apply(population & pop);

	/// destructor.
	virtual ~dumper()
	{
	};

	/// HIDDEN
	string description()
	{
		return "<simuPOP.dumper>" ;
	}


private:
	void displayStructure(const population & pop, ostream & out);

	UINT displayGenotype(const population & pop, const subPopList & subPops, ostream & out);

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
	vectoru m_loci;

	/// only output first ... individuals. Good for large population
	UINT m_max;
};


/** An operator that save populations to specified files.
 */
class savePopulation : public baseOperator
{
public:
	/** Create an operator that saves a population to \e output when it is
	 *  applied to the population. This operator supports all output
	 *  specifications (\c '', \c 'filename', \c 'filename' prefixed by one
	 *  or more '>' characters, and \c '!expr') but output from different
	 *  operators will always replace existing files (effectively ignore
	 *  '>' specification). Parameter \e subPops is ignored. Please refer to
	 *  class \c baseOperator for a detailed description about common operator
	 *  parameters such as \e stage and \e begin.
	 */
	savePopulation(const stringFunc & output = "", int begin = 0, int end = -1,
		int step = 1, const intList & at = vectori(), const intList & reps = intList(),
		const subPopList & subPops = subPopList(), const stringList & infoFields = vectorstr()) :
		baseOperator("", begin, end, step, at, reps, subPops, infoFields),
		m_filename(output.value())
	{
		if (output.empty())
			throw ValueError("Please specify a output file.");
	}


	/// destructor.
	~savePopulation()
	{
	}


	/// Deep copy of a savePopulation operator.
	virtual baseOperator * clone() const
	{
		return new savePopulation(*this);
	}


	/// Apply operator to population \e pop.
	virtual bool apply(population & pop);

	/// HIDDEN
	string description()
	{
		return "<simuPOP.save population>" ;
	}


private:
	/// filename,
	string m_filename;
};

}
#endif