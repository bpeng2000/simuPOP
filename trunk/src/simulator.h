/***************************************************************************
*   Copyright (C) 2004 by Bo Peng                                         *
*   bpeng@rice.edu
*                                                                         *
*   $LastChangedDate$
*   $Rev$                                                            *
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

#ifndef _SIMULATOR_H
#define _SIMULATOR_H

/**
 \file
 \brief head file of class simulator and some other utility functions
 */

#include "utility.h"
#include "simuPOP_cfg.h"
#include "mating.h"
#include "operator.h"

#include <vector>
#include <algorithm>

using std::vector;
using std::fill;
using std::swap;

#include <boost/archive/text_iarchive.hpp>
#include <boost/archive/text_oarchive.hpp>
#include <boost/archive/xml_iarchive.hpp>
#include <boost/archive/xml_oarchive.hpp>
#include <boost/archive/binary_iarchive.hpp>
#include <boost/archive/binary_oarchive.hpp>
using boost::serialization::make_nvp;

#include <boost/serialization/nvp.hpp>
#include <boost/serialization/utility.hpp>
#include <boost/serialization/vector.hpp>
#include <boost/serialization/split_member.hpp>
#include <boost/serialization/split_free.hpp>

#ifndef OPTIMIZED
#  include <time.h>

#  define InitClock(); \
    if (debug(DBG_PROFILE)) m_clock = clock();

#  define ElapsedTime(name); \
    if (debug(DBG_PROFILE)) \
	{ \
		cout << name << ": " << static_cast<double>(clock() - m_clock) / CLOCKS_PER_SEC << "\n"; \
		m_clock = clock(); \
	}
#else
#  define InitClock();
#  define ElapsedTime(name);
#endif

/** \brief all classes in simuPOP is defined in this namespace
 */
namespace simuPOP {

/// simulator manages several replicates of a population, evolve them using given mating scheme and operators
/**
   Simulators combine three important components of simuPOP:
   population, mating scheme and operator together. A
   simulator is created with an instance of \c population, a
   replicate number \c rep and a mating scheme. It makes \c rep
   number of replicates of this population and control the
   evolutionary process of them. \n

   The most important function of a simulator is \c evolve().
   It accepts an array of operators as its parameters,
   among which, \c preOps and \c postOps will be applied to the
   populations at the beginning and the end of evolution, respectively,
   whereas	\c ops will be applied at every generation. \n

   A simulator separates operators into \em pre-, \em during-, and
 \em post-mating operators. During evolution, a simulator first
   apply all pre-mating operators and then call the \c mate()
   function of the given mating scheme, which will call
   during-mating operators during the birth of each offspring.
   After mating is completed, post-mating operators are
   applied to the offspring in the order at which they appear in the operator list. \n

   Simulators can evolve a given number of generations (the
 \c end parameter of \c evolve), or evolve indefinitely until
   a certain type of operators called terminator terminates it. In this
   case, one or more terminators will check the status of
   evolution and determine if the simulation should be stopped.
   An obvious example of such a terminator is a fixation-checker. \n

   A simulator can be saved to a file in the format
   of \c 'txt', \c 'bin', or \c 'xml'. This allows you to stop a
   simulator and resume it at another time or on another
   machine.
 */
class simulator : public GenoStruTrait
{
public:
	// DEVONLY{ m_curRep, gen  are reference to
	// glocal shared variables. }
	/// create a simulator
	/**
	 \param population a population created by \c population()
	   function. This population will be copied \c rep times to the simulator.
	   Its content will not be changed.
	 \param matingScheme a mating scheme
	 \param rep number of replicates. Default to \c 1.
	 \param grp group number for each replicate. Operators can
	   be applied to a group of replicates using its \c grp parameter.
	 \param applyOpToStoppedReps 	If set, the simulator will continue to apply operators
	   to all stopped replicates until all replicates are marked
	   'stopped'.
	 \param stopIfOneRepStops If set, the simulator will stop evolution if one replicate stops.
	 \return a simulator
	 \sa population, mating
	 */
	simulator(const population & pop, mating & matingScheme,
	          bool stopIfOneRepStops = false,
	          bool applyOpToStoppedReps = false,
	          int rep = 1, vectori grp = vectori());

	/// destroy a simulator along with all its populations
	/**
	 \note <tt>pop = simulator::population()</tt>
	   returns temporary reference to an internal population.
	   After a simulator evolves another genertion or
	   after the simulator is destroyed, this referenced
	   population should \em not be used.
	 */
	~simulator();

	/// CPPONLY
	simulator(const simulator & rhs);

	/// deep copy of a simulator
	simulator * clone() const;

	/// add an information field to all replicates
	/**
	   Add an information field to all replicate, and to the
	   simulator itself. This is important because all populations
	   must have the same genotypic information as the simulator.
	   Adding an information field to one or more of the replicates
	   will compromise the integrity of the simulator.
	 \param field information field to be added
	 */
	void addInfoField(const string & field, double init = 0);

	/// add information fields to all replicates
	/**
	   Add given information fields to all replicate, and to the
	   simulator itself.
	 */
	void addInfoFields(const vectorstr & fields, double init = 0);

	/// set ancestral depth of all replicates
	void setAncestralDepth(UINT depth);

	/// Return a reference to the \c rep replicate of this simulator
	/**

	 \param rep the index number of replicate which will be accessed
	 \return reference to population \c rep.
	 \note  The returned reference is temporary in the sense that
	   the refered population will be invalid after another round
	   of evolution. If you would like to get a persistent population, please use \c getPopulation(rep).
	 */
	population & pop(UINT rep) const
	{
		DBG_FAILIF(rep >= m_numRep, IndexError,
			"replicate index out of range. From 0 to numRep()-1 ");

		return *m_ptrRep[rep];
	}


	/// return a copy of population \c rep
	/**
	   By default return a cloned copy of population \c rep of the simulator. If
	   <tt>destructive==True</tt>, the population is extracted from the simulator,
	   leaving a defunct simulator.

	 \param rep the index number of the replicate which will be obtained
	 \param destructive if true, destroy the copy of population within this simulator.
	   	Default to false. <tt>getPopulation(rep, true)</tt> is a more efficient way
	   	to get hold of a population when the simulator will no longer be used.
	 \return reference to a population
	 */
	population & getPopulation(UINT rep, bool destructive = false)
	{
		if (destructive) {
			population * pop = new population();
			pop->swap(*m_ptrRep[rep]);
			return *pop;
		} else
			return *new population(*m_ptrRep[rep]);
	}


	/// set a new mating scheme
	void setMatingScheme(const mating & matingScheme);

	/// CPPONLY set population... unsafe!
	void setPopulation(population & pop, UINT rep)
	{
		DBG_FAILIF(rep >= m_numRep, IndexError,
			"replicate index out of range. From 0 to numRep()-1 ");
		// get a copy of population
		delete m_ptrRep[rep];
		m_ptrRep[rep] = new population(pop);

		if (pop.genoStru() != this->genoStru() ) {
			DBG_DO(DBG_SIMULATOR,  cout << "Warning: added population has different genotypic structure." << endl);
			setGenoStruIdx(pop.genoStruIdx());
		}
		if (pop.genoStru() != m_scratchPop->genoStru() ) {
			delete m_scratchPop;
			m_scratchPop = new population(pop);
		}
		m_ptrRep[rep]->setRep(rep);
	}


	/// CPPONLY
	UINT curRep() const
	{
		return m_curRep;
	}


	/// return the number of replicates
	UINT numRep() const
	{
		return m_numRep;
	}


	/// return the current generation number
	ULONG gen() const
	{
		return m_gen;
	}


	/// CPPONLY
	int grp()
	{
		return m_groups[m_curRep];
	}


	/// return group indexes
	vectori group()
	{
		return m_groups;
	}


	/// set groups for replicates
	void setGroup(const vectori & grp);

	/// set the current generation. Usually used to reset a simulator.
	/**
	 \param gen new generation index number
	 */
	void setGen(ULONG gen)
	{
		m_gen = gen;
		// set gen for all replicates
		for (UINT i = 0; i < m_numRep; ++i)
			m_ptrRep[i]->setGen(gen, true);
	}


	/// evolve \c steps generation
	/**
	 \sa simulator::evolve()
	 */
	bool step(const vectorop & ops = vectorop(),
	          const vectorop & preOps = vectorop(),
	          const vectorop & postOps = vectorop(), UINT steps = 1,
	          bool dryrun = false)
	{
		// since end gen itself will be executed
		// cur = 5,
		// end = 6
		// will go two steps.
		return evolve(ops, preOps, postOps, -1, steps, dryrun);
	}


	/// evolve all replicates of the population, subject to operators
	/**
	   Evolve to the \c end generation unless \c end=-1. An operator (terminator)
	   may stop the evolution earlier.
	 \n
	 \c ops will be applied to each replicate of the population in the order of:
	 \li all pre-mating opertors
	 \li during-mating operators called by the mating scheme at the
	   birth of each offspring
	 \li all post-mating operators
	   If any pre- or post-mating operator fails to apply, that
	   replicate will be stopped. The behavior of the simulator
	   will be determined by flags \c applyOpToStoppedReps and \c stopIfOneRepStopss.

	 \param ops operators that will be applied at each generation,
	   if they are active at that generation. (Determined by
	   the \c begin, \c end, \c step and \c at parameters of the operator.)
	 \param preOps operators that will be applied before evolution.
	 \c evolve() function will \em not check if they are active.
	 \param postOps operators that will be applied after evolution.
	 \c evolve() function will \em not check if they are active.
	 \param gen generations to evolve. Default to \c -1. In this case, there
	   is no ending generation and a simulator will only be ended by a
	   terminator. Note that simu.gen() refers to the begining of a
	   generation, and starts at 0.
	 \param dryrun dryrun mode. Default to \c False.
	 \result True if evolution performed successfully.
	 \sa simulator::step()
	 \note When <tt>gen = -1</tt>, you can not specify negative generation
	   parameters to operators. How would an operator know which
	   genertion is the -1 genertion if no ending genertion is given?
	 */
	bool evolve(const vectorop & ops,
		const vectorop & preOps = vectorop(),
		const vectorop & postOps = vectorop(),
		int end = -1, int gen = -1, bool dryrun = false);

	///  CPPONLY apply a list of operators to all populations, \c geneartion of the population does not change
	/**
	 \param ops operators that will be applied at all generations.
	   Of course they might not be active at all generations.
	 \result True if evolution finishs successfully.
	 \note Pre-mating oeprators are applied before post-mating operators.
	   No during-mating operators are allowed.
	 */
	bool apply(const vectorop ops, bool dryrun = false);

	/// CPPONLY set 'stop' or not if one replicate stops
	/**
	   If set, the simulator will stop evolution if one replicate stops.
	 \param on turn on or off \c stopIfOneRepStops
	 */
	bool setStopIfOneRepStops(bool on = true)
	{
		m_stopIfOneRepStops = on;
		return on;
	}


	/// CPPONLY get the status of \c setStopIfOneRepStops
	bool stopIfOneRepStops()
	{
		return m_stopIfOneRepStops;
	}


	/// CPPONLY apply operators even if \c rep stops
	/**
	   If set, the simulator will continue to apply operators
	   to all stopped replicates until all replicates are marked
	   'stopped'.
	 \param on turn on or off \c applyOpToStoppedReps flag
	 */
	bool setApplyOpToStoppedReps(bool on = true)
	{
		m_applyOpToStoppedReps = on;
		return on;
	}


	/// CPPONLY get the status of \c setApplyOpToStoppedReps
	bool applyOpToStoppedReps()
	{
		return m_applyOpToStoppedReps;
	}


	/// Return the local namespace of population \c rep, equivalent to <tt>x.population(rep).vars(subPop)</tt>
	PyObject * vars(UINT rep, int subPop = -1)
	{
		if (static_cast<UINT>(rep) >= m_numRep)
			throw ValueError("Replicate index out of range.");

		return m_ptrRep[rep]->vars(subPop);
	}


	/// save simulator in \c 'txt', \c 'bin' or \c 'xml' format
	/**
	 \param filename filename to save the simulator. Default to \c simu.
	 \param format obsolete parameter
	 \param compress obsolete parameter
	 */
	void saveSimulator(string filename, string format = "", bool compress = true) const;

	/// CPPONLY load simulator from a file
	/**
	 \param filename load from filename
	 \param format obsolete parameter
	 \sa saveSimulator
	 */
	void loadSimulator(string filename, string format = "");

	// allow str(population) to get something better looking
	/// used by Python print function to print out the general information of the simulator
	string __repr__()
	{
		return "<simulator with " + toStr(numRep()) + " replicates>";
	}


private:
	friend class boost::serialization::access;

	template<class Archive>
	void save(Archive & ar, const UINT version) const
	{
		ULONG l_gen = gen();
		ar & make_nvp("generation", l_gen);
		ar & make_nvp("num_replicates", m_numRep);

		// ignore scratch population
		for (UINT i = 0; i < m_numRep; i++)
			ar & make_nvp("populations", *m_ptrRep[i]);
		ar & make_nvp("groups", m_groups);
	}


	template<class Archive>
	void load(Archive & ar, const UINT version)
	{
		m_curRep = 1;
		ULONG l_gen;
		ar & make_nvp("generation", l_gen);

		ar & make_nvp("num_replicates", m_numRep);

		m_ptrRep = new population *[m_numRep];

		for (UINT i = 0; i < m_numRep; ++i) {
			m_ptrRep[i] = new population();
			ar & make_nvp("populations", *m_ptrRep[i]);
			m_ptrRep[i]->setRep(i);
		}
		m_scratchPop = new population(*m_ptrRep[0]);
		setGenoStruIdx(m_ptrRep[0]->genoStruIdx());

		ar & make_nvp("groups", m_groups);

		m_stopIfOneRepStops = false;
		m_applyOpToStoppedReps = false;

		// only after all replicates are ready do we set gen
		setGen(l_gen);
	}


	BOOST_SERIALIZATION_SPLIT_MEMBER();

private:
	/// access current population
	population & curpopulation()
	{
		return *m_ptrRep[m_curRep];
	}


	/// access scratch population
	population & scratchpopulation()
	{
		return *m_scratchPop;
	}


private:
	/// current generation
	ULONG m_gen;

	/// index to current population
	UINT m_curRep;

	/// mating functor that will do the mating.
	mating * m_matingScheme;

	/// number of replicates of population
	UINT m_numRep;

	/// groups
	vectori m_groups;

	/// replicate pointers
	population ** m_ptrRep;

	/// the scratch pop
	population * m_scratchPop;

	/// determine various behaviors of simulator
	/// for example: if stop after one replicate stops
	///   or stop after all stop
	///   or if apply operators if stopped.
	bool m_stopIfOneRepStops;

	bool m_applyOpToStoppedReps;

#ifndef OPTIMIZED
	clock_t m_clock;
#endif

};

/// load a simulator from a file with the specified mating scheme. The file format is by default determined by file extension (<tt>format="auto"</tt>). Otherwise, \c format can be one of \c txt, \c bin, or \c xml.
simulator & LoadSimulator(const string & file,
	mating & mate,
	string format = "auto");

}
#endif
