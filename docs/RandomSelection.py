#!/usr/bin/env python

#
# $File: RandomSelection.py $
#
# This file is part of simuPOP, a forward-time population genetics
# simulation environment. Please visit http://simupop.sourceforge.net
# for details.
#
# Copyright (C) 2004 - 2010 Bo Peng (bpeng@mdanderson.org)
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#

# This script is an example in the simuPOP user's guide. Please refer to
# the user's guide (http://simupop.sourceforge.net/manual) for a detailed
# description of this example.
#

import simuPOP as sim
pop = sim.Population(100, ploidy=1, loci=[5, 5], ancGen=1,
    infoFields='parent_idx')
pop.evolve(
    initOps=sim.InitGenotype(freq=[0.3, 0.7]),
    matingScheme=sim.RandomSelection(ops=[
        sim.ParentsTagger(infoFields='parent_idx'),
        sim.CloneGenoTransmitter(),
    ]),
    gen = 5
)
ind = pop.individual(0)
par = pop.ancestor(ind.parent_idx, 1)
print(ind.sex(), ind.genotype())
print(par.sex(), par.genotype())
