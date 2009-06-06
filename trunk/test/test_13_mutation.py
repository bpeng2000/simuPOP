#!/usr/bin/env python
#
# Purpose:
#    testing of interfaces of mutators    of simuPOP
#
# Author:
#    Bo Peng (bpeng@rice.edu)
#
# $LastChangedRevision$
# $LastChangedDate$
#

import simuOpt
simuOpt.setOptions(quiet=True)

from simuPOP import *
import unittest, os, sys, exceptions

def getGenotype(pop, atLoci=[], subPop=[], indRange=[], atPloidy=[]):
    '''HIDDEN
    Obtain genotype as specified by parameters

        atLoci
            subset of loci, default to all

        subPop
            subset of subpopulations, default ao all

        indRange
            individual ranges

    This is mostly used for testing purposes because the returned
    array can be large for large populations.
    '''
    geno = []
    if type(atPloidy) == type(1):
        ploidy = [atPloidy]
    elif len(atPloidy) > 0:
        ploidy = atPloidy
    else:
        ploidy = range(0, pop.ploidy())
    if len(atLoci) > 0:
        loci = atLoci
    else:
        loci = range(pop.totNumLoci())
    gs = pop.genoSize()
    tl = pop.totNumLoci()
    if len(indRange) > 0:
        if type(indRange[0]) not in [type([]), type(())]:
            indRange = [indRange]
        arr = pop.genotype()
        for r in indRange:
            for i in range(r[0], r[1]):
                for p in ploidy:
                    for loc in loci:
                        geno.append( arr[ gs*i + p*tl + loc] )
    elif len(subPop) > 0:
        for sp in subPop:
            arr = pop.genotype(sp)
            for i in range(pop.subPopSize(sp)):
                for p in ploidy:
                    for loc in loci:
                        geno.append(arr[ gs*i + p*tl +loc])
    else:
        arr = pop.genotype()
        if len(ploidy) == 0 and len(atLoci) == 0:
            geno = pop.genotype()
        else:
            for i in range(pop.popSize()):
                for p in ploidy:
                    for loc in loci:
                        geno.append( arr[ gs*i + p*tl +loc] )
    return geno


class TestMutator(unittest.TestCase):

    def assertGenotype(self, pop, genotype,
        loci=[], subPops=[], indRange=[], atPloidy=[]):
        'Assert if the genotype of subPop of pop is genotype '
        geno = getGenotype(pop, loci, subPops, indRange, atPloidy)
        if AlleleType() == 'binary':
            if type(genotype) == type(1):
                self.assertEqual(geno, [genotype>0]*len(geno))
            else:
                self.assertEqual(geno, [x>0 for x in genotype])
        else:
            if type(genotype) == type(1):
                self.assertEqual(geno, [genotype]*len(geno))
            else:
                self.assertEqual(geno, genotype)

    def assertGenotypeFreq(self, pop, freqLow, freqHigh,
        loci=[], subPops=[], indRange=[], atPloidy=[]):
        'Assert if the genotype has the correct allele frequency'
        geno = getGenotype(pop, loci, subPops, indRange, atPloidy)
        if AlleleType() == 'binary':
            if len(freqLow) == 1:    # only one
                freq0 = geno.count(0)*1.0 / len(geno)
                self.assertTrue(freq0 >= freqLow[0] and freq0 <= freqHigh[0])
            else:
                f0 = [freqLow[0], sum(freqLow[1:])]
                f1 = [freqHigh[0], sum(freqHigh[1:])]
                freq0 = geno.count(0)*1.0 / len(geno)
                freq1 = geno.count(1)*1.0 / len(geno)
                #print f0,f1,freq0,freq1
                self.assertTrue(freq0 >= f0[0] and freq0 <= f1[0])
                self.assertTrue(freq1 >= f0[1] and freq1 <= f1[1])
        else:
            for i in range(len(freqLow)):
                freq = geno.count(i)*1.0 / len(geno)
                self.assertTrue(freq >= freqLow[i])
                self.assertTrue(freq <= freqHigh[i])


    def testUntouchedLoci(self):
        'Testing if mutator would mutate irrelevant locus'
        simu = simulator( population(size=1000, ploidy=2, loci=[2, 3]),
            randomMating() )
        simu.evolve(preOps = [initSex()],
            ops = [ kamMutator(k=2, rates=0.5, loci=[1,4])], gen=200)
        self.assertGenotype(simu.population(0), 0,
            loci=[0,2,3])

    def testsnpMutator(self):
        'Testing diallelic mutator (SNP mutator)'
        simu = simulator( population(size=1000, ploidy=2, loci=[2, 3]),
            randomMating(), rep=5)
        simu.evolve(
                preOps = [ initByFreq([.5, .5], loci=[0, 4])],
                ops = [snpMutator(u=0.1, loci=[0, 4]),
                    #stat(alleleFreq=[0, 4]),
                    #pyEval(r'"%.3f %.3f\n" % (alleleFreq[0][0], alleleFreq[4][0])')
                ],
                gen=100)
        self.assertGenotype(simu.population(0), 0,
            loci=[1, 2, 3])
        # fewer and fewer allele 0
        self.assertGenotypeFreq(simu.population(0),
            [0.], [0.05], loci=[0, 4])

    def testAlleleMapping(self):
        'Testing the allele mapping feature'
        simu = simulator(population(size=1000, ploidy=2, loci=[2, 3]),
            randomMating(), rep=5)
        simu.evolve(
                preOps = [initByFreq([0, 0, 0, 0, 0, .5, .5], loci=[0, 4])],
                ops = [snpMutator(u=0.1, loci=[0, 4],
                    mapIn=[0, 0, 0, 0, 0, 0, 1],
                    mapOut=[5, 6]),
                    #stat(alleleFreq=[0, 4]),
                    #pyEval(r'"%.3f %.3f\n" % (alleleFreq[0][5], alleleFreq[4][5])')
                ],
                gen=100)
        self.assertGenotype(simu.population(0), 0,
            loci=[1, 2, 3])
        # fewer and fewer allele 0
        self.assertGenotypeFreq(simu.population(0),
            [0, 0, 0, 0, 0, 0, 0.95], [0, 0, 0, 0, 0, 0.05, 1], loci=[0, 4])
        #
        def mapIn(allele):
            return allele - 5
        def mapOut(allele):
            return allele + 5
        simu = simulator(population(size=1000, ploidy=2, loci=[2, 3]),
            randomMating(), rep=5)
        simu.evolve(
                preOps = [initByFreq([0, 0, 0, 0, 0, .5, .5], loci=[0, 4])],
                ops = [snpMutator(u=0.1, loci=[0, 4],
                    mapIn=mapIn, mapOut=mapOut),
                    #stat(alleleFreq=[0, 4]),
                    #pyEval(r'"%.3f %.3f\n" % (alleleFreq[0][5], alleleFreq[4][5])')
                ],
                gen=100)
        self.assertGenotype(simu.population(0), 0,
            loci=[1, 2, 3])
        # fewer and fewer allele 0
        self.assertGenotypeFreq(simu.population(0),
            [0, 0, 0, 0, 0, 0, 0.95], [0, 0, 0, 0, 0, 0.05, 1], loci=[0, 4])



    def testKamMutator(self):
        'Testing k-allele mutator'
        simu = simulator( population(size=1000, ploidy=2, loci=[2, 3]),
            randomMating(), rep=5)
        # simu.apply( [ initByFreq([.2,.8])])
        simu.evolve(
                preOps = [ initByFreq([.2,.8])],
                ops = [ kamMutator(k=2, rates=0.1)],
                gen=200)
        # at loci
        simu = simulator( population(size=10000, ploidy=2, loci=[2, 3]),
            randomMating(), rep=5)
        simu.evolve(
            preOps = [initSex()],
            ops = [ kamMutator(k=2, rates=0.1, loci=[0,4])],
            gen = 1)
        # frequency seems to be OK.
        self.assertGenotypeFreq(simu.population(0),
            [0.85],[0.95], loci=[0,4])
        self.assertGenotype(simu.population(0), 0,
            loci=[1,2,3])

    def testSmmMutator(self):
        'Testing generalized step-wise mutation mutator'
        if AlleleType() == 'binary':
            return
        simu = simulator( population(size=1000, ploidy=2, loci=[2, 3]),
            randomMating(), rep=5)
        # simu.apply( [ initByFreq([.2,.8])])
        simu.evolve(preOps=[initByFreq([.2,.8])],
             ops = [ smmMutator(rates=0.2)], gen=200)
        # at loci
        simu = simulator( population(size=10000, ploidy=2, loci=[2, 3]),
            randomMating(), rep=5)
        simu.evolve(preOps = [initSex()],
            ops = [ smmMutator(rates=0.2, loci=[0,4])],
            gen = 1)
        # frequency seems to be OK.
        self.assertGenotypeFreq(simu.population(0),
            [0.85],[0.95], loci=[0,4])
        self.assertGenotype(simu.population(0), 0,
            loci=[1,2,3])


    def testPyMutator(self):
        pop = population(size=10, loci=[2])
        # cutom mutator
        def mut(x):
            return 1
        m = pyMutator(rate=1, func=mut)
        m.apply(pop)
        assert pop.individual(0).allele(0) == 1, \
            "PyMutator failed"

    def testMutationCount(self):
        N = 10000
        r = [0.001, 0.002, 0.003]
        G = 100
        pop = population(size=N, ploidy=2, loci=[5])
        simu = simulator(pop, randomMating())
        mut = kamMutator(k = 10, rates=r, loci=[0,2,4])
        simu.evolve(preOps = [initSex()],
            ops = [mut],
            gen=G)
        assert abs( mut.mutationCounts()[0] - 2*N*r[0]*G) < 200, \
            "Number of mutation event is not as expected."
        assert abs( mut.mutationCounts()[2] - 2*N*r[1]*G) < 200, \
            "Number of mutation event is not as expected."
        assert abs( mut.mutationCounts()[4] - 2*N*r[2]*G) < 200, \
            "Number of mutation event is not as expected."
        self.assertEqual( mut.mutationCounts()[1], 0)
        self.assertEqual( mut.mutationCounts()[3], 0)

    def testPointMutator(self):
        # test point mutator
        pop = population(size=10, ploidy=2, loci=[5])
        InitByValue(pop, value=[[1]*5, [2]*5], proportions=[.3,.7])
        PointMutate(pop, inds=[1,2,3], toAllele=0, loci=[1,3])
        assert pop.individual(1).allele(1,0) == 0
        assert pop.individual(1).allele(1,1) != 0
        PointMutate(pop, inds=[1,2,3], atPloidy=[1],
            toAllele=0, loci=[1,2])
        assert pop.individual(1).allele(2,1) == 0
        assert pop.individual(1).allele(2,0) != 0

if __name__ == '__main__':
    unittest.main()
