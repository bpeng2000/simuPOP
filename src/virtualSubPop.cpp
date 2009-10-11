/**
 *  $File: virtualSubPop.cpp $
 *  $LastChangedDate: 2009-01-14 21:43:45 -0600 (Wed, 14 Jan 2009) $
 *  $Rev: 2335 $
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

#include "simuPOP_cfg.h"
#include "virtualSubPop.h"
#include "population.h"

namespace simuPOP {

ostream & operator<<(ostream & out, const vspID & vsp)
{
	out << vsp.subPop();
	if (vsp.isVirtual())
		out << "," << vsp.virtualSubPop();
	return out;
}


void vspSplitter::resetSubPop(population & pop, SubPopID subPop)
{
	DBG_ASSERT(m_activated == InvalidSubPopID || m_activated == subPop,
		ValueError, "Subpopulation " + toStr(subPop) + " is not activated.");

	if (m_activated == InvalidSubPopID)
		return;

	RawIndIterator it = pop.rawIndBegin(subPop);
	RawIndIterator it_end = pop.rawIndEnd(subPop);
	for (; it != it_end; ++it)
		it->setVisible(true);
	m_activated = InvalidSubPopID;
}


ULONG vspSplitter::countVisibleInds(const population & pop, SubPopID subPop) const
{
	if (activatedSubPop() != subPop)
		return pop.subPopSize(subPop);
	ULONG count = 0;
	ConstRawIndIterator it = pop.rawIndBegin(subPop);
	ConstRawIndIterator it_end = pop.rawIndEnd(subPop);
	for (; it != it_end; ++it)
		if (it->visible())
			++count;
	return count;
}


combinedSplitter::combinedSplitter(const vectorsplitter & splitters,
	const intMatrix & vspMap)
	: vspSplitter(), m_splitters(0), m_vspMap(0), m_inputMap(vspMap)
{
	for (size_t i = 0; i < splitters.size(); ++i)
		m_splitters.push_back(splitters[i]->clone());
	// default vsp map
	if (vspMap.empty()) {
		size_t idx = 0;
		for (size_t i = 0; i < splitters.size(); ++i)
			for (size_t j = 0; j < splitters[i]->numVirtualSubPop(); ++j, ++idx)
				m_vspMap.push_back(vspList(1, vspPair(i, j)));
	} else {
		for (size_t i = 0; i < vspMap.size(); ++i) {
			vspList list;
			for (size_t j = 0; j < vspMap[i].size(); ++j) {
				// find out which splitter and which vsp
				UINT lower = 0;
				UINT higher = 0;
				bool done = false;
				for (size_t s = 0; s < splitters.size(); ++s) {
					higher += splitters[s]->numVirtualSubPop();
					if (vspMap[i][j] >= lower && vspMap[i][j] < higher) {
						list.push_back(vspPair(s, vspMap[i][j] - lower));
						done = true;
						break;
					}
					lower = higher;
				}
				DBG_ASSERT(done, IndexError,
					"Given vsp index " + toStr(vspMap[i][j]) + " is larger than the number of total VSPs");
			}
			m_vspMap.push_back(list);
		}
	}
}


combinedSplitter::~combinedSplitter()
{
	for (size_t i = 0; i < m_splitters.size(); ++i)
		delete m_splitters[i];
}


vspSplitter * combinedSplitter::clone() const
{
	return new combinedSplitter(m_splitters, m_inputMap);
}


ULONG combinedSplitter::size(const population & pop, SubPopID subPop, SubPopID virtualSubPop) const
{
	DBG_FAILIF(static_cast<UINT>(virtualSubPop) >= m_vspMap.size(), IndexError,
		"Virtual subpopulation index out of range");

	if (m_vspMap[virtualSubPop].empty())
		return 0;

	const vspList & list = m_vspMap[virtualSubPop];
	if (list.size() == 1)
		return m_splitters[list[0].first]->size(pop, subPop, list[0].second);

	size_t count = 0;
	for (size_t ind = 0; ind < pop.subPopSize(subPop); ++ind) {
		bool ok = false;
		for (size_t s = 0; s < list.size(); ++s) {
			if (m_splitters[list[s].first]->contains(pop, ind, vspID(subPop, list[s].second))) {
				ok = true;
				break;
			}
		}
		if (ok)
			++count;
	}
	return count;
}


bool combinedSplitter::contains(const population & pop, ULONG ind, vspID vsp)
{
	SubPopID virtualSubPop = vsp.virtualSubPop();

	DBG_FAILIF(static_cast<UINT>(virtualSubPop) >= m_vspMap.size(), IndexError,
		"Virtual subpopulation index out of range");

	const vspList & list = m_vspMap[virtualSubPop];
	for (size_t s = 0; s < list.size(); ++s)
		if (m_splitters[list[s].first]->contains(pop, ind, vspID(vsp.subPop(), list[s].second)))
			return true;
	return false;
}


void combinedSplitter::activate(population & pop, SubPopID subPop, SubPopID virtualSubPop,
                                IterationType type)
{
	const vspList & list = m_vspMap[virtualSubPop];

	if (list.size() == 0)
		return;

	if (list.size() == 1)
		m_splitters[list[0].first]->activate(pop, subPop, list[0].second, type);
	else {
		const vspList & list = m_vspMap[virtualSubPop];
		for (size_t ind = 0; ind < pop.subPopSize(subPop); ++ind) {
			bool ok = false;
			for (size_t i = 0; i < list.size(); ++i) {
				if (m_splitters[list[i].first]->contains(pop, ind, vspID(subPop, list[i].second))) {
					ok = true;
					break;
				}
			}
			if (type == VisibleInds)
				pop.ind(ind, subPop).setVisible(ok);
			else
				pop.ind(ind, subPop).setIteratable(ok);
		}
	}
	if (type == VisibleInds)
		m_activated = subPop;
}


void combinedSplitter::deactivate(population & pop, SubPopID sp)
{
	resetSubPop(pop, sp);
	m_activated = InvalidSubPopID;
}


string combinedSplitter::name(SubPopID sp)
{
	const vspList & list = m_vspMap[sp];
	string name;

	for (size_t i = 0; i < list.size(); ++i) {
		if (i != 0)
			name += " or ";
		name += m_splitters[list[i].first]->name(list[i].second);
	}
	return name;
}


productSplitter::productSplitter(const vectorsplitter & splitters)
	: vspSplitter(), m_numVSP(0)
{
	for (size_t i = 0; i < splitters.size(); ++i) {
		if (m_numVSP == 0)
			m_numVSP = 1;
		m_numVSP *= splitters[i]->numVirtualSubPop();
		m_splitters.push_back(splitters[i]->clone());
	}
}


vectori productSplitter::getVSPs(SubPopID vsp) const
{
	DBG_FAILIF(vsp >= m_numVSP, IndexError,
		"Subpopulation index out of range.");

	vectori res;
	UINT tmpMod = m_numVSP;
	UINT tmpIdx = vsp;
	for (size_t i = 0; i < m_splitters.size(); ++i) {
		tmpMod /= m_splitters[i]->numVirtualSubPop();
		res.push_back(tmpIdx / tmpMod);
		tmpIdx %= tmpMod;
	}
	return res;
}


productSplitter::~productSplitter()
{
	for (size_t i = 0; i < m_splitters.size(); ++i)
		delete m_splitters[i];
}


vspSplitter * productSplitter::clone() const
{
	return new productSplitter(m_splitters);
}


ULONG productSplitter::size(const population & pop, SubPopID subPop, SubPopID virtualSubPop) const
{
	vectori idx = getVSPs(virtualSubPop);
	size_t count = 0;

	for (size_t i = 0; i < pop.subPopSize(subPop); ++i) {
		bool ok = true;
		for (size_t s = 0; s < m_splitters.size(); ++s) {
			if (!m_splitters[s]->contains(pop, i, vspID(subPop, idx[s]))) {
				ok = false;
				break;
			}
		}
		if (ok)
			++count;
	}
	return count;
}


bool productSplitter::contains(const population & pop, ULONG ind, vspID vsp)
{
	vectori idx = getVSPs(vsp.virtualSubPop());

	for (size_t s = 0; s < m_splitters.size(); ++s)
		if (!m_splitters[s]->contains(pop, ind, vspID(vsp.subPop(), idx[s])))
			return false;
	return true;
}


void productSplitter::activate(population & pop, SubPopID subPop, SubPopID virtualSubPop,
                               IterationType type)
{
	vectori idx = getVSPs(virtualSubPop);

	for (size_t i = 0; i < pop.subPopSize(subPop); ++i) {
		bool ok = true;
		for (size_t s = 0; s < m_splitters.size(); ++s) {
			if (!m_splitters[s]->contains(pop, i, vspID(subPop, idx[s]))) {
				ok = false;
				break;
			}
		}
		if (type == VisibleInds)
			pop.ind(i, subPop).setVisible(ok);
		else
			pop.ind(i, subPop).setIteratable(ok);
	}

	if (type == VisibleInds)
		m_activated = subPop;
}


void productSplitter::deactivate(population & pop, SubPopID sp)
{
	resetSubPop(pop, sp);
	m_activated = InvalidSubPopID;
}


string productSplitter::name(SubPopID sp)
{
	vectori idx = getVSPs(sp);
	string name;

	for (size_t i = 0; i < idx.size(); ++i) {
		if (i != 0)
			name += ", ";
		name += m_splitters[i]->name(idx[i]);
	}
	return name;
}


ULONG sexSplitter::size(const population & pop, SubPopID subPop, SubPopID virtualSubPop) const
{
	if (virtualSubPop == InvalidSubPopID)
		return countVisibleInds(pop, subPop);
	ConstRawIndIterator it = pop.rawIndBegin(subPop);
	ConstRawIndIterator it_end = pop.rawIndEnd(subPop);
	ULONG count = 0;
	Sex s = virtualSubPop == 0 ? Male : Female;

	for (; it != it_end; ++it)
		if (it->sex() == s)
			++count;
	return count;
}


bool sexSplitter::contains(const population & pop, ULONG ind, vspID vsp)
{
	return (vsp.virtualSubPop() == 0 ? Male : Female) == pop.ind(ind, vsp.subPop()).sex();
}


void sexSplitter::activate(population & pop, SubPopID subPop, SubPopID virtualSubPop,
                           IterationType type)
{
	Sex s = virtualSubPop == 0 ? Male : Female;

	RawIndIterator it = pop.rawIndBegin(subPop);
	RawIndIterator it_end = pop.rawIndEnd(subPop);

	for (; it != it_end; ++it)
		if (type == VisibleInds)
			it->setVisible(it->sex() == s);
		else
			it->setIteratable(it->sex() == s);
	if (type == VisibleInds)
		m_activated = subPop;
}


void sexSplitter::deactivate(population & pop, SubPopID subPop)
{
	resetSubPop(pop, subPop);
}


ULONG affectionSplitter::size(const population & pop, SubPopID subPop, SubPopID virtualSubPop) const
{
	if (virtualSubPop == InvalidSubPopID)
		return countVisibleInds(pop, subPop);
	ConstRawIndIterator it = pop.rawIndBegin(subPop);
	ConstRawIndIterator it_end = pop.rawIndEnd(subPop);
	ULONG count = 0;
	// 0 is unaffected
	bool aff = virtualSubPop == 0 ? false : true;

	for (; it != it_end; ++it)
		if (it->affected() == aff)
			++count;
	return count;
}


bool affectionSplitter::contains(const population & pop, ULONG ind, vspID vsp)
{
	return (vsp.virtualSubPop() == 0 ? false : true) == pop.ind(ind, vsp.subPop()).affected();
}


void affectionSplitter::activate(population & pop, SubPopID subPop, SubPopID virtualSubPop,
                                 IterationType type)
{
	bool aff = virtualSubPop == 0 ? false : true;

	RawIndIterator it = pop.rawIndBegin(subPop);
	RawIndIterator it_end = pop.rawIndEnd(subPop);

	for (; it != it_end; ++it)
		if (type == VisibleInds)
			it->setVisible(it->affected() == aff);
		else
			it->setIteratable(it->affected() == aff);
	if (type == VisibleInds)
		m_activated = subPop;
}


void affectionSplitter::deactivate(population & pop, SubPopID subPop)
{
	resetSubPop(pop, subPop);
}


infoSplitter::infoSplitter(string info, const vectorinfo & values,
	const vectorf & cutoff, const matrix & ranges)
	: vspSplitter(),
	m_info(info), m_values(values), m_cutoff(cutoff), m_ranges(ranges)
{
	DBG_FAILIF(m_values.empty() && m_cutoff.empty() && m_ranges.empty(),
		ValueError, "Please specify either a list of values, a set of cutoff values or ranges");
	DBG_FAILIF(m_values.empty() + m_cutoff.empty() + m_ranges.empty() != 2,
		ValueError, "Please specify only one of parameters values, cutoff or ranges.");
	// cutoff value has to be ordered
	if (!m_cutoff.empty()) {
		for (size_t i = 1; i < m_cutoff.size(); ++i) {
			DBG_ASSERT(m_cutoff[i - 1] < m_cutoff[i],
				ValueError,
				"Cutoff values have to be in increasing order");
		}
	}
	if (!m_ranges.empty()) {
		for (size_t i = 1; i < m_ranges.size(); ++i) {
			DBG_FAILIF(m_ranges[i].size() != 2, ValueError,
				"Invalid information range.");
			DBG_ASSERT(m_ranges[i][1] > m_ranges[i][0],
				ValueError, "Invalid range.");
		}
	}
}


ULONG infoSplitter::size(const population & pop, SubPopID subPop, SubPopID virtualSubPop) const
{
	if (virtualSubPop == InvalidSubPopID)
		return countVisibleInds(pop, subPop);
	UINT idx = pop.infoIdx(m_info);

	ULONG count = 0;

	ConstRawIndIterator it = pop.rawIndBegin(subPop);
	ConstRawIndIterator it_end = pop.rawIndEnd(subPop);

	if (!m_cutoff.empty()) {
		DBG_FAILIF(static_cast<UINT>(virtualSubPop) > m_cutoff.size(), IndexError,
			"Virtual Subpoplation index out of range of 0 ~ "
			+ toStr(m_cutoff.size()));

		// using cutoff, below
		if (virtualSubPop == 0) {
			for (; it != it_end; ++it)
				if (it->info(idx) < m_cutoff[0])
					count++;
			return count;
		} else if (static_cast<UINT>(virtualSubPop) == m_cutoff.size()) {
			double v = m_cutoff.back();
			for (; it != it_end; ++it)
				if (it->info(idx) >= v)
					count++;
			return count;
		} else {         // in between
			double v1 = m_cutoff[virtualSubPop - 1];
			double v2 = m_cutoff[virtualSubPop];
			for (; it != it_end; ++it) {
				double v = it->info(idx);
				if (v >= v1 && v < v2)
					count++;
			}
			return count;
		}
	} else if (!m_values.empty()) {
		DBG_FAILIF(static_cast<UINT>(virtualSubPop) >= m_values.size(), IndexError,
			"Virtual Subpoplation index out of range of 0 ~ "
			+ toStr(m_values.size() - 1));
		double v = m_values[virtualSubPop];
		for (; it != it_end; ++it)
			if (fcmp_eq(it->info(idx), v))
				count++;
		return count;
	} else {
		DBG_FAILIF(static_cast<UINT>(virtualSubPop) >= m_ranges.size(), IndexError,
			"Virtual Subpoplation index out of range of 0 ~ "
			+ toStr(m_ranges.size() - 1));
		double v1 = m_ranges[virtualSubPop][0];
		double v2 = m_ranges[virtualSubPop][1];
		for (; it != it_end; ++it) {
			double v = it->info(idx);
			if (v >= v1 && v < v2)
				count++;
		}
		return count;
	}
	// should never reach here.
	return 0;
}


UINT infoSplitter::numVirtualSubPop()
{
	if (!m_cutoff.empty())
		return m_cutoff.size() + 1;
	else if (!m_values.empty())
		return m_values.size();
	else
		return m_ranges.size();
}


bool infoSplitter::contains(const population & pop, ULONG ind, vspID vsp)
{
	SubPopID virtualSubPop = vsp.virtualSubPop();
	UINT idx = pop.infoIdx(m_info);

	if (!m_cutoff.empty()) {
		DBG_FAILIF(static_cast<UINT>(virtualSubPop) > m_cutoff.size(), IndexError,
			"Virtual Subpoplation index out of range of 0 ~ "
			+ toStr(m_cutoff.size()));

		// using cutoff, below
		if (virtualSubPop == 0)
			return pop.ind(ind, vsp.subPop()).info(idx) < m_cutoff[0];
		else if (static_cast<UINT>(virtualSubPop) == m_cutoff.size())
			return pop.ind(ind, vsp.subPop()).info(idx) >= m_cutoff.back();
		else {         // in between
			double v1 = m_cutoff[virtualSubPop - 1];
			double v2 = m_cutoff[virtualSubPop];
			double v = pop.ind(ind, vsp.subPop()).info(idx);
			return v >= v1 && v < v2;
		}
	} else if (!m_values.empty()) {
		DBG_FAILIF(static_cast<UINT>(virtualSubPop) >= m_values.size(), IndexError,
			"Virtual Subpoplation index " + toStr(virtualSubPop) + " out of range of 0 ~ "
			+ toStr(m_values.size() - 1));
		return fcmp_eq(pop.ind(ind, vsp.subPop()).info(idx), m_values[virtualSubPop]);
	} else {
		DBG_FAILIF(static_cast<UINT>(virtualSubPop) >= m_ranges.size(), IndexError,
			"Virtual Subpoplation index " + toStr(virtualSubPop) + " out of range of 0 ~ "
			+ toStr(m_ranges.size() - 1));
		double v = pop.ind(ind, vsp.subPop()).info(idx);
		return v >= m_ranges[virtualSubPop][0] && v < m_ranges[virtualSubPop][1];
	}
	// this should not be reached.
	return false;
}


void infoSplitter::activate(population & pop, SubPopID subPop, SubPopID virtualSubPop,
                            IterationType type)
{
	UINT idx = pop.infoIdx(m_info);

	RawIndIterator it = pop.rawIndBegin(subPop);
	RawIndIterator it_end = pop.rawIndEnd(subPop);

	if (!m_cutoff.empty()) {
		DBG_FAILIF(static_cast<UINT>(virtualSubPop) > m_cutoff.size(), IndexError,
			"Virtual Subpoplation index out of range of 0 ~ "
			+ toStr(m_cutoff.size()));

		// using cutoff, below
		if (virtualSubPop == 0) {
			for (; it != it_end; ++it)
				if (type == VisibleInds)
					it->setVisible(it->info(idx) < m_cutoff[0]);
				else
					it->setIteratable(it->info(idx) < m_cutoff[0]);
		} else if (static_cast<UINT>(virtualSubPop) == m_cutoff.size()) {
			double v = m_cutoff.back();
			for (; it != it_end; ++it)
				if (type == VisibleInds)
					it->setVisible(it->info(idx) >= v);
				else
					it->setIteratable(it->info(idx) >= v);
		} else {         // in between
			double v1 = m_cutoff[virtualSubPop - 1];
			double v2 = m_cutoff[virtualSubPop];
			for (; it != it_end; ++it) {
				double v = it->info(idx);
				if (type == VisibleInds)
					it->setVisible(v >= v1 && v < v2);
				else
					it->setIteratable(v >= v1 && v < v2);
			}
		}
	} else if (!m_values.empty()) {
		DBG_FAILIF(static_cast<UINT>(virtualSubPop) >= m_values.size(), IndexError,
			"Virtual Subpoplation index out of range of 0 ~ "
			+ toStr(m_values.size() - 1));
		double v = m_values[virtualSubPop];
		for (; it != it_end; ++it)
			if (type == VisibleInds)
				it->setVisible(fcmp_eq(it->info(idx), v));
			else
				it->setIteratable(fcmp_eq(it->info(idx), v));
	} else {
		DBG_FAILIF(static_cast<UINT>(virtualSubPop) >= m_ranges.size(), IndexError,
			"Virtual Subpoplation index out of range of 0 ~ "
			+ toStr(m_ranges.size() - 1));
		double v1 = m_ranges[virtualSubPop][0];
		double v2 = m_ranges[virtualSubPop][1];
		for (; it != it_end; ++it) {
			double v = it->info(idx);
			if (type == VisibleInds)
				it->setVisible(v >= v1 && v < v2);
			else
				it->setIteratable(v >= v1 && v < v2);
		}
	}
	if (type == VisibleInds)
		m_activated = subPop;
}


void infoSplitter::deactivate(population & pop, SubPopID subPop)
{
	resetSubPop(pop, subPop);
}


string infoSplitter::name(SubPopID sp)
{
	if (!m_cutoff.empty()) {
		DBG_FAILIF(static_cast<UINT>(sp) > m_cutoff.size(), IndexError,
			"Virtual Subpoplation index out of range of 0 ~ "
			+ toStr(m_cutoff.size()));
		if (sp == 0)
			return m_info + " < " + toStr(m_cutoff[0]);
		else if (static_cast<UINT>(sp) == m_cutoff.size())
			return m_info + " >= " + toStr(m_cutoff[sp - 1]);
		else
			return toStr(m_cutoff[sp - 1]) + " <= " + m_info + " < "
			       + toStr(m_cutoff[sp]);
	} else if (!m_values.empty()) {
		DBG_FAILIF(static_cast<UINT>(sp) >= m_values.size(), IndexError,
			"Virtual Subpoplation index out of range of 0 ~ "
			+ toStr(m_values.size() - 1));
		return m_info + " = " + toStr(m_values[sp]);
	} else {
		DBG_FAILIF(static_cast<UINT>(sp) >= m_ranges.size(), IndexError,
			"Virtual Subpoplation index out of range of 0 ~ "
			+ toStr(m_ranges.size() - 1));
		return toStr(m_ranges[sp][0]) + " <= " + m_info + " < "
		       + toStr(m_ranges[sp][1]);
	}
}


proportionSplitter::proportionSplitter(vectorf const & proportions)
	: vspSplitter(), m_proportions(proportions)
{
	DBG_ASSERT(fcmp_eq(std::accumulate(proportions.begin(),
				proportions.end(), 0.), 1.), ValueError,
		"Passed proportions should add up to one");
}


ULONG proportionSplitter::size(const population & pop, SubPopID subPop, SubPopID virtualSubPop) const
{
	if (virtualSubPop == InvalidSubPopID)
		return countVisibleInds(pop, subPop);
	DBG_FAILIF(static_cast<UINT>(virtualSubPop) >= m_proportions.size(), IndexError,
		"Virtual subpopulation index out of range");
	//
	if (static_cast<UINT>(virtualSubPop) < m_proportions.size() - 1)
		return static_cast<ULONG>(pop.subPopSize(subPop) * m_proportions[virtualSubPop]);
	// to avoid floating point problem, the last subpop is specially treated
	ULONG size = pop.subPopSize(subPop);
	ULONG spSize = size;
	// virtualSubPop == m_proportions.size() - 1
	for (int i = 0; i < virtualSubPop; ++i)
		spSize -= static_cast<ULONG>(size * m_proportions[i]);
	return spSize;
}


UINT proportionSplitter::numVirtualSubPop()
{
	return m_proportions.size();
}


bool proportionSplitter::contains(const population & pop, ULONG ind, vspID vsp)
{
	DBG_FAILIF(static_cast<UINT>(vsp.virtualSubPop()) >= m_proportions.size(), IndexError,
		"Virtual subpopulation index out of range");

	ULONG size = pop.subPopSize(vsp.subPop());
	ULONG lower = 0;
	ULONG higher = 0;
	for (UINT sp = 0; sp < m_proportions.size(); ++sp) {
		if (static_cast<UINT>(sp) + 1 < m_proportions.size())
			higher += static_cast<ULONG>(size * m_proportions[sp]);
		else
			higher = size;
		if (ind >= lower && ind < higher)
			return vsp.virtualSubPop() == static_cast<int>(sp);
		lower = higher;
	}
	return false;
}


void proportionSplitter::activate(population & pop, SubPopID subPop, SubPopID virtualSubPop,
                                  IterationType type)
{
	DBG_FAILIF(static_cast<UINT>(virtualSubPop) >= m_proportions.size(), IndexError,
		"Virtual subpopulation index out of range");

	ULONG size = pop.subPopSize(subPop);
	ULONG spSize = static_cast<ULONG>(size * m_proportions[0]);
	ULONG spCount = 0;
	SubPopID sp = 0;
	SubPopID visibleSP = virtualSubPop;

	RawIndIterator it = pop.rawIndBegin(subPop);
	RawIndIterator it_end = pop.rawIndEnd(subPop);
	for (; it != it_end; ++it, ++spCount) {
		if (spCount == spSize) {
			++sp;
			if (static_cast<UINT>(sp) + 1 < m_proportions.size())
				spSize = static_cast<ULONG>(size * m_proportions[sp]);
			else
				// in the last virtual sp.
				// use a bigger size to make sure the last few
				// individuals are counted.
				spSize = size;
			spCount = 0;
		}
		if (type == VisibleInds)
			it->setVisible(sp == visibleSP);
		else
			it->setIteratable(sp == visibleSP);
	}
	if (type == VisibleInds)
		m_activated = subPop;
}


void proportionSplitter::deactivate(population & pop, SubPopID subPop)
{
	resetSubPop(pop, subPop);
}


string proportionSplitter::name(SubPopID subPop)
{
	DBG_FAILIF(static_cast<UINT>(subPop) >= m_proportions.size(), IndexError,
		"Virtual subpopulation index out of range");
	return "Prop " + toStr(m_proportions[subPop]);
}


rangeSplitter::rangeSplitter(const intMatrix & ranges)
	: vspSplitter(), m_ranges(ranges)
{
	for (size_t i = 0; i < m_ranges.size(); ++i) {
		DBG_FAILIF(m_ranges[i].size() != 2
			|| m_ranges[i][0] > m_ranges[i][1],
			ValueError, "Wrong range [" +
			toStr(m_ranges[i][0]) + ", " +
			toStr(m_ranges[i][1]) + ")");
	}
}


ULONG rangeSplitter::size(const population & pop, SubPopID subPop, SubPopID virtualSubPop) const
{
	if (virtualSubPop == InvalidSubPopID)
		return countVisibleInds(pop, subPop);
	DBG_FAILIF(static_cast<UINT>(virtualSubPop) >= m_ranges.size(), IndexError,
		"Virtual subpopulation index out of range");
	if (static_cast<UINT>(m_ranges[virtualSubPop][0]) > pop.subPopSize(subPop))
		return 0;
	if (static_cast<UINT>(m_ranges[virtualSubPop][1]) > pop.subPopSize(subPop))
		return pop.subPopSize(subPop) - m_ranges[virtualSubPop][0];
	return m_ranges[virtualSubPop][1] - m_ranges[virtualSubPop][0];
}


UINT rangeSplitter::numVirtualSubPop()
{
	return m_ranges.size();
}


bool rangeSplitter::contains(const population & pop, ULONG ind, vspID vsp)
{
	SubPopID virtualSubPop = vsp.virtualSubPop();

	return ind >= static_cast<ULONG>(m_ranges[virtualSubPop][0]) &&
	       ind < static_cast<ULONG>(m_ranges[virtualSubPop][1]);
}


void rangeSplitter::activate(population & pop, SubPopID subPop, SubPopID virtualSubPop,
                             IterationType type)
{
	DBG_FAILIF(static_cast<UINT>(virtualSubPop) >= m_ranges.size(), IndexError,
		"Virtual subpopulation index out of range");

	ULONG low = m_ranges[virtualSubPop][0];
	ULONG high = m_ranges[virtualSubPop][1];
	ULONG idx = 0;

	RawIndIterator it = pop.rawIndBegin(subPop);
	RawIndIterator it_end = pop.rawIndEnd(subPop);
	for (; it != it_end; ++it, ++idx)
		if (type == VisibleInds)
			it->setVisible(idx >= low && idx < high);
		else
			it->setIteratable(idx >= low && idx < high);
	if (type == VisibleInds)
		m_activated = subPop;
}


void rangeSplitter::deactivate(population & pop, SubPopID subPop)
{
	resetSubPop(pop, subPop);
}


string rangeSplitter::name(SubPopID subPop)
{
	DBG_FAILIF(static_cast<UINT>(subPop) >= m_ranges.size(), IndexError,
		"Virtual subpopulation index out of range");
	return "Range [" + toStr(m_ranges[subPop][0]) + ", " +
	       toStr(m_ranges[subPop][1]) + ")";
}


genotypeSplitter::genotypeSplitter(const uintList & loci,
	const intMatrix & alleles,
	bool phase)
	: vspSplitter(), m_loci(loci.elems()), m_alleles(alleles),
	m_phase(phase)
{
}


ULONG genotypeSplitter::size(const population & pop, SubPopID subPop, SubPopID virtualSubPop) const
{
	if (virtualSubPop == InvalidSubPopID)
		return countVisibleInds(pop, subPop);
	DBG_FAILIF(static_cast<UINT>(virtualSubPop) >= m_alleles.size(), IndexError,
		"Virtual subpopulation index out of range");
	const vectori & alleles = m_alleles[virtualSubPop];
	ULONG count = 0;
	ConstRawIndIterator it = pop.rawIndBegin(subPop);
	ConstRawIndIterator it_end = pop.rawIndEnd(subPop);
	for (; it != it_end; ++it)
		if (match(& * it, alleles))
			++count;
	return count;
}


UINT genotypeSplitter::numVirtualSubPop()
{
	return m_alleles.size();
}


bool genotypeSplitter::contains(const population & pop, ULONG ind, vspID vsp)
{
	SubPopID virtualSubPop = vsp.virtualSubPop();

	DBG_FAILIF(static_cast<UINT>(virtualSubPop) >= m_alleles.size(), IndexError,
		"Virtual subpopulation index out of genotype");

	const vectori & alleles = m_alleles[virtualSubPop];

	return match(&pop.ind(ind, vsp.subPop()), alleles);
}


void genotypeSplitter::activate(population & pop, SubPopID subPop, SubPopID virtualSubPop,
                                IterationType type)
{
	DBG_FAILIF(static_cast<UINT>(virtualSubPop) >= m_alleles.size(), IndexError,
		"Virtual subpopulation index out of genotype");

	const vectori & alleles = m_alleles[virtualSubPop];
	RawIndIterator it = pop.rawIndBegin(subPop);
	RawIndIterator it_end = pop.rawIndEnd(subPop);
	for (; it != it_end; ++it)
		if (type == VisibleInds)
			it->setVisible(match(& * it, alleles));
		else
			it->setIteratable(match(& * it, alleles));
	if (type == VisibleInds)
		m_activated = subPop;
}


void genotypeSplitter::deactivate(population & pop, SubPopID subPop)
{
	resetSubPop(pop, subPop);
}


//
// 1: 0 1
// 1: 0 1 1 1
// Two possibilities (depending on ploidy)
// 1, 2: 0 1 1 0 1 1 1 1
string genotypeSplitter::name(SubPopID subPop)
{
	DBG_FAILIF(static_cast<UINT>(subPop) >= m_alleles.size(), IndexError,
		"Virtual subpopulation index out of genotype");
	string label = "Genotype ";
	for (size_t i = 0; i < m_loci.size(); ++i) {
		if (i != 0)
			label += ", ";
		label += toStr(m_loci[i]);
	}
	label += ":";
	for (size_t i = 0; i < m_alleles[subPop].size(); ++i)
		label += " " + toStr(m_alleles[subPop][i]);
	return label;
}


bool genotypeSplitter::match(const individual * it, const vectori & alleles) const
{
	int ploidy = it->ploidy();
	int numLoci = m_loci.size();

	unsigned choices = alleles.size() / ploidy / numLoci;

	DBG_FAILIF(alleles.size() != choices * ploidy * numLoci,
		ValueError, "Given genotype does not match population ploidy.");

	for (unsigned t = 0; t < choices; ++t) {
		vectori partial(alleles.begin() + t * ploidy * numLoci,
		                alleles.begin() + (t + 1) * ploidy * numLoci);
		if (matchSingle(it, partial))
			return true;
	}
	return false;
}


bool genotypeSplitter::matchSingle(const individual * it, const vectori & alleles) const
{
	int ploidy = it->ploidy();

	if (m_phase || ploidy == 1) {
		// if phase=True, has to match exactly.
		UINT idx = 0;
		uintList::const_iterator loc = m_loci.begin();
		uintList::const_iterator loc_end = m_loci.end();
		for (; loc != loc_end; ++loc)
			for (int p = 0; p < ploidy; ++p)
				if (static_cast<int>(it->allele(*loc, p)) != alleles[idx++])
					return false;
		return true;
	} else if (ploidy == 2) {
		UINT idx = 0;
		uintList::const_iterator loc = m_loci.begin();
		uintList::const_iterator loc_end = m_loci.end();
		UINT numLoci = m_loci.size();
		for (; loc != loc_end; ++loc, ++idx) {
			int a1 = it->allele(*loc, 0);
			int a2 = it->allele(*loc, 1);
			int a3 = alleles[idx];
			int a4 = alleles[idx + numLoci];
			if (!((a1 == a3 && a2 == a4) || (a1 == a4 && a2 == a3)))
				return false;
		}
		return true;
	} else {
		UINT idx = 0;
		uintList::const_iterator loc = m_loci.begin();
		uintList::const_iterator loc_end = m_loci.end();
		UINT numLoci = m_loci.size();
		vectori v1(ploidy);
		vectori v2(ploidy);
		for (; loc != loc_end; ++loc, ++idx) {
			for (int p = 0; p < ploidy; ++p) {
				v1[p] = it->allele(*loc, p);
				v2[p] = alleles[idx + p * numLoci];
			}
			std::sort(v1.begin(), v1.end());
			std::sort(v2.begin(), v2.end());
			for (int p = 0; p < ploidy; ++p)
				if (v1[p] != v2[p])
					return false;
		}
		return true;
	}
	return false;
}


}     // namespce simuPOP

