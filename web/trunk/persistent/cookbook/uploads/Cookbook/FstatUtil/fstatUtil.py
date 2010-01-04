#!/usr/bin/env python
#
# Purpose:
#     This python module provides several utility functions that save a simuPOP
#     Population in FSTAT formats,
#
# License:
#     This program is freely available in the simuPOP's online cookbook
#     (http://simupop.sourceforge.net/cookbook). You can redistribute it and/or
#     modify it freely, with or without this license notice. However, this
#     license notice should be present in the online version of this file.
#
#     This program is NOT part of simuPOP and is NOT protected by simuPOP's GPL
#     license. It is provided in the hope that it will be useful, but WITHOUT
#     ANY WARRANTY. If you notice any bug or have some new ideas, you can
#     modify this file and, as a courtesy to other simuPOP users, incoporate
#     your changes to the online version of this file. If you are uncertain
#     about your changes, please feel free to discuss your changes in the
#     simuPOP mailinglist (simupop-list@lists.sourceforge.net, subscription
#     required).
#
# Change Log:
#     2009-06-25 Bo Peng <bpeng@mdanderson.org>
#
#         Move functions SaveFStat and LoadFStat from simuUtil.py to the
#         online cookbook.
# 

from simuPOP import *
import re, exceptions

def saveFStat(pop, output='', maxAllele=0, loci=[], shift=1,
    combine=None):
    '''
    '''
    if output != '':
        file = output
    else:
        raise exceptions.ValueError, "Please specify output"
    # open file
    try:
        f = open(file, "w")
    except exceptions.IOError:
        raise exceptions.IOError, "Can not open file " + file + " to write."
    #
    # file is opened.
    np = pop.numSubPop()
    if np > 200:
        print "Warning: Current version (2.93) of FSTAT can not handle more than 200 samples"
    if loci == []:
        loci = range(pop.totNumLoci())
    nl = len(loci)
    if nl > 100:
        print "Warning: Current version (2.93) of FSTAT can not handle more than 100 loci"
    if maxAllele != 0:
        nu = maxAllele
    else:
        nu = max(pop.genotype()) + shift
    if nu > 999:
        print "Warning: Current version (2.93) of FSTAT can not handle more than 999 alleles at each locus"
        print "If you used simuPOP_la library, you can specify maxAllele in population constructure"
    if nu < 10:
        nd = 1
    elif nu < 100:
        nd = 2
    elif nu < 1000:
        nd = 3
    else: # FSTAT can not handle this now. how many digits?
        nd = len(str(nu))
    # write the first line
    f.write( '%d %d %d %d\n' % (np, nl, nu, nd) )
    # following lines with loci name.
    for loc in loci:
        #
        f.write( pop.locusName(loc) +"\n");
    gs = pop.totNumLoci()
    for sp in range(0, pop.numSubPop()):
        # genotype of subpopulation sp, individuals are
        # rearranged in perfect order
        gt = pop.genotype(sp)
        for ind in range(0, pop.subPopSize(sp)):
            f.write("%d " % (sp+1))
            p1 = 2*gs*ind          # begining of first hemo copy
            p2 = 2*gs*ind + gs     # second
            for al in loci: # allele
                # change from 0 based allele to 1 based allele
                if combine is None:
                    ale1 = gt[p1+al] + shift
                    ale2 = gt[p2+al] + shift
                    f.write('%%0%dd%%0%dd ' % (nd, nd) % (ale1, ale2))
                else:
                    f.write('%%0%dd' % nd % combine([gt[p1+al], gt[p2+al]]))
            f.write( "\n")
    f.close()


def loadFStat(file, loci=[]):
    '''load Population from fStat file 'file'
    since fStat does not have chromosome structure
    an additional parameter can be given
    '''
    try:
        f = open(file, "r")
    except exceptions.IOError:
        raise exceptions.IOError("Can not open file " + file + " to read.")
    #
    # file is opened. get basic parameters
    try:
        # get numSubPop(), totNumLoci(), maxAllele(), digit
        [np, nl, nu, nd] = map(int, f.readline().split())
    except exceptions.ValueError:
        raise exceptions.ValueError("The first line does not have 4 numbers. Are you sure this is a FSTAT file?")

    # now, ignore nl lines, if loci is empty try to see if we have info here
    # following lines with loci name.
    numLoci = loci
    lociNames = []
    if loci != []: # ignore allele name lines
        if nl != sum(loci):
            raise exceptions.ValueError("Given number of loci does not add up to number of loci in the file")
        for al in range(0, nl):
            lociNames.append(f.readline().strip() )
    else:
        scan = re.compile(r'\D*(\d+)\D*(\d+)')
        for al in range(0, nl):
            lociNames.append( f.readline().strip())
            # try to parse the name ...
            try:
                #print "mating ", lociNames[-1]
                ch,loc = map(int, scan.match(lociNames[-1]).groups())
                # get numbers?
                #print ch, loc
                if len(numLoci)+1 == ch:
                    numLoci.append( loc )
                else:
                    numLoci[ ch-1 ] = loc
            except exceptions.Exception:
                pass
        # if we can not get numbers correct, put all loci in one chromosome
        if sum(numLoci) != nl:
            numLoci = [nl]
    #
    # now, numLoci should be valid, we need number of population
    # and subpopulations
    maxAllele = 0
    gt = []
    for line in f.readlines():
        gt.append( line.split() )
    f.close()
    # subpop size?
    subPopIndex = map(lambda x:int(x[0]), gt)
    # count subpop.
    subPopSize = [0]*subPopIndex[-1]
    for i in range(0, subPopIndex[-1]):
        subPopSize[i] = subPopIndex.count(i+1)
    if len(subPopSize) != np:
        raise exceptions.ValueError("Number of subpop does not match")
    if sum(subPopSize) != len(gt):
        raise exceptions.ValueError("population size does not match")
    # we have all the information, create a population
    pop = Population(size=subPopSize, loci=numLoci, lociNames=lociNames)
    for idx, ind in enumerate(pop.individuals()):
        for locus in range(pop.totNumLoci()):
            for ploidy in [0,1]:
                ind.setAllele(int(gt[idx][locus+1][ploidy])-1, idx=locus, ploidy=ploidy)
    return pop


if __name__ == '__main__':
    # for testing
    # test func SaveFStat
    outfile = 'Fstatout.dat'
    pop = Population(size=[3,4,5], loci=[2,3],
                     lociNames=['loc1-1','loc1-2','loc2-1','loc2-2','loc2-3'])
    initByFreq(pop, [.1, .2, .3, .4])
    saveFStat(pop, outfile)
    print open(outfile).read()
    # load the saved population(in fStat format) into pop1(in simuPOP format) 
    pop1 = loadFStat('Fstatout.dat')
