/***************************************************************************
 *   Copyright (C) 2004 by Bo Peng                                         *
 *   bpeng@rice.edu                                                        *
 *                                                                         *
 *   $LastChangedDate: 2006-02-21 15:27:25 -0600 (Tue, 21 Feb 2006) $
 *   $Rev: 191 $
 *
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

#include "tagger.h"

namespace simuPOP
{
	bool inheritTagger::applyDuringMating(population& pop, population::IndIterator offspring,
		individual* dad, individual* mom)
	{
		UINT id1=0, id2=0;
		if (m_mode == TAG_Paternal)
			id1 = pop.infoIdx(infoField(0));
		else if (m_mode == TAG_Maternal)
			id1 = pop.infoIdx(infoField(1));
		else
		{
			id1 = pop.infoIdx(infoField(0));
			id2 = pop.infoIdx(infoField(1));
		}

		if( m_mode == TAG_Paternal)
		{
			if (dad == NULL)
				offspring->setInfo(0, id1);
			else
				offspring->setInfo(dad->info(id1), id1);
		}
		else if( m_mode == TAG_Maternal)
		{
			if (mom == NULL)
				offspring->setInfo(0, id1);
			else
				offspring->setInfo(mom->info(id1), id1);
		}
		else
		{
			if( dad == NULL )
				offspring->setInfo(0, id1);
			else
				offspring->setInfo(dad->info(id1), id1);
			if( mom == NULL)
				offspring->setInfo(0, id2);
			else
				offspring->setInfo(mom->info(id2), id2);
		}
		return true;
	}

	bool parentsTagger::applyDuringMating(population& pop, population::IndIterator offspring,
		individual* dad, individual* mom)
	{
		UINT id1 = pop.infoIdx(infoField(0));
		UINT id2 = pop.infoIdx(infoField(1));

		if(dad == NULL)
			offspring->setInfo(0, id1);
		else
			offspring->setInfo(dad - &*pop.indBegin(), id1);

		if( mom == NULL)
			offspring->setInfo(0, id2);
		else
			offspring->setInfo(mom - &*pop.indBegin(), id2);

		return true;
	}

}