#!/usr/bin/env python
#
# Purpose:
#
# This is a unittest file for population object
#
# Bo Peng (bpeng@rice.edu)
#
# $LastChangedRevision$
# $LastChangedDate$
#

import simuOpt
#simuOpt.setOptions(quiet=True)

from simuPOP import *
import unittest, os, sys, exceptions, random

class TestPopulation(unittest.TestCase):

    def assertGenotype(self, pop, subPop, genotype):
        'Assert if the genotype of subPop of pop is genotype '
        gt = list(pop.arrGenotype(subPop, True))
        gt.sort()
        if AlleleType() == 'binary':
            self.assertEqual(gt, [x>0 for x in genotype])
        else:
            self.assertEqual(gt, genotype)

    def testNewPopulation(self):
        'Testing the creation of populations'
        self.assertRaises(exceptions.ValueError,
            [1,2,4,5].index, 6)
        # no exception '
        if AlleleType() == 'binary':
            population(size=[20,80], ploidy=2, loci=[5, 7],
                lociPos=[ [2,3,4,5,6],[2,4,6,8,10,12,14]],
                maxAllele=1, alleleNames=['_','A','C','T','G'])
        else:
            population(size=[20,80], ploidy=2, loci=[5, 7],
                lociPos=[ [2,3,4,5,6],[2,4,6,8,10,12,14]],
                maxAllele=4, alleleNames=['_','A','C','T','G'])
        # raise exception when max allele is wrong
        # MaxAllele may be too big.
        self.assertRaises( (exceptions.TypeError, exceptions.ValueError, exceptions.OverflowError),
            population, size=10, maxAllele=MaxAllele()+1)
        # raise exception when ploidy value is wrong
        self.assertRaises(exceptions.ValueError,
            population, size=[20,20], ploidy=0)
        # raise exceptions with negative values
        self.assertRaises((exceptions.TypeError, exceptions.OverflowError),
            population, size=-10)
        self.assertRaises((exceptions.TypeError, exceptions.OverflowError),
            population, size=[-10])
        self.assertRaises((exceptions.ValueError, exceptions.OverflowError),
            population, ploidy=-1)
        # lociDist is depreciated
        self.assertRaises(exceptions.TypeError,
            population, loci=[2], lociDist=[1,2])
        # loci distance in order.
        self.assertRaises(exceptions.ValueError,
            population, loci=[2], lociPos=[3,2])
        # loci distance is in order.
        population(loci=[2,3], lociPos=[1,2,3,5,6])
        # loci distance can be given in another form
        population(loci=[2,3], lociPos=[[1,2],[3,5,6]])
        # but not if number mismatch
        self.assertRaises(exceptions.ValueError,
            population, loci=[2,3], lociPos=[[1,2,3], [8,9]])
        # size mismatch
        self.assertRaises(exceptions.ValueError,
            population, loci=[2], lociPos=[1,2,3])
        self.assertRaises(exceptions.ValueError,
            population, loci=[2], lociPos=[1])
        # loci names
        self.assertRaises(exceptions.ValueError,
            population, loci=[2], lociNames=['1', '2' , '3'])
        # allele names, should only gives warning
        population(10, alleleNames=['_'])
        population(10, maxAllele=1, alleleNames=['A', 'B'])
        # sex chrom, 2 does not trigger type error
        p = population(loci=[2], sexChrom=2)
        self.assertEqual( p.sexChrom(), True)
        p = population(loci=[2], sexChrom=False)
        self.assertEqual( p.sexChrom(), False)
        # default population size is 0
        p = population()
        self.assertEqual( p.popSize(), 0)
        self.assertEqual( p.subPopSize(0), 0)
        self.assertEqual( p.sexChrom(), False)
        # ancestral depth
        p = population(ancestralDepth=-1)
        p = population(ancestralDepth=5)
        # max allele can not be zero
        self.assertRaises(exceptions.ValueError,
            population, maxAllele=0)

    def testGenoStructure(self):
        'Testing geno structure related functions'
        if AlleleType() != 'binary':
            pop = population(size=[20,80], ploidy=2, loci=[5, 7],
                lociPos=[ [2,3,4,5,6],[2,4,6,8,10,12,14]],
                maxAllele=3, chromNames=["ch1", "ch2"],
                alleleNames=['A','C','T','G'])
        else:
            pop = population(size=[20,80], ploidy=2, loci=[5, 7],
                lociPos=[ [2,3,4,5,6],[2,4,6,8,10,12,14]],
                chromNames=["ch1", "ch2"], alleleNames=['1','2'])
        #
        self.assertEqual(pop.ploidy(), 2)
        self.assertEqual(pop.ploidyName(), 'diploid')
        self.assertEqual(pop.haplodiploid(), False)
        #
        self.assertEqual(pop.numChrom(), 2)
        self.assertEqual(pop.chromName(0), "ch1")
        self.assertEqual(pop.chromName(1), "ch2")
        self.assertEqual(pop.chromByName("ch2"), 1)
        self.assertRaises(exceptions.ValueError, pop.chromByName, "ch3")
        self.assertRaises(exceptions.IndexError, pop.chromName, 2)
        #
        self.assertEqual(pop.numLoci(0), 5)
        self.assertEqual(pop.numLoci(1), 7)
        self.assertRaises(exceptions.IndexError, pop.numLoci, 2 )
        #
        self.assertEqual(pop.locusPos(10), 12)
        self.assertRaises(exceptions.IndexError, pop.locusPos, 20 )
        self.assertRaises((exceptions.TypeError, exceptions.OverflowError), pop.locusPos, -1 )
        # more use of arr.. please see test_00_carray
        self.assertEqual(len(pop.arrLociPos()), 12)
        self.assertEqual(pop.arrLociPos().tolist(), [2,3,4,5,6,2,4,6,8,10,12,14])
        #
        self.assertEqual(pop.chromBegin(0), 0)
        self.assertEqual(pop.chromBegin(1), 5)
        self.assertEqual(pop.chromEnd(0), 5)
        self.assertEqual(pop.chromEnd(1), 12)
        self.assertRaises(exceptions.IndexError, pop.chromBegin, 2 )
        self.assertRaises(exceptions.IndexError, pop.chromEnd, 2 )
        #
        self.assertEqual(pop.absLocusIndex(1,5), 10)
        self.assertEqual(pop.locusPos(pop.absLocusIndex(1,2) ), 6)
        self.assertRaises(exceptions.IndexError, pop.absLocusIndex, 2, 5 )
        #
        self.assertEqual(pop.chromLocusPair(10), (1,5) )
        self.assertRaises(exceptions.IndexError, pop.chromLocusPair, 50 )
        #
        self.assertEqual(pop.totNumLoci(), 12)
        #
        self.assertEqual(pop.genoSize(), pop.totNumLoci()*pop.ploidy() )
        #
        if AlleleType() == 'binary':
            self.assertEqual(pop.alleleNames(), ('1','2') )
            self.assertEqual(pop.alleleName(0), '1')
            self.assertEqual(pop.alleleName(1), '2')
            self.assertRaises(exceptions.IndexError, pop.alleleName, 5)
        else:
            self.assertEqual(pop.alleleName(0), 'A')
            self.assertEqual(pop.alleleName(1), 'C')
            self.assertEqual(pop.alleleName(2), 'T')
            self.assertEqual(pop.alleleName(3), 'G')
            self.assertRaises(exceptions.IndexError, pop.alleleName, 4)
        # loci name, default, the name will be used by other programs
        # or file format, so we set it to be one based.
        self.assertEqual(pop.locusName(0), 'loc1-1')
        self.assertEqual(pop.locusName(1), 'loc1-2')
        self.assertEqual(pop.locusName(5), 'loc2-1')
        pop = population(loci=[1,2], lociNames=['la','lb','lc'])
        self.assertEqual(pop.locusName(0), 'la')
        self.assertEqual(pop.locusName(1), 'lb')
        self.assertEqual(pop.locusName(2), 'lc')
        self.assertRaises(exceptions.IndexError, pop.locusName, 5)

    def testHaplodiploid(self):
        'Testing haplodiploid populations'
        pop = population(size=100, ploidy=Haplodiploid, loci=[5, 7])
        self.assertEqual(pop.ploidy(), 2)
        self.assertEqual(pop.ploidyName(), 'haplodiploid')
        self.assertEqual(pop.haplodiploid(), True)


    def testPopProperties(self):
        'Testing population properties'
        if AlleleType() != 'binary':
            pop = population(size=[20,80], ploidy=2, loci=[5, 7],
                lociPos=[ [2,3,4,5,6],[2,4,6,8,10,12,14]],
                maxAllele=4, alleleNames=['_','A','C','T','G'])
        else:
            pop = population(size=[20,80], ploidy=2, loci=[5, 7],
                lociPos=[ [2,3,4,5,6],[2,4,6,8,10,12,14]],
                alleleNames=['1','2'])
        #
        self.assertEqual(pop.popSize(), 100)
        #
        self.assertEqual(pop.subPopSize(0), 20)
        self.assertEqual(pop.subPopSize(1), 80)
        self.assertRaises(exceptions.IndexError, pop.subPopSize, 2 )
        #
        self.assertEqual(pop.subPopSizes(), (20,80) )
        #
        self.assertEqual(pop.subPopBegin(1), 20)
        self.assertRaises(exceptions.IndexError, pop.subPopBegin, 2 )
        self.assertEqual(pop.subPopEnd(0), 20)
        self.assertRaises(exceptions.IndexError, pop.subPopEnd, 2 )
        #
        self.assertEqual(pop.numSubPop(), 2)
        #
        # ind, subPop
        self.assertEqual(pop.absIndIndex(1,1), 21)
        self.assertRaises(exceptions.IndexError, pop.absIndIndex, 0, 2 )
        #
        self.assertEqual(pop.subPopIndPair(21), (1,1) )
        self.assertRaises(exceptions.IndexError, pop.subPopIndPair, 200 )

    def testLociPos(self):
        'Testing loci position related functions'
        pop = population(loci=[5, 7],
                lociPos=[ [2,3,4,5,6],[2,4,6,8,10,12,14]])
        self.assertEqual(pop.lociDist(0, 3), 3)
        self.assertEqual(pop.lociDist(2, 4), 2)
        self.assertRaises(exceptions.ValueError, pop.lociDist, 2, 8)
        #
        self.assertEqual(pop.lociCovered(1, 2.2), 3)
        self.assertEqual(pop.lociCovered(1, 5.2), 4)
        self.assertEqual(pop.lociCovered(7, 0.2), 1)
        self.assertEqual(pop.lociCovered(7, 2.2), 2)
        self.assertEqual(pop.lociCovered(7, 6.5), 4)
        #
        self.assertEqual(pop.lociLeft(2), 3)
        self.assertEqual(pop.lociLeft(4), 1)
        self.assertEqual(pop.lociLeft(5), 7)
        self.assertEqual(pop.lociLeft(11), 1)
        #
        self.assertEqual(pop.distLeft(2), 2)
        self.assertEqual(pop.distLeft(4), 0)
        self.assertEqual(pop.distLeft(5), 12)
        self.assertEqual(pop.distLeft(11), 0)


    def testIterator(self):
        'Testing the individual iterators'
        pop = population(loci=[1], size=[4,6])
        for ind in pop.individuals():
            ind.setAllele(1, 0)
        for ind in pop.individuals(1):
            ind.setAllele(2, 0)
        for ind in pop.individuals(0):
            self.assertEqual(ind.allele(0), 1)
        if AlleleType() == 'binary':
            for ind in pop.individuals(1):
                self.assertEqual(ind.allele(0), 1)
        else:
            for ind in pop.individuals(1):
                self.assertEqual(ind.allele(0), 2)

    def testSetSubPopStru(self):
        'Testing function setSubPopStru'
        pop = population(size=1, loci=[1])
        # pop1 is only a reference to pop
        pop1 = pop
        pop.individual(0).setAllele(1,0)
        # the genotype of pop1 is also changed
        self.assertEqual( pop1.individual(0).allele(0), 1)
        pop2 = pop.clone()
        pop.individual(0).setAllele(0,0)
        # pop2 does not change with pop
        self.assertEqual( pop2.individual(0).allele(0), 1)
        #
        pop = population(size=10)
        self.assertEqual( pop.subPopSizes(), (10,) )
        pop.setSubPopStru(newSubPopSizes=[2,8])
        self.assertEqual( pop.subPopSizes(), (2,8) )
        # can set empty subpop
        pop.setSubPopStru(newSubPopSizes=[0,0,1,0,2,7,0])
        self.assertEqual( pop.subPopSizes(), (0,0,1,0,2,7,0) )
        # by default, can not change population size
        self.assertRaises(exceptions.ValueError,
            pop.setSubPopStru, newSubPopSizes=[10,20])
        # can change population size if allow... is set to True
        #
        pop = population(size=10, infoFields=['age'])
        pop.individual(1).setInfo(1, 'age')
        self.assertEqual(pop.individual(1).info('age'), 1)
        self.assertEqual(pop.individual(1).info('age'), 1)
        self.assertEqual(pop.individual(1).info('age'), 1)
        pop.setIndInfo(range(10), 'age')
        self.assertEqual(pop.individual(0).info('age'), 0)
        #print pop.indInfo('age')
        pop.setSubPopStru(newSubPopSizes=[2,8])
        for i in range(10):
            self.assertEqual(pop.individual(i).info('age'), i)


    def testPopSwap(self):
        'Testing population swap'
        pop = population(10, loci=[2])
        pop1 = population(5, loci=[3])
        InitByFreq(pop, [.2,.3,.5])
        InitByFreq(pop1, [.2,.3,.5])
        popa = pop.clone()
        pop1a = pop1.clone()
        pop1.swap(pop)
        self.assertEqual( pop, pop1a)
        self.assertEqual( pop1, popa)
        # test if info is swapped
        pop = population(10, infoFields=['age'])
        pop.setIndInfo(range(10), 'age')
        pop1 = population(5, infoFields=['fitness'])
        pop1.setIndInfo(range(10,15), 'fitness')
        pop.swap(pop1)
        self.assertEqual(pop.infoField(0), 'fitness')
        self.assertEqual(pop1.infoField(0), 'age')
        for i in range(5):
            self.assertEqual(pop.individual(i).info('fitness'), i+10)
        for i in range(10):
            self.assertEqual(pop1.individual(i).info('age'), i)
        ###
        ###  ARRINDINFO is only valid for head node.
        ###
##         self.assertEqual(pop.arrIndInfo(), range(10,15))
##         self.assertEqual(pop1.arrIndInfo(), range(10))
        self.assertEqual(pop.popSize(), 5)
        self.assertEqual(pop1.popSize(), 10)

    def testSplitSubPop(self):
        'Testing function splitSubPop'
        pop = population(size=[5,6,7], ploidy=1, loci=[1])
        arr = pop.arrGenotype(True)
        # mapArr is separate
        mapArr = list(arr)
        mapArr = range(pop.popSize())
        arr[:] = mapArr
        # split, the additional subpop will be put at the end
        # member function form
        pop.splitSubPop(1, [2,4])
        self.assertEqual(pop.subPopSizes(), (5,2,7,4) )
        # check if 7,8,9,10 is moved to subpopulation 3.
        # underlying genotype will *not* be sorted
        self.assertGenotype(pop, 0, [0,1,2,3,4])
        self.assertGenotype(pop, 1, [5,6])
        self.assertGenotype(pop, 2, [11,12,13,14,15,16,17])
        self.assertGenotype(pop, 3, [7,8,9,10])
        #, 5,6, 11,12,13,14,15,16,17, 7,8,9,10])
        #
        # recover population
        pop.setSubPopStru([5,6,7])
        pop.arrGenotype(True)[:] = range(pop.popSize())
        # function form
        SplitSubPop(pop, 1, [2,4], subPopID=[4,1], randomize=False)
        self.assertEqual(pop.subPopSizes(), (5,4,7,0,2))
        self.assertGenotype(pop, 0, [0,1,2,3,4])
        self.assertGenotype(pop, 1, [7,8,9,10])
        self.assertGenotype(pop, 2, [11,12,13,14,15,16,17])
        self.assertGenotype(pop, 3, [])
        self.assertGenotype(pop, 4, [5,6])
        # given wrong split size?
        self.assertRaises(exceptions.ValueError,
            SplitSubPop, pop, 1, [2,4], subPopID=[4,1])
        # if given subPopID is already used?
        print "A warning should be issued"
        SplitSubPop(pop, 0, [2,3], subPopID=[2,3])

    def testSplitSubPopByProportion(self):
        'Testing function splitSubPopByProportion'
        # split by proportion --------
        pop = population(size=[5,6,7], ploidy=1, loci=[1])
        arr = pop.arrGenotype(True)
        # mapArr is separate
        mapArr = list(arr)
        mapArr = range(pop.popSize())
        arr[:] = mapArr
        # step 1, split, the additional subpop will be put at the end
        pop.splitSubPopByProportion(1, [2/5.,3/5.])
        self.assertEqual(pop.subPopSizes(), (5,2,7,4) )
        # check if 7,8,9,10 is moved to subpopulation 3.
        # underlying genotype will *not* be sorted
        self.assertGenotype(pop, 0, [0,1,2,3,4])
        self.assertGenotype(pop, 1, [5,6])
        self.assertGenotype(pop, 2, [11,12,13,14,15,16,17])
        self.assertGenotype(pop, 3, [7,8,9,10])
        #
        # recover population
        pop.setSubPopStru([5,6,7])
        pop.arrGenotype(True)[:] = range(pop.popSize())
        SplitSubPop(pop, 1, proportions=[2/5.,3/5.], subPopID=[4,1], randomize=False)
        self.assertEqual(pop.subPopSizes(), (5,4,7,0,2))
        self.assertGenotype(pop, 0, [0,1,2,3,4])
        self.assertGenotype(pop, 1, [7,8,9,10])
        self.assertGenotype(pop, 2, [11,12,13,14,15,16,17])
        self.assertGenotype(pop, 3, [])
        self.assertGenotype(pop, 4, [5,6])
        # proportion does not add up to one?
        self.assertRaises(exceptions.ValueError,
            SplitSubPop, pop, 1, proportions=[2/3.,2/3.], subPopID=[4,1])
        # if given subPopID is already used?
        print "A warning should be issued"
        SplitSubPop(pop, 0, proportions=[2/5.,3/5.], subPopID=[2,3])
        #
        # split by proportion

    def testRemoveSubPops(self):
        'Testing function removeEmptySubPops, removeSubPops'
        pop = population(size=[0,1,0,2,3,0])
        self.assertEqual( pop.numSubPop(), 6)
        pop.removeEmptySubPops()
        self.assertEqual( pop.numSubPop(), 3)
        # remove subpop
        pop = population(size=[0,1,0,2,3,0], ploidy=1, loci=[1])
        arr = pop.arrGenotype(True)
        # mapArr is separate
        arr[:] = range(pop.popSize())
        pop.removeSubPops([1,2])
        self.assertEqual( pop.subPopSizes(), (0,2,3,0))
        # subpop will be shifted
        self.assertGenotype(pop, 0, [])
        self.assertGenotype(pop, 1, [1,2])
        self.assertGenotype(pop, 2, [3,4,5])
        self.assertGenotype(pop, 3, [])
        #
        pop.removeSubPops([2], shiftSubPopID=False)
        self.assertEqual( pop.subPopSizes(), (0,2,0,0))
        # subpop will be shifted
        self.assertGenotype(pop, 0, [])
        self.assertGenotype(pop, 1, [1,2])
        self.assertGenotype(pop, 2, [])
        self.assertGenotype(pop, 3, [])
        # should give warning
        print "A warning should be issued"
        pop.removeSubPops([8])
        # see if remove subPOp change info
        pop = population(size=[2,4,5], infoFields=['age'])
        self.assertEqual( pop.numSubPop(), 3)
        pop.setIndInfo(range(11), 0)
##         self.assertEqual(pop.arrIndInfo(), range(11))
        pop.removeSubPops([1])
##         self.assertEqual(pop.arrIndInfo(0, True), range(2))
##         self.assertEqual(pop.arrIndInfo(1, True), range(6,11))

    def testRemoveIndividuals(self):
        'Testing function removeIndividuals'
        pop = population(size=[0,1,0,2,3,0], ploidy=1, loci=[1])
        arr = pop.arrGenotype(True)
        arr[:] = range(pop.popSize())
        #
        pop.removeIndividuals([2])
        self.assertEqual( pop.subPopSizes(), (0,1,0,1,3,0))
        # subpop will be shifted
        self.assertGenotype(pop, 0, [])
        self.assertGenotype(pop, 1, [0])
        self.assertGenotype(pop, 2, [])
        self.assertGenotype(pop, 3, [1])
        self.assertGenotype(pop, 4, [3,4,5])
        #
        pop.removeIndividuals([1], removeEmptySubPops=True)
        self.assertEqual( pop.subPopSizes(), (1,3))
        # subpop will be shifted
        self.assertGenotype(pop, 0, [0])
        self.assertGenotype(pop, 1, [3,4,5])
        # see if remove individual change info
        pop = population(size=[2,4,5], infoFields=['age'])
        pop.setIndInfo(range(11), 0)
        pop.removeIndividuals([2,3,4,5])
        self.assertEqual(pop.subPopSizes(), (2,0,5))
##         self.assertEqual(pop.arrIndInfo(0, True), range(2))
##         self.assertEqual(pop.arrIndInfo(2, True), range(6,11))
        # nothing in the middle left
##         self.assertEqual(pop.arrIndInfo(), range(2) + range(6,11))


    def testMergeSubPops(self):
        'Testing function mergeSubPops'
        pop = population(size=[0,1,0,2,3,0], ploidy=1, loci=[1])
        arr = pop.arrGenotype(True)
        arr[:] = range(pop.popSize())
        #
        pop.mergeSubPops([1,2,4])
        self.assertEqual( pop.subPopSizes(), (0,4,0,2,0,0))
        # subpop will be shifted
        self.assertGenotype(pop, 0, [])
        self.assertGenotype(pop, 1, [0,3,4,5])
        self.assertGenotype(pop, 2, [])
        self.assertGenotype(pop, 3, [1,2])
        self.assertGenotype(pop, 4, [])
        self.assertGenotype(pop, 5, [])
        #
        pop.mergeSubPops([1,2,3], removeEmptySubPops=True)
        self.assertEqual( pop.subPopSizes(), (6,))
        # subpop will be shifted
        self.assertGenotype(pop, 0, [0,1,2,3,4,5])
        # see if merging affect individual id.
        pop = population(size=[2,4,5], infoFields=['age'])
        pop.setIndInfo(range(11), 0)
        pop.mergeSubPops([0,2], removeEmptySubPops=True)
        self.assertEqual(pop.subPopSizes(), (7,4))
        # the order may be different
##         self.assertEqual(sum(pop.arrIndInfo(0, False)), sum(range(2)+range(6,11)))
##         self.assertEqual(pop.arrIndInfo(1, True), range(2,6))


    def testReorderSubPops(self):
        'Testing function reorderSubPops'
        pop = population(size=[1,2,3,4], ploidy=1, loci=[1])
        arr = pop.arrGenotype(True)
        arr[:] = range(pop.popSize())
        #
        pop.reorderSubPops(order=[1,3,0,2])
        self.assertEqual( pop.subPopSizes(), (2,4,1,3))
        # subpop will be shifted
        self.assertGenotype(pop, 0, [1,2])
        self.assertGenotype(pop, 1, [6,7,8,9])
        self.assertGenotype(pop, 2, [0])
        self.assertGenotype(pop, 3, [3,4,5])
        # by rank
        pop = population(size=[1,2,3,4], ploidy=1, loci=[1])
        arr = pop.arrGenotype(True)
        arr[:] = range(pop.popSize())
        #
        pop.reorderSubPops(rank=[1,3,0,2])
        self.assertEqual( pop.subPopSizes(), (3,1,4,2))
        # subpop will be shifted
        self.assertGenotype(pop, 0, [3,4,5])
        self.assertGenotype(pop, 1, [0])
        self.assertGenotype(pop, 2, [6,7,8,9])
        self.assertGenotype(pop, 3, [1,2])
        # reorder does not change info
        pop = population(size=[1,2,3,4], ploidy=1, loci=[1], infoFields=['age'])
        pop.setIndInfo(range(10), 'age')
        #
        pop.reorderSubPops(rank=[1,3,0,2])
        self.assertEqual( pop.subPopSizes(), (3,1,4,2))
        newInfoSums = [sum([3,4,5]), sum([0]), sum([6,7,8,9]), sum([1,2])]
##         for i in range(4):
##             self.assertEqual(sum(pop.arrIndInfo(i, True)), newInfoSums[i])


    def testNewPopByIndID(self):
        'Testing function newPopByIndInfo'
        pop = population(size=[1,2,3,4], ploidy=1, loci=[1])
        arr = pop.arrGenotype(True)
        arr[:] = range(pop.popSize())
        oldPop = pop.clone()
        #
        pop1 = pop.newPopByIndID(id=[-1,0,1,1,2,1,1,2,-1,0])
        self.assertEqual( pop, oldPop)
        self.assertEqual( pop1.subPopSizes(), (2,4,2))
        # subpop will be shifted
        self.assertGenotype(pop1, 0, [1,9])
        self.assertGenotype(pop1, 1, [2,3,5,6])
        self.assertGenotype(pop1, 2, [4,7])
        # change new pop will be change old one
        pop1.individual(0).setAllele(1, 0)
        self.assertNotEqual(pop.individual(0).allele(0), 1)
        # does new pop keeps info
        pop = population(size=[1,2,3,4], ploidy=1, loci=[1], infoFields=['age'])
        pop.setIndInfo(range(10),'age')
        pop1 = pop.newPopByIndID(id=[-1,8,7,6,5,4,3,2,1,-1], removeEmptySubPops=True)
        self.assertEqual(pop1.popSize(), 8)
        self.assertEqual(pop1.subPopSizes(), tuple([1]*8))
        for i in range(8):
            self.assertEqual(pop1.individual(i).info('age'), 8-i)


    def testRemoveLoci(self):
        'Testing function removeLoci'
        # FIXME: make sure to test a case when
        # genotype has to be moved from one node to another
        # in the MPI modules
        pop = population(size=[1,2], ploidy=2, loci=[2,3,1])
        arr = pop.arrGenotype(True)
        arr[:] = range(pop.totNumLoci())*(pop.popSize()*pop.ploidy())
        pop.removeLoci(remove=[2])
        self.assertEqual( pop.numChrom(), 3)
        self.assertEqual( pop.numLoci(0), 2)
        self.assertEqual( pop.numLoci(1), 2)
        self.assertEqual( pop.numLoci(2), 1)
        self.assertEqual( pop.arrGenotype(True).count(2), 0)
        pop.removeLoci(remove=[4])
        self.assertEqual( pop.numChrom(), 2)
        self.assertEqual( pop.numLoci(0), 2)
        self.assertEqual( pop.numLoci(1), 2)
        self.assertEqual( pop.arrGenotype(True).count(5), 0)
        # keep
        pop.removeLoci(keep=[1,2])
        self.assertEqual( pop.numChrom(), 2)
        self.assertEqual( pop.numLoci(0), 1)
        self.assertEqual( pop.numLoci(1), 1)
        if AlleleType() == 'binary':
            self.assertEqual( pop.arrGenotype(True).count(3), 0 )
            self.assertEqual( pop.arrGenotype(True).count(1), pop.popSize()*pop.ploidy()*2 )
        else:
            self.assertEqual( pop.arrGenotype(True).count(3), pop.popSize()*pop.ploidy() )
            self.assertEqual( pop.arrGenotype(True).count(1), pop.popSize()*pop.ploidy() )

    def testArrGenotype(self):
        'Testing function arrGenotype'
        pop = population(loci=[1,2], size=[1,2])
        arr = pop.arrGenotype(True)
        self.assertEqual( len(arr), pop.genoSize()*pop.popSize())
        arr = pop.arrGenotype(1, True)
        self.assertEqual( len(arr), pop.genoSize()*pop.subPopSize(1))
        arr[0] = 1
        self.assertEqual( pop.individual(0,1).allele(0), 1)
        self.assertRaises(exceptions.IndexError,
            pop.arrGenotype, 2, True)
        # arr assignment
        arr[:] = 1
        self.assertEqual( pop.individual(0,0).arrGenotype(), [0]*pop.genoSize())
        self.assertEqual( pop.individual(0,1).arrGenotype(), [1]*pop.genoSize())
        self.assertEqual( pop.individual(1,1).arrGenotype(), [1]*pop.genoSize())

    def testCompare(self):
        'Testing population comparison'
        pop = population(10, loci=[2])
        pop1 = population(10, loci=[2])
        self.assertEqual( pop == pop1, True)
        pop.individual(0).setAllele(1, 0)
        self.assertEqual( pop == pop1, False)
        pop1 = population(10, loci=[3])
        pop1.individual(0).setAllele(1, 0)
        # false becase of geno structure difference.
        self.assertEqual( pop == pop1, False)


    def testPopInfo(self):
        'Testing info-related functions'
        # create a population without info field
        pop = population(10)
        ind = pop.individual(0)
        self.assertRaises(exceptions.IndexError, ind.info, 0)
        # give name
        self.assertRaises(exceptions.ValueError, population, infoFields='age')
        pop = population(10, infoFields=['age'])
        self.assertEqual(pop.infoField(0), 'age')
        self.assertEqual(pop.infoFields(), ('age',))
        ind = pop.individual(0)
        self.assertRaises(exceptions.IndexError, ind.info, 1)
        # can set more names
        pop = population(10, infoFields=['age', 'fitness', 'trait1'])
        self.assertEqual(pop.infoField(0), 'age')
        self.assertEqual(pop.infoField(2), 'trait1')
        self.assertRaises(exceptions.IndexError, pop.infoField, 3)
        self.assertEqual(pop.infoFields(), ('age', 'fitness', 'trait1'))
        # can set and read each info
        pop.setIndInfo(range(10), 0)
        pop.setIndInfo(range(10,20), 1)
        pop.setIndInfo(range(20,30), 2)
        self.assertRaises(exceptions.IndexError, pop.setIndInfo, range(30,40), 3)
        for i in range(3):
            for j in range(10):
                self.assertEqual(pop.individual(j).info(i), i*10+j)
        ind = pop.individual(0)
        self.assertEqual(ind.arrInfo(), (0,10,20))
##         self.assertEqual(pop.arrIndInfo()[:8], (0,10,20,1,11,21,2,12))
##         self.assertEqual(pop.arrIndInfo(0, True)[:8], (0,10,20,1,11,21,2,12))
##         self.assertRaises(exceptions.IndexError, pop.arrIndInfo, 1, True)
        # access by name
        #pop.setIndInfo(range(30,40), 'sex')
##         #pop.arrIndInfo('sex')
        self.assertRaises(exceptions.IndexError, ind.info, 'sex')
        ind.setInfo(18, 'age')
        self.assertEqual(ind.info('age'), 18)
        #
        pop = population(10, infoFields=['age', 'fitness'])
        self.assertEqual(pop.hasInfoField('age'), True)
        self.assertEqual(pop.hasInfoField('fitness'), True)
        self.assertEqual(pop.hasInfoField('misc'), False)
        self.assertEqual(pop.infoFields(), ('age', 'fitness'))
        self.assertEqual(pop.infoSize(), 2)
        ind = pop.individual(0)
        # set info
        ind.setInfo(2, 0)
        self.assertEqual(ind.info('age'), 2)
        # get info
        self.assertEqual(ind.info(0), 2)
        # create another field
        self.assertEqual(pop.infoIdx('age'), 0)
        # set values
        pop.setIndInfo([1, 2,3,4,5,6,7,8,9,10], 0)
        for i in range(10):
            self.assertEqual(pop.individual(i).info(0), i+1)
        self.assertEqual(pop.infoIdx('fitness'), 1)
        # adding fitness should not interfere with age.
        for i in range(10):
            self.assertEqual(pop.individual(i).info(0), i+1)
        # set info by name
        pop = population(10, infoFields=['age', 'fitness'])
        #print pop.indInfo('fitness')
        #print pop.indInfo('age')
        for i in range(10):
            pop.individual(i).setInfo(i+50, 'fitness')
            self.assertEqual(pop.individual(i).info('fitness'), i+50)
        pop.setIndInfo(range(50,60), 'fitness')
        for i in range(10):
            pop.individual(i).setInfo(i+50, 'fitness')
            self.assertEqual(pop.individual(i).info('fitness'), i+50)
        #
        #  test indInfo
        pop = population(size=[4,6], infoFields=['age', 'fitness'])
        pop.setIndInfo(range(10), 'age')
        pop.setIndInfo(range(100, 110), 'fitness')
        self.assertEqual(pop.indInfo('age'), tuple([float(x) for x in range(10)]))
        self.assertEqual(pop.indInfo('fitness'), tuple([float(x) for x in range(100, 110)]))
        self.assertEqual(pop.indInfo('age', 1), tuple([float(x) for x in range(4, 10)]))
        self.assertEqual(pop.indInfo('fitness', 0), tuple([float(x) for x in range(100, 104)]))
        #
        # test reset info fields
        pop = population(size=10, infoFields=['age'])
        pop.setInfoFields(['age', 'fitness'])
        self.assertEqual(pop.infoSize(), 2)
        self.assertEqual(pop.infoFields(), ('age', 'fitness'))
        # set values
        pop.setIndInfo(range(10), 'age')
        pop.setIndInfo(range(100, 110), 'fitness')
        self.assertEqual(pop.indInfo('age'), tuple([float(x) for x in range(10)]))
        self.assertEqual(pop.indInfo('fitness'), tuple([float(x) for x in range(100, 110)]))
        # add an existing field
        pop.addInfoField('fitness')
        self.assertEqual(pop.infoSize(), 2)
        # add a new one.
        pop.addInfoField('misc')
        self.assertEqual(pop.infoSize(), 3)
        pop.setIndInfo(range(200, 210), 'fitness')
        self.assertEqual(pop.indInfo('age'), tuple([float(x) for x in range(10)]))
        self.assertEqual(pop.indInfo('fitness'), tuple([float(x) for x in range(200, 210)]))


    def testPopVars(self):
        'Testing population variables'
        # FIXME: currently variable is stored on all nodes.
        pop = population()
        self.assertEqual( pop.grp(), -1)
        self.assertEqual( pop.rep(), -1)
        # var will be copied?
        pop.dvars().x = 1
        pop1 = pop.clone()
        self.assertEqual( pop1.dvars().x, 1)
        pop1.dvars().y = 2
        self.assertEqual(pop.vars().has_key('y'), False)
        # test if a variable will be fully updated (a previous bug)
        # If a vector has 16 numbers, and then it will have a value
        # of 10 numbers, will the rest of the 6 numbers be removed?
        pop = population(1000, loci=[2,4])
        InitByFreq(pop, [.2, .3, .5])
        Stat(pop, alleleFreq=range(0,6))
        self.assertEqual(len(pop.dvars().alleleFreq), 6)
        pop.removeLoci(remove=[0,4])
        Stat(pop, alleleFreq=range(0,4))
        self.assertEqual(len(pop.dvars().alleleFreq), 4)

    def testAncestry(self):
        'Testing ancestral population related functions'
        pop = population(size=[3,5], loci=[2,3], ancestralDepth=2)
        InitByFreq(pop, [.2,.8])
        gt = list(pop.arrGenotype(True))
        self.assertEqual(pop.ancestralDepth(), 0)
        pop1 = population(size=[2,3], loci=[2,3], ancestralDepth=2)
        InitByFreq(pop1, [.8,.2])
        gt1 = list(pop1.arrGenotype(True))
        # can not do, because of different genotype
        pop.pushAndDiscard(pop1)
        # pop1 should be empty now
        self.assertEqual(pop1.popSize(), 0)
        # pop should have one ancestry
        self.assertEqual(pop.ancestralDepth(), 1)
        # genotype of pop should be pop1
        self.assertEqual(pop.arrGenotype(True), gt1)
        # use ancestry pop
        pop.useAncestralPop(1)
        self.assertEqual(pop.arrGenotype(True), gt)
        # use back
        pop.useAncestralPop(0)
        self.assertEqual(pop.arrGenotype(True), gt1)
        # can not push itself
        self.assertRaises(exceptions.ValueError,
            pop.pushAndDiscard, pop)
        # can not do, because of different genotype
        pop2 = population(size=[3,5], loci=[2])
        self.assertRaises(exceptions.ValueError,
            pop.pushAndDiscard, pop2)
        # [ gt1, gt ]
        # push more?
        pop2 = population(size=[3,5], loci=[2,3])
        InitByFreq(pop2, [.2,.8])
        gt2 = list(pop2.arrGenotype(True))
        pop3 = pop2.clone()
        pop.pushAndDiscard(pop2)
        # [ gt2, gt1, gt]
        # pop should have one ancestry
        self.assertEqual(pop2.popSize(), 0)
        self.assertEqual(pop.ancestralDepth(), 2)
        #
        self.assertEqual(pop.arrGenotype(True), gt2)
        pop.useAncestralPop(1)
        self.assertEqual(pop.arrGenotype(True), gt1)
        pop.useAncestralPop(2)
        self.assertEqual(pop.arrGenotype(True), gt)
        pop.useAncestralPop(0)
        #
        pop.pushAndDiscard(pop3)
        # [ gt2, gt2, gt1]
        self.assertEqual(pop3.popSize(), 0)
        self.assertEqual(pop.ancestralDepth(), 2)
        pop.useAncestralPop(1)
        self.assertEqual(pop.arrGenotype(True), gt2)
        pop.useAncestralPop(2)
        self.assertEqual(pop.arrGenotype(True), gt1)
        #
        # test if ind info is saved with ancestral populations
        pop = population(10, ancestralDepth=2, infoFields=['age', 'fitness'])
        pop.setIndInfo(range(10), 'age')
        pop.setIndInfo(range(10, 20), 'fitness')
        pop1 = population(20, infoFields=['age', 'fitness'])
        pop1.setIndInfo(range(100, 120), 'age')
        pop1.setIndInfo(range(110, 130), 'fitness')
        pop.pushAndDiscard(pop1)
        # test info
        self.assertEqual(pop.popSize(), 20)
##         self.assertEqual(pop.arrIndInfo()[:4], [100, 110, 101, 111])
        pop.useAncestralPop(1)
        self.assertEqual(pop.popSize(), 10)
##         self.assertEqual(pop.arrIndInfo()[:4], [0, 10, 1, 11])


    def testSaveLoadPopulation(self):
        'Testing save and load populations'
        if AlleleType() != 'binary':
            pop = population(size=[2,8], ploidy=2, loci=[5, 7],
                lociPos=[ [2,3,4,5,6],[2,4,6,8,10,12,14]],
                maxAllele=4, alleleNames=['_','A','C','T','G'],
                infoFields=['age', 'fitness'])
            InitByFreq(pop, [.2, .3, .5])
            pop.setIndInfo(range(10), 'age')
            pop.setIndInfo(range(100, 110), 'fitness')
        else:
            pop = population(size=[2,8], ploidy=2, loci=[5, 7],
                lociPos=[ [2,3,4,5,6],[2,4,6,8,10,12,14]],
                alleleNames=['1','2'], infoFields=['age', 'fitness'])
            InitByFreq(pop, [.2, .8])
            pop.setIndInfo(range(10), 'age')
            pop.setIndInfo(range(100, 110), 'fitness')
        file = 'a.pop'
        pop.savePopulation(file, compress=False)
        assert os.path.isfile(file), "File %s does not exist" % file
        pop1 = LoadPopulation(file)
        self.assertEqual(pop, pop1)
        pop.savePopulation(file, compress=True)
        assert os.path.isfile(file), "File %s does not exist" % file
        pop1 = LoadPopulation(file)
        self.assertEqual(pop, pop1)
        os.remove(file)
        # can load file with wrong extension
        # can load file with wrong extension
        pop.savePopulation('a.txt')
        pop1 = LoadPopulation('a.txt')
        self.assertEqual(pop, pop1)
        os.remove('a.txt')
        #
        # save load several populations
        # make pop and pop1 different
        pop.individual(0).setAllele(0,1)
        pop1.individual(0).setAllele(1,1)
        self.assertNotEqual(pop, pop1)

    def testCrossSaveLoad(self):
        'Testing population saved by other modules'
        if AlleleType() == 'binary':
            if os.path.isfile('test_ba.txt'):
                pop = LoadPopulation('test_ba.txt')
            else:
                pop = population(size=[2,8], ploidy=2, loci=[5, 7],
                    lociPos=[ [2,3,4,5,6],[2,4,6,8,10,12,14]],
                    alleleNames=['1', '2'], infoFields=['age', 'fitness'], ancestralDepth=2)
                InitByFreq(pop, [.2, .8])
                pop.setIndInfo(range(10), 'age')
                pop.setIndInfo(range(100, 110), 'fitness')
                simu = simulator(pop, randomMating(), rep=1)
                simu.evolve(ops=[], end=2)
                simu.population(0).savePopulation('test_ba.txt')
            # try to load file
            if os.path.isfile('test_std.txt'):
                pop1 = LoadPopulation('test_std.txt')
                self.assertEqual(pop, pop1)
            if os.path.isfile('test_la.txt'):
                pop1 = LoadPopulation('test_la.txt')
                self.assertEqual(pop, pop1)
        elif AlleleType() == 'short':
            if os.path.isfile('test_ba.txt'):
                pop = LoadPopulation('test_ba.txt')
                pop.savePopulation('test_std.txt')
            else:
                return
            if os.path.isfile('test_la.txt'):
                pop1 = LoadPopulation('test_la.txt')
                self.assertEqual(pop, pop1)
        else:
            if os.path.isfile('test_ba.txt'):
                pop = LoadPopulation('test_ba.txt')
                pop.savePopulation('test_la.txt')
            else:
                return
            if os.path.isfile('test_std.txt'):
                pop1 = LoadPopulation('test_std.txt')
                self.assertEqual(pop, pop1)


    def testMergePopulation(self):
        'Testing merge populations...'
        pop = population(size=[7, 3, 4], loci=[4, 5, 1])
        pop1 = population(size=[4, 5], loci=[4,5,1])
        pop2 = population(size=[4, 5], loci=[4,1])
        InitByFreq(pop, [.2, .3, .5])
        InitByFreq(pop1, [.5, .5])
        InitByFreq(pop2, [.2, .8])
        # merge error (number of subpop mismatch)
        self.assertRaises(exceptions.ValueError, pop.mergePopulation, pop2)
        # merge without subpop size change
        pop_ori = pop.clone()
        pop.mergePopulation(pop1)
        self.assertEqual(pop.subPopSizes(), (7,3,4,4,5))
        for sp in range(3):
            for i in range(pop.subPopSize(sp)):
                self.assertEqual(pop.individual(i, sp), pop_ori.individual(i, sp))
        for sp in range(2):
            for i in range(pop.subPopSize(3+sp)):
                self.assertEqual(pop.individual(i, sp+3), pop1.individual(i, sp))
        # merge with new subpop sizes
        pop = pop_ori.clone()
        # total size should not change
        self.assertRaises(exceptions.ValueError, pop.mergePopulation, pop1, newSubPopSizes=[5, 20])
        #
        pop.mergePopulation(pop1, newSubPopSizes=[9, 10,4])
        self.assertEqual(pop.subPopSizes(), (9, 10, 4))
        for i in range(pop_ori.popSize()):
            self.assertEqual(pop.individual(i), pop_ori.individual(i))
        for i in range(pop1.popSize()):
            self.assertEqual(pop.individual(i+pop_ori.popSize()), pop1.individual(i))
        #
        # test the Merge function
        pop = population(size=[7, 3, 4], loci=[4, 5, 1])
        pop1 = population(size=[4, 5], loci=[4,5,1])
        pop2 = population(size=[4, 5], loci=[4,1])
        InitByFreq(pop, [.2, .3, .5])
        pop_ori = pop.clone()
        InitByFreq(pop1, [.5, .5])
        pop1_ori = pop1.clone()
        InitByFreq(pop2, [.2, .8])
        pop2_ori = pop2.clone()
        #self.assertRaises(exceptions.ValueError, MergePopulations, [pop, pop2])
        #
        mp = MergePopulations(pops=[pop, pop1, pop1])
        # populaition not changed
        self.assertEqual(pop, pop_ori)
        self.assertEqual(pop1, pop1_ori)
        pop.mergePopulation(pop1)
        pop.mergePopulation(pop1)
        self.assertEqual(pop, mp)
        #
        # test for merge of ancestral gen
        pop = population(size=[7, 3, 4], loci=[4, 5, 1])
        pop.setAncestralDepth(-1)
        pop1 = population(size=[4, 5], loci=[4, 5, 1])
        pop.pushAndDiscard(pop1)
        #
        pop1 = pop.clone()
        #
        pop2 = MergePopulations([pop, pop1])
        self.assertEqual(pop2.ancestralDepth(), 1)
        self.assertEqual(pop2.subPopSizes(), (4,5,4,5))
        pop2.useAncestralPop(1)
        self.assertEqual(pop2.subPopSizes(), (7,3,4,7,3,4))
        # test for keepAncestralPops (FIXME)

    def testMergePopulationByLoci(self):
        'Testing merge populations...'
        pop = population(size=[7, 3, 4], loci=[4, 5, 1])
        pop1 = population(size=[7, 3, 4], loci=[3, 2])
        pop2 = population(size=[4, 5], loci=[4,1])
        InitByFreq(pop, [.2, .3, .5])
        InitByFreq(pop1, [.5, .5])
        InitByFreq(pop2, [.2, .8])
        # merge error (number of indivisuals mismatch)
        self.assertRaises(exceptions.ValueError, pop.mergePopulationByLoci, pop2)
        # merge without subpop size change
        pop_ori = pop.clone()
        pop.mergePopulationByLoci(pop1)
        self.assertEqual(pop.subPopSizes(), (7,3,4))
        self.assertEqual(pop.numLoci(), (4, 5, 1, 3, 2))
        for sp in range(3):
            for i in range(pop.subPopSize(sp)):
                ind = pop.individual(i, sp)
                ind1 = pop_ori.individual(i, sp)
                ind2 = pop1.individual(i, sp)
                for p in range(2): # ploidy
                    for j in range(10):
                        self.assertEqual(ind.allele(j, p), ind1.allele(j, p))
                    for j in range(5):
                        self.assertEqual(ind.allele(j+10, p), ind2.allele(j, p))
        # merge with new loci
        pop = pop_ori.clone()
        # total number of loci should not change should
        self.assertRaises(exceptions.ValueError, pop.mergePopulationByLoci, pop1, newNumLoci=[5, 7])
        pop = pop_ori.clone()
        # loci distance must be in order
        self.assertRaises(exceptions.ValueError, pop.mergePopulationByLoci, pop1, newNumLoci=[5, 7, 3])
        # this time should be fine.
        pop = pop_ori.clone()
        pop.mergePopulationByLoci(pop1, newNumLoci=[5, 7, 3], newLociPos=range(5)+range(7)+range(3))
        self.assertEqual(pop.subPopSizes(), (7, 3, 4))
        #
        for i in range(pop.popSize()):
            ind = pop.individual(i)
            ind1 = pop_ori.individual(i)
            ind2 = pop1.individual(i)
            for p in range(2): # ploidy
                for j in range(10):
                    self.assertEqual(ind.allele(j, p), ind1.allele(j, p))
                for j in range(5):
                    self.assertEqual(ind.allele(j+10, p), ind2.allele(j, p))
        #
        # test the Merge function
        pop = population(size=[7, 3, 4], loci=[4, 5, 1])
        pop1 = population(size=[7, 3, 4], loci=[2, 3])
        pop2 = population(size=[4, 5], loci=[4,1])
        InitByFreq(pop, [.2, .3, .5])
        pop_ori = pop.clone()
        InitByFreq(pop1, [.5, .5])
        pop1_ori = pop1.clone()
        InitByFreq(pop2, [.2, .8])
        pop2_ori = pop2.clone()
        self.assertRaises(exceptions.ValueError, MergePopulationsByLoci, [pop, pop2])
        #
        mp = MergePopulationsByLoci(pops=[pop, pop1, pop1])
        # populaition not changed
        self.assertEqual(pop, pop_ori)
        self.assertEqual(pop1, pop1_ori)
        pop.mergePopulationByLoci(pop1)
        pop.mergePopulationByLoci(pop1)
        self.assertEqual(pop, mp)
        #
        # test for merge of ancestral gen
        pop = population(size=[3, 4], loci=[4, 5, 1])
        pop.setAncestralDepth(-1)
        pop1 = population(size=[3, 4], loci=[4, 5, 1])
        pop.pushAndDiscard(pop1)
        #
        pop1 = pop.clone()
        #
        pop2 = MergePopulationsByLoci([pop, pop1])
        self.assertEqual(pop2.ancestralDepth(), 1)
        self.assertEqual(pop2.numLoci(), (4,5,1,4,5,1))
        #
        # test for merge with loci rearrangement
        pop1 = population(10, loci=[2,3], lociPos=[0.1, 0.3, 0.15, 0.2, 0.3])
        for i in range(5):
            InitByFreq(pop1, locus=i, alleleFreq=[i*0.1+0.05, 1-i*0.1 - 0.05])
        Stat(pop1, alleleFreq=range(5))
        af1 = [pop1.dvars().alleleFreq[x][0] for x in range(5)]
        pop2 = population(10, loci=[3,2,1], lociPos=[0.15, 0.16, 0.32, 0.1, 0.21, 0.1])
        for i in range(5):
            InitByFreq(pop2, locus=i, alleleFreq=[i*0.1 + 0.12, 1-i*0.1 - 0.12])
        Stat(pop2, alleleFreq=range(6))
        af2 = [pop2.dvars().alleleFreq[x][0] for x in range(6)]
        #
        pop3 = MergePopulationsByLoci([pop1, pop2], byChromosome=True)
        Stat(pop3, alleleFreq=range(11))
        af3 = [pop3.dvars().alleleFreq[x][0] for x in range(11)]
        self.assertEqual(af1[0], af3[0])
        self.assertEqual(af2[0], af3[1])
        self.assertEqual(af2[1], af3[2])
        self.assertEqual(af1[1], af3[3])
        self.assertEqual(af2[2], af3[4])
        self.assertEqual(af2[3], af3[5])
        self.assertEqual(af1[2], af3[6])
        self.assertEqual(af1[3], af3[7])
        self.assertEqual(af2[4], af3[8])
        self.assertEqual(af1[4], af3[9])
        self.assertEqual(af2[5], af3[10])
        #
        # test mergePopulationByLoci using byChromosome
        pop = population(size=[7, 3, 4], loci=[4, 5, 1])
        InitByFreq(pop, [.2, .3, .5])
        pop_re = pop.clone()
        pop_re.removeLoci(remove=[1, 4, 7])
        pop_ke = pop.clone()
        pop_ke.removeLoci(keep=[1, 4, 7])
        pop_re.mergePopulationByLoci(pop_ke, byChromosome=True)
        self.assertEqual(pop, pop_re)


    def testInsertBeforeLoci(self):
        'Testing insert before loci of a population'
        pop = population(size=[7,3,4], loci=[4,5,1])
        InitByFreq(pop, [.2, .3, .5])
        pop1 = pop.clone()
        self.assertRaises(exceptions.ValueError, pop.insertBeforeLoci, idx=[0,5], pos=[0,0.5])
        # recover pop.
        pop = pop1.clone()
        pop.insertBeforeLoci(idx=[0, 5], pos=[0,1.5])
        self.assertEqual(pop.locusName(6), 'ins2_2_1')
        # compare
        for i in range(pop.popSize()):
            ind = pop.individual(i)
            ind1 = pop1.individual(i)
            for j in range(pop.ploidy()):
                self.assertEqual(ind.allele(0, j), 0)
                self.assertEqual(ind.allele(1, j), ind1.allele(0, j))
                self.assertEqual(ind.allele(2, j), ind1.allele(1, j))
                self.assertEqual(ind.allele(3, j), ind1.allele(2, j))
                self.assertEqual(ind.allele(4, j), ind1.allele(3, j))
                self.assertEqual(ind.allele(5, j), ind1.allele(4, j))
                self.assertEqual(ind.allele(6, j), 0)
                self.assertEqual(ind.allele(7, j), ind1.allele(5, j))
                self.assertEqual(ind.allele(8, j), ind1.allele(6, j))
                self.assertEqual(ind.allele(9, j), ind1.allele(7, j))
        pop.insertBeforeLocus(idx=pop.totNumLoci()-1, pos=0.5)
        self.assertEqual(pop.locusName(11), 'ins3_1_1')
        for i in range(pop.popSize()):
            ind = pop.individual(i)
            ind1 = pop1.individual(i)
            for j in range(pop.ploidy()):
                self.assertEqual(ind.allele(11, j), 0)
        # insert multiple loci before the same location.
        # recover pop.
        pop = pop1.clone()
        pop.insertBeforeLoci(idx=[0, 5, 5, 9, 9], pos=[0,1.3, 1.5, 0.5, 0.6])
        self.assertEqual(pop.locusName(6), 'ins2_2_1')
        # compare
        for i in range(pop.popSize()):
            ind = pop.individual(i)
            ind1 = pop1.individual(i)
            for j in range(pop.ploidy()):
                self.assertEqual(ind.allele(0, j), 0)
                self.assertEqual(ind.allele(1, j), ind1.allele(0, j))
                self.assertEqual(ind.allele(2, j), ind1.allele(1, j))
                self.assertEqual(ind.allele(3, j), ind1.allele(2, j))
                self.assertEqual(ind.allele(4, j), ind1.allele(3, j))
                self.assertEqual(ind.allele(5, j), ind1.allele(4, j))
                self.assertEqual(ind.allele(6, j), 0)
                self.assertEqual(ind.allele(7, j), 0)
                self.assertEqual(ind.allele(8, j), ind1.allele(5, j))
                self.assertEqual(ind.allele(9, j), ind1.allele(6, j))
                self.assertEqual(ind.allele(10, j), ind1.allele(7, j))
                self.assertEqual(ind.allele(11, j), ind1.allele(8, j))
                self.assertEqual(ind.allele(12, j), 0)
                self.assertEqual(ind.allele(13, j), 0)
                self.assertEqual(ind.allele(14, j), ind1.allele(9, j))
        # test ancestral population FIXME

    def  testInsertAfterLoci(self):
        'Testing insert before loci of a population'
        pop = population(size=[7,3,4], loci=[4,5,1])
        InitByFreq(pop, [.2, .3, .5])
        pop1 = pop.clone()
        self.assertRaises(exceptions.ValueError, pop.insertAfterLoci, idx=[0,5], pos=[0,0.5])
        # recover pop.
        pop = pop1.clone()
        pop.insertAfterLoci(idx=[0, 5], pos=[1.5,2.5])
        self.assertEqual(pop.locusName(7), 'app2_2_1')
        # compare
        for i in range(pop.popSize()):
            ind = pop.individual(i)
            ind1 = pop1.individual(i)
            for j in range(pop.ploidy()):
                self.assertEqual(ind.allele(0, j), ind1.allele(0, j))
                self.assertEqual(ind.allele(1, j), 0)
                self.assertEqual(ind.allele(2, j), ind1.allele(1, j))
                self.assertEqual(ind.allele(3, j), ind1.allele(2, j))
                self.assertEqual(ind.allele(4, j), ind1.allele(3, j))
                self.assertEqual(ind.allele(5, j), ind1.allele(4, j))
                self.assertEqual(ind.allele(6, j), ind1.allele(5, j))
                self.assertEqual(ind.allele(7, j), 0)
                self.assertEqual(ind.allele(8, j), ind1.allele(6, j))
                self.assertEqual(ind.allele(9, j), ind1.allele(7, j))
        pop.insertAfterLocus(idx=pop.totNumLoci()-1, pos=99)
        self.assertEqual(pop.locusName(12), 'app3_1_1')
        for i in range(pop.popSize()):
            ind = pop.individual(i)
            ind1 = pop1.individual(i)
            for j in range(pop.ploidy()):
                self.assertEqual(ind.allele(12, j), 0)
        # insert multiple loci before the same location.
        # recover pop.
        pop = pop1.clone()
        pop.insertAfterLoci(idx=[0, 5, 5, 9, 9], pos=[1.5, 2.3, 2.5, 1.5, 1.6])
        self.assertEqual(pop.locusName(7), 'app2_2_1')
        # compare
        for i in range(pop.popSize()):
            ind = pop.individual(i)
            ind1 = pop1.individual(i)
            for j in range(pop.ploidy()):
                self.assertEqual(ind.allele(0, j), ind1.allele(0, j))
                self.assertEqual(ind.allele(1, j), 0)
                self.assertEqual(ind.allele(2, j), ind1.allele(1, j))
                self.assertEqual(ind.allele(3, j), ind1.allele(2, j))
                self.assertEqual(ind.allele(4, j), ind1.allele(3, j))
                self.assertEqual(ind.allele(5, j), ind1.allele(4, j))
                self.assertEqual(ind.allele(6, j), ind1.allele(5, j))
                self.assertEqual(ind.allele(7, j), 0)
                self.assertEqual(ind.allele(8, j), 0)
                self.assertEqual(ind.allele(9, j), ind1.allele(6, j))
                self.assertEqual(ind.allele(10, j), ind1.allele(7, j))
                self.assertEqual(ind.allele(11, j), ind1.allele(8, j))
                self.assertEqual(ind.allele(12, j), ind1.allele(9, j))
                self.assertEqual(ind.allele(13, j), 0)
                self.assertEqual(ind.allele(14, j), 0)
        # test ancestral population FIXME


    def testResizePopulation(self):
        'Testing population resize'
        pop = population(size=[7,3,4], loci=[4,5,1])
        InitByFreq(pop, [.2, .3, .5])
        pop1 = pop.clone()
        pop2 = pop.clone()
        # resize error (number of subpop mismatch)
        self.assertRaises(exceptions.ValueError, pop1.resize, [5,5])
        # resize without propagation
        pop1.resize([5, 5, 8], propagate=False)
        for sp in range(pop1.numSubPop()):
            for i in range(min(pop1.subPopSize(sp), pop.subPopSize(sp))):
                self.assertEqual(pop1.individual(i, sp), pop.individual(i, sp))
            for i in range(min(pop1.subPopSize(sp), pop.subPopSize(sp)), pop1.subPopSize(sp)):
                self.assertEqual(pop1.individual(i, sp).arrGenotype(), [0]*20)
        # resize with propagation
        pop2.resize([5, 5, 8], propagate=True)
        for sp in range(pop1.numSubPop()):
            for i in range(pop2.subPopSize(sp)):
                self.assertEqual(pop2.individual(i, sp), pop.individual(i%pop.subPopSize(sp), sp))

    def testSexSplitter(self):
        'Test sex virtual subpop splitter'
        pop = population(size=[20, 80])
        InitByFreq(pop, [0.4, 0.6])
        Stat(pop, numOfMale=True)
        pop.setVirtualSplitter(sexSplitter())
        self.assertEqual(pop.virtualSubPopSize(1, 0), pop.dvars(1).numOfMale)
        self.assertEqual(pop.virtualSubPopSize(1, 1), pop.dvars(1).numOfFemale)
        self.assertEqual(pop.virtualSubPopName(1, 0), 'Male')
        self.assertEqual(pop.virtualSubPopName(1, 1), 'Female')
        pop.activateVirtualSubPop(1, 1)
        for ind in pop.individuals(1):
            self.assertEqual(ind.sex(), Female)
        pop.deactivateVirtualSubPop(1)
        #
        pop.activateVirtualSubPop(1, 0)
        for ind in pop.individuals(1):
            self.assertEqual(ind.sex(), Male)
        pop.deactivateVirtualSubPop(1)
        numMale = 0
        numFemale = 0
        for ind in pop.individuals(1):
            if ind.sex() == Male:
                numMale += 1
            else:
                numFemale += 1
        #print numMale, numFemale
        self.assertEqual(numMale == 0, False)
        self.assertEqual(numFemale == 0, False)


    def testAffectionSplitter(self):
        'Test sex virtual subpop splitter'
        pop = population(size=[20, 80])
        InitByFreq(pop, [0.4, 0.6])
        MaPenetrance(pop, locus=0, wildtype=0, penetrance=[0.2, 0.4, 0.8])
        Stat(pop, numOfAffected=True)
        pop.setVirtualSplitter(affectionSplitter())
        self.assertEqual(pop.virtualSubPopSize(1, 1), pop.dvars(1).numOfAffected)
        self.assertEqual(pop.virtualSubPopSize(1, 0), pop.dvars(1).numOfUnaffected)
        self.assertEqual(pop.virtualSubPopName(1, 0), 'Unaffected')
        self.assertEqual(pop.virtualSubPopName(1, 1), 'Affected')
        pop.activateVirtualSubPop(1, 1)
        for ind in pop.individuals(1):
            self.assertEqual(ind.affected(), True)
        pop.deactivateVirtualSubPop(1)
        #
        pop.activateVirtualSubPop(1, 0)
        for ind in pop.individuals(1):
            self.assertEqual(ind.affected(), False)
        pop.deactivateVirtualSubPop(1)
        numAffected = 0
        numUnaffected = 0
        for ind in pop.individuals(1):
            if ind.affected():
                numAffected += 1
            else:
                numUnaffected += 1
        self.assertEqual(numAffected == 0, False)
        self.assertEqual(numUnaffected == 0, False)


    def testInfoSplitter(self):
        'Test info virtual subpop splitter'
        pop = population(1000, infoFields=['x'])
        for ind in pop.individuals():
            ind.setInfo(random.randint(10, 20), 'x')
        pop.setVirtualSplitter(infoSplitter('x', values=range(10, 15)))
        self.assertEqual(pop.numVirtualSubPop(), 5)
        infos = list(pop.indInfo('x'))
        self.assertEqual(pop.virtualSubPopName(0, 0), "x = 10")
        self.assertEqual(pop.virtualSubPopName(0, 1), "x = 11")
        self.assertEqual(pop.virtualSubPopName(0, 4), "x = 14")
        self.assertEqual(pop.virtualSubPopSize(0, 0), infos.count(10))
        self.assertEqual(pop.virtualSubPopSize(0, 1), infos.count(11))
        self.assertEqual(pop.virtualSubPopSize(0, 2), infos.count(12))
        self.assertEqual(pop.virtualSubPopSize(0, 3), infos.count(13))
        self.assertEqual(pop.virtualSubPopSize(0, 4), infos.count(14))
        pop.activateVirtualSubPop(0, 1)
        for ind in pop.individuals(0):
            self.assertEqual(ind.info('x'), 11)
        # test cutoff
        pop.setVirtualSplitter(infoSplitter('x', cutoff=[11.5, 13.5]))
        self.assertEqual(pop.virtualSubPopName(0, 0), "x < 11.5")
        self.assertEqual(pop.virtualSubPopName(0, 1), "11.5 <= x < 13.5")
        self.assertEqual(pop.virtualSubPopName(0, 2), "x >= 13.5")
        self.assertEqual(pop.virtualSubPopSize(0, 0), infos.count(10) + infos.count(11))
        self.assertEqual(pop.virtualSubPopSize(0, 1), infos.count(12) + infos.count(13))
        self.assertEqual(pop.virtualSubPopSize(0, 2),
            sum([infos.count(x) for x in range(14, 21)]))


    def testProportionSplitter(self):
        'Test proportion virtual subpop splitter'
        pop = population(10)
        pop.setVirtualSplitter(proportionSplitter([0.01]*100))
        for i in range(100):
            self.assertEqual(pop.virtualSubPopName(0, i), "Prop 0.01")
            if i != 99:
                self.assertEqual(pop.virtualSubPopSize(0, i), 0)
            else:
                # the last vsp is specially treated to avoid such problem.
                self.assertEqual(pop.virtualSubPopSize(0, i), 10)
        #
        pop = population(1000)
        pop.setVirtualSplitter(proportionSplitter([0.4, 0.6]))
        self.assertEqual(pop.virtualSubPopSize(0, 0), 400)
        self.assertEqual(pop.virtualSubPopSize(0, 1), 600)
        pop.activateVirtualSubPop(0, 1)
        count = 0
        for ind in pop.individuals(0):
            count += 1
        self.assertEqual(count, 600)


    def testRangeSplitter(self):
        'Test range virtual subpop splitter'
        pop = population(100)
        pop.setVirtualSplitter(rangeSplitter(range=[10, 20]))
        self.assertEqual(pop.virtualSubPopName(0, 0), "Range [10, 20)")
        pop.setVirtualSplitter(rangeSplitter(ranges=[[10, 20], [80, 200]]))
        self.assertEqual(pop.virtualSubPopName(0, 0), "Range [10, 20)")
        self.assertEqual(pop.virtualSubPopName(0, 1), "Range [80, 200)")
        self.assertEqual(pop.virtualSubPopSize(0, 0), 10)
        self.assertEqual(pop.virtualSubPopSize(0, 1), 20)
        pop.activateVirtualSubPop(0, 1)
        count = 0
        for ind in pop.individuals(0):
            count += 1
        self.assertEqual(count, 20)


    def testGenotypeSplitter(self):
        'Test genotype virtual subpop splitter'
        pop = population(1000, loci=[2, 3])
        InitByFreq(pop, [0.3, 0.7])
        pop.setVirtualSplitter(genotypeSplitter(locus=1, alleles=[[0,0], [1,0]], phase=True))
        self.assertEqual(pop.virtualSubPopName(0, 0), "Genotype 1: 0 0")
        Stat(pop, genoFreq=[1], genoFreq_param={'phase':1})
        self.assertEqual(pop.virtualSubPopSize(0, 0), pop.dvars().genoNum[1][0][0])
        self.assertEqual(pop.virtualSubPopSize(0, 1), pop.dvars().genoNum[1][1][0])
        pop.activateVirtualSubPop(0, 1)
        for ind in pop.individuals(0):
            self.assertEqual((ind.allele(1, 0), ind.allele(1, 1)), (1,0))
        # without phase
        #
        pop.deactivateVirtualSubPop(0)
        pop.setVirtualSplitter(genotypeSplitter(locus=1, alleles=[[0,0], [1,0], [0,1]], phase=False))
        self.assertEqual(pop.virtualSubPopName(0, 0), "Genotype 1: 0 0")
        Stat(pop, genoFreq=[1], genoFreq_param={'phase':0})
        self.assertEqual(pop.virtualSubPopSize(0, 1), pop.virtualSubPopSize(0, 2))
        self.assertEqual(pop.virtualSubPopSize(0, 1), pop.dvars().genoNum[1][0][1])
        #
        pop.activateVirtualSubPop(0, 1)
        for ind in pop.individuals(0):
            self.assertEqual((ind.allele(1, 0), ind.allele(1, 1)) in [(1,0), (0,1)], True)
        # multiple genotype at the same locus
        pop.setVirtualSplitter(genotypeSplitter(locus=1, alleles=[[0,0], [1, 0, 1, 1], [0, 1]], phase=False))
        self.assertEqual(pop.virtualSubPopName(0, 0), "Genotype 1: 0 0")
        self.assertEqual(pop.virtualSubPopName(0, 1), "Genotype 1: 1 0 1 1")
        Stat(pop, genoFreq=[1], genoFreq_param={'phase':1})
        self.assertEqual(pop.virtualSubPopSize(0, 0), pop.dvars().genoNum[1][0][0])
        self.assertEqual(pop.virtualSubPopSize(0, 1), pop.dvars().genoNum[1][1][0] +
            pop.dvars().genoNum[1][1][1] + pop.dvars().genoNum[1][0][1] )
        # multiple loci

    def testCombinedSplitter(self):
        'Testing the combined splitter'
        pop = population(1000, loci=[2, 3])
        InitByFreq(pop, [0.3, 0.7])
        pop.setVirtualSplitter(combinedSplitter([
            genotypeSplitter(locus=1, alleles=[[0,0], [1,0]], phase=True),
            sexSplitter()]))
        self.assertEqual(pop.virtualSubPopName(0, 0), "Genotype 1: 0 0")
        self.assertEqual(pop.virtualSubPopName(0, 1), "Genotype 1: 1 0")
        self.assertEqual(pop.virtualSubPopName(0, 2), "Male")
        self.assertEqual(pop.virtualSubPopName(0, 3), "Female")
        Stat(pop, numOfMale=True)
        self.assertEqual(pop.virtualSubPopSize(0, 3), pop.dvars(0).numOfFemale)


    def testInfoIterator(self):
        'Testing the info iterator in virtual subpopulations'
        pop = population(1000, infoFields=['x'])
        for ind in pop.individuals():
            ind.setInfo(random.randint(10, 20), 'x')
        pop.setVirtualSplitter(infoSplitter('x', values=range(10, 15)))
        pop.activateVirtualSubPop(0, 1)
        for ind in pop.individuals(0):
            self.assertEqual(ind.info('x'), 11)
        # this makes sure that the new infoIterator can skip invisible individuals.
        self.assertEqual(pop.indInfo('x'), tuple([11.0]*pop.virtualSubPopSize(0, 1)))
        pop.deactivateVirtualSubPop(0)


    def testAlleleIterator(self):
        'Test the allele iterator in virtual subpopulations'
        pop = population(1000, loci=[5, 8])
        InitByFreq(pop, [0.2, 0.4, 0.4])
        pop.setVirtualSplitter(genotypeSplitter(loci=[2,5], alleles=[1,1,1,1], phase=False))
        pop.activateVirtualSubPop(0, 0)
        for ind in pop.individuals(0):
            self.assertEqual(ind.allele(2, 0), 1)
            self.assertEqual(ind.allele(2, 1), 1)
            self.assertEqual(ind.allele(5, 0), 1)
            self.assertEqual(ind.allele(5, 1), 1)
        Stat(pop, alleleFreq=[2])
        self.assertEqual(pop.dvars().alleleNum[2][0], 0)
        pop.deactivateVirtualSubPop(0)
        Stat(pop, alleleFreq=range(pop.totNumLoci()))
        an = [pop.dvars().alleleNum[x][0] for x in range(pop.totNumLoci())]

    def testIterateVirtualSubPop(self):
        'Testing iteration through virtual subpopulations'
        pop =  population(1000, loci=[5, 8])
        InitByFreq(pop, [0.2, 0.4, 0.4])
        pop.setVirtualSplitter(genotypeSplitter(loci=[2,5], alleles=[1,1,1,1], phase=False))
        for ind in pop.individuals(0, 0):
            self.assertEqual(ind.allele(2, 0), 1)
            self.assertEqual(ind.allele(2, 1), 1)
            self.assertEqual(ind.allele(5, 0), 1)
            self.assertEqual(ind.allele(5, 1), 1)
        Stat(pop, alleleFreq=[2])
        # this is different from the previous tests, where virtual subpopulation is activated
        self.assertEqual(pop.dvars().alleleNum[2][0] == 0, False)

    def testLocateSelf(self):
        'Testing set index for individuals themselves'
        simu = simulator(population(1000, ancestralDepth=2, infoFields=['index']), randomMating())
        simu.evolve(ops=[], gen=2)
        pop = simu.getPopulation(0, True)
        pop.locateRelatives(REL_Self, ['index'])
        for ans in range(pop.ancestralDepth()):
            pop.useAncestralPop(ans)
            for idx,ind in enumerate(pop.individuals()):
                self.assertEqual(ind.info('index'), idx)

    def testLocateSpouse(self):
        'Testing set index for spouse of individuals'
        # it is possible for someone to have many spouse so we need to be safe here.
        spouseFields = ['spouse%d' % x for x in range(10)]
        simu = simulator(population([1000, 1000], ancestralDepth=4,
            infoFields=['father_idx', 'mother_idx'] + spouseFields),
            randomMating(numOffspring=2))
        simu.evolve(ops=[parentsTagger()], gen=10)
        pop = simu.getPopulation(0, True)
        pop.locateRelatives(REL_Spouse, spouseFields)
        for ans in range(1, pop.ancestralDepth()):
            # parental generation
            pop.useAncestralPop(ans)
            allPairs = []
            for field in spouseFields:
                spouse = pop.indInfo(field)
                pairs = [(x, spouse[x]) for x in range(len(spouse)) if spouse[x] != -1]
                allPairs += pairs
                allPairs += [(y,x) for x,y in pairs]
            pop.useAncestralPop(ans-1)
            for ind in pop.individuals():
                pair = (ind.info('father_idx'), ind.info('mother_idx'))
                self.assertEqual(pair in allPairs, True)
    

    def testLocateOffspring(self):
        'Testing set index for offsprings of individuals'
        offFields = ['off%d' % x for x in range(10)]
        simu = simulator(population([1000, 1000], ancestralDepth=4,
            infoFields=['father_idx', 'mother_idx'] + offFields),
            randomMating(numOffspring=2))
        simu.evolve(ops=[parentsTagger()], gen=10)
        pop = simu.getPopulation(0, True)
        self.assertEqual(pop.locateRelatives(REL_Offspring, offFields), True)
        for field in offFields:
            for ans in range(1, pop.ancestralDepth()):
                # parental generation
                pop.useAncestralPop(ans)
                off = pop.indInfo(field)
                pop.useAncestralPop(ans-1)
                for idx,ind in enumerate(off):
                    # idx is for the parental generation
                    # ind is for the offspring generation
                    # one of ind's parent should be idx.
                    if ind == -1:
                        continue
                    self.assertEqual(idx in 
                        [pop.ancestor(int(ind), ans-1).info('father_idx'),
                        pop.ancestor(int(ind), ans-1).info('mother_idx')], True)
        # FIXME: test single parent case
    

    def testLocateSibling(self):
        'Testing set index for sibling of individuals'
        offFields = ['off%d' % x for x in range(20)]
        sibFields = ['sib%d' % x for x in range(20)]
        fullsibFields = ['fullsib%d' % x for x in range(20)]
        simu = simulator(population([1000, 1000], ancestralDepth=4,
            infoFields=['father_idx', 'mother_idx'] + fullsibFields 
                + sibFields + offFields),
            randomMating(numOffspring=2))
        simu.evolve(ops=[parentsTagger()], gen=10)
        pop = simu.getPopulation(0, True)
        pop.locateRelatives(REL_Offspring, offFields)
        pop.locateRelatives(REL_Sibling, sibFields)
        pop.locateRelatives(REL_FullSibling, fullsibFields)
        for ans in range(0, pop.ancestralDepth()):
            pop.useAncestralPop(ans)
            for idx,ind in enumerate(pop.individuals()):
                father = int(ind.info('father_idx'))
                mother = int(ind.info('mother_idx'))
                father_off = [pop.ancestor(father, ans + 1).info(x) for x in offFields 
                    if pop.ancestor(father, ans + 1).info(x) != -1]
                mother_off = [pop.ancestor(mother, ans + 1).info(x) for x in offFields 
                    if pop.ancestor(mother, ans + 1).info(x) != -1]
                self.assertEqual(idx in father_off and idx in mother_off, True)
                #
                sibs = [ind.info(x) for x in sibFields if ind.info(x) != -1]
                fullsibs = [ind.info(x) for x in fullsibFields if ind.info(x) != -1]
                for sib in sibs:
                    self.assertEqual((sib in father_off) or (sib in mother_off), True)
                for sib in fullsibs:
                    self.assertEqual((sib in father_off) and (sib in mother_off), True)
        # FIXME: test sex choices


    def testTraceRelativeInfo(self):
        'Testing tracing relatives and set indexes'
        offFields = ['off%d' % x for x in range(20)]
        fullsibFields = ['fullsib%d' % x for x in range(20)]
        cousinFields = ['cousin%d' % x for x in range(20)]
        mcFields = ['mc%d' % x for x in range(20)]
        fcFields = ['fc%d' % x for x in range(20)]
        simu = simulator(population([1000, 1000], ancestralDepth=4,
            infoFields=['father_idx', 'mother_idx'] + fullsibFields 
                + cousinFields + offFields + mcFields + fcFields),
            randomMating(numOffspring=2))
        simu.evolve(ops=[parentsTagger()], gen=10)
        pop = simu.getPopulation(0, True)
        pop.locateRelatives(REL_Offspring, offFields)
        pop.locateRelatives(REL_FullSibling, fullsibFields)
        #
        pop.setIndexesOfRelatives(pathGen=[0, 1, 1, 0],
            pathFields = [['father_idx', 'mother_idx'], fullsibFields,
                offFields],
            pathSex = [AnySex]*3,
            resultFields = cousinFields)
        pop.setIndexesOfRelatives(pathGen=[0, 1, 1, 0],
            pathFields = [['father_idx', 'mother_idx'], fullsibFields,
                offFields],
            pathSex = [AnySex, AnySex, MaleOnly],
            resultFields = mcFields)
        pop.setIndexesOfRelatives(pathGen=[0, 1, 1, 0],
            pathFields = [['father_idx', 'mother_idx'], fullsibFields,
                offFields],
            pathSex = [AnySex, AnySex, FemaleOnly],
            resultFields = fcFields)
        for idx,ind in enumerate(pop.individuals()):
            cousins = [ind.intInfo(x) for x in cousinFields if ind.info(x) != -1]
            maleCousins = [ind.intInfo(x) for x in mcFields if ind.info(x) != -1]
            femaleCousins = [ind.intInfo(x) for x in fcFields if ind.info(x) != -1]
            for m in maleCousins:
                self.assertEqual(pop.individual(m).sex(), Male)
            for f in femaleCousins:
                self.assertEqual(pop.individual(f).sex(), Female)
            self.assertEqual(len(cousins), len(maleCousins) + len(femaleCousins))
            # cousin is mutual
            for c in cousins:
                ccousins = [pop.individual(c).intInfo(x) for x in cousinFields if pop.individual(c).info(x) != -1]
                self.assertEqual(idx in ccousins, True)

    def testAncestor(self):
        'Testing direct access to ancestors'
        pop = population([100, 200], loci=[10, 20], infoFields=['x', 'y'],
            ancestralDepth=5)
        InitByFreq(pop, [0.2, 0.8])
        for ind in pop.individuals():
            ind.setInfo(random.randint(4, 10), 'x')
            ind.setInfo(random.randint(10, 100), 'y')
        pop1 = population([200, 100], loci=[10, 20], infoFields=['x', 'y'])
        InitByFreq(pop1, [0.5, 0.5])
        for ind in pop1.individuals():
            ind.setInfo(random.randint(4, 10), 'x')
            ind.setInfo(random.randint(10, 100), 'y')
        #
        pop_c = pop.clone()
        pop1_c = pop1.clone()
        #
        pop.pushAndDiscard(pop1)
        #
        for idx, ind in enumerate(pop_c.individuals()):
            self.assertEqual(ind, pop.ancestor(idx, 1))
            self.assertEqual(ind.info('x'), pop.ancestor(idx, 1).info('x'))
            self.assertEqual(ind.info('y'), pop.ancestor(idx, 1).info('y'))
        #
        pop.pushAndDiscard(pop1)
        # setting ancestral pop should not matter
        pop.useAncestralPop(2)
        #
        for idx, ind in enumerate(pop1_c.individuals()):
            self.assertEqual(ind, pop.ancestor(idx, 1))
            self.assertEqual(ind.info('x'), pop.ancestor(idx, 1).info('x'))
            self.assertEqual(ind.info('y'), pop.ancestor(idx, 1).info('y'))
        # setting ancestral pop should not matter
        pop.useAncestralPop(1)
        for idx, ind in enumerate(pop_c.individuals()):
            self.assertEqual(ind, pop.ancestor(idx, 2))
            self.assertEqual(ind.info('x'), pop.ancestor(idx, 2).info('x'))
            self.assertEqual(ind.info('y'), pop.ancestor(idx, 2).info('y'))
        #
        pop.useAncestralPop(0)
        self.assertRaises(exceptions.IndexError, pop.ancestor, 10000, 2)
        self.assertRaises(exceptions.IndexError, pop.ancestor, 10000, 3)
        
if __name__ == '__main__':
    unittest.main()
