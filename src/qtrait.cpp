/**
 *  $File: qtrait.cpp $
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

#include "qtrait.h"

namespace simuPOP {

bool baseQuanTrait::apply(population & pop)
{
	vectoru infoIdx(infoSize());

	for (size_t i = 0; i < infoSize(); ++i)
		infoIdx[i] = pop.infoIdx(infoField(i));

	UINT ansGen = 0;
	UINT oldGen = pop.curAncestralGen();
	if (m_ancGen == -1)
		ansGen = pop.ancestralGens();
	else if (m_ancGen > 0) {
		if (static_cast<UINT>(m_ancGen) > pop.ancestralGens())
			ansGen = pop.ancestralGens();
		else
			ansGen = m_ancGen;
	}
	vectorf traits(infoSize());
	for (UINT i = 0; i <= ansGen; ++i) {
		pop.useAncestralGen(i);

		subPopList subPops = applicableSubPops();

		// the usual whole population, easy case.
		if (subPops.allAvail())
			subPops.useSubPopsFrom(pop);

		subPopList::const_iterator sp = subPops.begin();
		subPopList::const_iterator spEnd = subPops.end();
		for (; sp != spEnd; ++sp) {
			if (sp->isVirtual())
				pop.activateVirtualSubPop(*sp);

			IndIterator ind = pop.indIterator(sp->subPop());
			for (; ind.valid(); ++ind) {
				qtrait(&*ind, pop.gen(), traits);
				for (size_t i = 0; i < infoSize(); ++i)
					ind->setInfo(traits[i], infoIdx[i]);
			}

			if (sp->isVirtual())
				pop.deactivateVirtualSubPop(sp->subPop());
		}
	}
	pop.useAncestralGen(oldGen);
	return true;
}


bool baseQuanTrait::applyDuringMating(population & pop, RawIndIterator offspring,
                                      individual * dad, individual * mom)

{
	vectorf traits(infoSize());

	qtrait(&*offspring, pop.gen(), traits);
	for (size_t i = 0; i < traits.size(); ++i)
		offspring->setInfo(traits[i], infoField(i));
	return true;
}


void pyQuanTrait::qtrait(individual * ind, ULONG gen, vectorf & traits)
{
	PyObject * args = PyTuple_New(m_func.numArgs());

	DBG_ASSERT(args, RuntimeError, "Failed to create a parameter tuple");

	for (int i = 0; i < m_func.numArgs(); ++i) {
		const string & arg = m_func.arg(i);
		if (arg == "ind")
			PyTuple_SET_ITEM(args, i, pyIndObj(static_cast<void *>(ind)));
		else if (arg == "geno")
			PyTuple_SET_ITEM(args, i, ind->genoAtLoci(m_loci));
		else if (arg == "gen")
			PyTuple_SET_ITEM(args, i, PyInt_FromLong(gen));
		else {
			DBG_FAILIF(!ind->hasInfoField(arg), ValueError,
				"Only parameters 'ind', 'geno', 'gen', and names of information fields are "
				"acceptable in function " + m_func.name());
			PyTuple_SET_ITEM(args, i, PyFloat_FromDouble(ind->info(arg)));
		}
	}

	PyObject * res = PyEval_CallObject(m_func.func(), args);
	Py_XDECREF(args);

	if (PyNumber_Check(res)) {
		DBG_ASSERT(infoSize() == 1, RuntimeError,
			"A number is returned from a user-defined function but a sequence is expected.");
		PyObj_As_Double(res, traits[0]);
		Py_DECREF(res);
	} else if (PySequence_Check(res)) {
		DBG_ASSERT(static_cast<UINT>(PySequence_Size(res)) == traits.size(), RuntimeError,
			"Length of returned sequence does not match number of trait fields");
		PyObj_As_Array(res, traits);
		Py_DECREF(res);
	} else {
		DBG_FAILIF(true, RuntimeError, "Invalid return value from penetrance function.");
	}
	return;
}


}