#!/usr/bin/env python
#
# Purpose:    generate dataset for common complex disease 
#             with certain number of disease susceptibility
#             loci.
#
# Bo Peng (bpeng@rice.edu)
#
# $LastChangedDate: 2005-10-31 17:29:34 -0600 (Mon, 31 Oct 2005) $
# $Rev: 78 $
#
# Known bugs:
#     None
# 

"""

Introduction
=============

This program analyze the dataset generated by simuComplexDisease.py. This, and
the functions in simuUtil.py provides examples of how to analyze populations,
using the popular affected sibpair and case control sample, and Linkage TDT and
association tests. This script will

    1. Apply single or multi-locus penetrance function to determine 
       affectedness of each individual. Note that the penetrance model would
       better be compatible to the fitness model. You would not want to assign
       affectedness to individuals according to disease susceptibility locus 
       (DSL) one while selection was working on DSL two.
    2. Draw case control and affected sibpair samples and save in simuPOP
       and Linkage format respectively, using given sample sizes.
    3. If geneHunter is available, it will be used to analyze affected sibpair 
       samples using TDT and Linkage method. Association mapping will also be
       done for SNP datasets if rpy is available.

Please refer to simuComplexDisease.py and see how the dataset is generated.

The program is written in Python using simuPOP modules. For more information,
please visit simuPOP website http://simupop.sourceforge.net .


Penetrance
==========

Since we assume that fitness only depends on genotype, not affectedness status,
we do not care who are affected during evolution. This has to change at the 
last generation where different sampling schemes will be applied to the 
population. Several customizable penetrance schemes will be used. As a matter
of fact, if there is no selection against any DS allele, we can use any
of the penetrance functions:

    1. recessive single-locus and heterogeneity multi-locus model: 
       At DSL i, penetrance P_i will be computed as
           0, 0, p_i
       for genotype
           AA, Aa, aa    (A is wild type)
       where p_i are penetrance factors (that can vary between DSL).

       The overall penetrance is 
           1 - Prod(1-P_i)
    
    2. additive single-locus and heterogeneity multi-locus model: 
       For each DSL, the penetrance P_i is
            0, p_i/2, p_i
       for genotype
            AA, Aa, aa
       where the overall penetrance takes the form of
            1 - Prod( 1- P_i)
       This is the heterogeneity model proposed by Neil Risch (1990).
         
    3. Customized, you can write your own penetrance function. Which means that 
       you will have to modify analComplexDisease.py itself.
    

Samples and Output
==================

Different kinds of samples will be draw from the final large population.

    1. population based case control sample: 
       Regardless of family structure, N cases and N controls will
       be drawn randomly.
    
    2. affected and unaffected sibpairs:
       N/4 affected and N/4 unaffected (sibling) families (two siblings and
       two parents) will be drawn. (Sample size is N cases and N controls
       when counting individuals.)

The datasets are saved in native simuPOP format and in Linkage format.
DSL markers are removed so there will be no marker that is directly 
linked to the disease.

All files are put under a specified folder. They are organized by
penetrance methods. The result will be written in a file result.sav
which can be loaded into python using the pickle module.


Gene mapping
============

If the location of genehunter is specified. It will be applied to all affected
sibpair samples. If R/Rpy is availablem, the basic chi-sq assocition tests will
be applied to case control samples. No adjustment for multiple testing is done.
For details about how gene mapping is done. please read relevant functions in 
simuUtil.py.

Note:

This script can be used to process populations directly, or be imported as 
a python module so that you can call analyzePopulation function directly.


Output:
=======

The results are saved in a file that can be execfile'ed (or imported) by python.
For example, if you choose additive penetrance function, the output file
additive.py has contents like

    # DSL locations (samples do not have DSL)
    DSL = [10, 300, 350]
    # ...

Please read the comment before each variable for details about them.

"""

import simuOpt, simuUtil
import os, sys, types, exceptions, os.path, operator, time
#
# declare all options. getParam will use these information to get parameters
# from a tk/wxPython-based dialog, command line, config file or user input
#
# detailed information about these fields is given in the simuPOP reference
# manual.
options = [
    {'arg': 'h',
     'longarg': 'help',
     'default': False, 
     'description': 'Print this usage message.',
     'allowedTypes': [types.NoneType, type(True)],
     'jump': -1                    # if -h is specified, ignore any other parameters.
    },
    {'longarg': 'markerType=',
     'default': 'SNP',
     'allowedTypes': [types.StringType],
     'label': 'Marker type used',
     'description': '''Marker type used to generated the sample. This is
        important since the file formats are not compatible between 
        binary and standard simuPOP modules''',
     'validate':    simuOpt.valueOneOf([ 'microsatellite', 'SNP']),
     'chooseOneOf': ['microsatellite', 'SNP']
    }, 
    {'longarg': 'dataset=',
     'default': 'simu.txt',
     'allowedTypes': [types.StringType],
     'label': 'Dataset to analyze',
     'description': 'Dataset generated by simuComplexDisease.py. ',
     'validate':    simuOpt.valueValidFile()
    },
    {'longarg': 'peneFunc=',
     'default': 'additive',
     'label': 'Penetrance function',
     'allowedTypes': [types.StringType],
     'description': ''' Penetrance functions to be applied to the final
        population. Two penetrance fucntions are provided, namely recessive
        or additive single-locus model with heterogeneity multi-locus model. 
        You can define another customized penetrance functions by modifying
        this script. ''',
     'validate':    simuOpt.valueOneOf(['recessive', 'additive', 'custom']),
     'chooseOneOf': [ 'recessive', 'additive', 'custom']
    },
    {'longarg': 'penePara=',
     'default': [0.5],
     'label': 'Penetrance parameters',
     'description': '''Penetrance parameter for all DSL. An array of parameter 
        can be given to each DSL. The meaning of this parameter differ by 
        penetrance model. For a recessive model, the penetrance is 0,0,p for 
        genotype AA,Aa,aa (a is disease allele) respectively. For an additive 
        model, the penetrance is 0,p/2,p respectively.''',
     'allowedTypes': [types.ListType, types.TupleType],
     'validate':   simuOpt.valueOneOf([ 
             simuOpt.valueBetween(0,1), simuOpt.valueListOf(simuOpt.valueBetween(0,1))] )
    },
    {'longarg': 'sampleSize=',
     'default': 800,
     'label':    'Sample size',
     'allowedTypes':    [types.IntType, types.LongType],
     'description':    '''Size of the samples, that will mean N/4 affected 
        sibpair families (of size 4), N/2 cases and controls etc. ''',
     'validate':    simuOpt.valueGT(1)
    },
    {'longarg': 'numSample=',
     'default': 2,
     'label':    'Sample number',
     'allowedTypes':    [types.IntType, types.LongType],
     'description':    '''Number of samples to draw for each penetrance function. ''',
     'validate':    simuOpt.valueGT(0)
    },
    {'longarg': 'outputDir=',
     'default': '.',
     'allowedTypes': [types.StringType],
     'label': 'Output directory',
     'description': 'Directory into which the datasets will be saved. ',
     'validate':    simuOpt.valueValidDir()
    },
    {'longarg': 'loci=',
     'default': [],
     'allowedTypes': [types.TupleType, types.ListType],
     'label': 'Loci of concern',
     'description': '''Loci at which p-values will be calculated and returned. Use
        [] to return p-values for all loci (excluging DSL)''',
     'validate':    simuOpt.valueListOf(simuOpt.valueGE(0))
    },
    {'longarg': 'geneHunter=',
     'default': 'gh',
     'allowedTypes': [types.StringType],
     'label': 'Location of gene hunter',
     'description': '''Location of gene hunter executable. If provided,
        the TDT and Linkage method of genehunter will be applied to 
        affected sibpair samples.'''
    },
    {'longarg': 'mappingMethods=',
     'default': ['TDT', 'Linkage'],
     'label': 'Gene mapping methods',
     'allowedTypes': [types.TupleType, types.ListType],
     'description': ''' Gene mapping methods to apply. geneHunter is needed for
        TDT and Linkage methods, and R/RPy are needed for chisq association 
        tests.''',
     'allowedTypes': [types.ListType, types.TupleType],
     'validate':    simuOpt.valueListOf( simuOpt.valueOneOf(['TDT', 'Linkage', 'Association'])),
     'chooseFrom': [ 'TDT', 'Linkage', 'Association']
    },
    # another two hidden parameter
    {'longarg': 'reAnalyzeOnly=',
     'default': False,
     'allowedTypes': [type(True)],
     'description': '''If given in command line, redo the analysis.'''
    },
    {'longarg': 'saveConfig=',
     'default': 'anal.cfg',
     'allowedTypes': [types.StringType, types.NoneType],
     'label': 'Save configuration',
     'description': 'Save current paremeter set to specified file.'
    },
    {'arg': 'v',
     'longarg': 'verbose',
     'default': False,
     'allowedTypes': [types.NoneType, types.IntType],
     'description': 'Verbose mode.'
    },
]

outputVars = {
    # basic information
    'dataset': 'name of the datafile',
    'logfile': 'Name of the log file generated by simuComplexDisease.py',
    'DSL': 'Location of DSL in the populations. (They are removed from the samples.)',
    # evolution related parameters
    'numSubPop': 'Number of subpopulation',
    'recRate': 'recombination rate',
    'initSize': 'Size of initial founder population',
    'endingSize': 'Population size of the last generation',
    'burninGen': 'Length of burnin stage',
    'splitGen': 'Generation at which population is split to subpopulations',
    'mixingGen': 'Generation at which migration is allowed',
    'endingGen': 'total evolution length',
    'migrModel': 'migration model',
    'migrRate': 'migration rate',
    'mutaModel': 'mutation model',
    'mutaRate': 'mutation rate',
    # population statistics
    'Fst': 'F_st: measure of population differentiation',
    'Fis': 'F_is',
    'Fit': 'F_it',
    'AvgFst': 'Average of F_st estimated from all loci',
    'AvgFis': 'Average of F_is estimated from all loci',
    'AvgFit': 'Average of F_it estimated from all loci',
    'AvgHetero': 'Averge heterozygosity',
    'Fprime': '',
    'K': 'Disease prevalence (penetrance dependent)',
    'Ks': 'Sibling recurrence risk',
    'Ls': 'Sibling recurrence risk ratio', 
    'P11': 'Pr( (N,N) | affected ): proportion of NN (normal) genotype among affected individuals',
    'P12': 'Pr( (N,S) | affected ): proportion of NS (normal, susceptible) or SN genotype among affected individuals',
    'P22': 'Pr( (S,S) | affected ): proportion of SS (susceptible) genotype among affected individuals',
    'LD': 'Linkage disequilibrium',
    'LD_prime': "D' measure of Linkage disequilibrium",
    'R2': 'R^2 measure of Linkage disequilibrium',
    'alleleFreq': 'allele frequency, including DSL',    
    # result of gene mapping methods
    'LOD': 'p-values obtained using Linkage method, organized by sample, chromosome and loci (nested list)',
    'TDT': 'p-values obtained using TDT method, organized by sample, chromosome and loci (nested list)',
    'ChiSq': 'p-values obtained using ChiSq method, organized by sample, chromosome and loci',
}

# penetrance generator functions. They will return a penetrance function
# with given penetrance parameter
def recessive(pen):
    ''' recessive single-locus, heterogeneity multi-locus '''
    def func(geno):
        val = 1
        for i in range(len(geno)/2):
            if geno[i*2] + geno[i*2+1] == 2:
                val *= 1 - pen[i]
        return 1-val
    return func
    

def additive(pen):
    ''' additive single-locus, heterogeneity multi-locus '''
    def func(geno):
        val = 1
        for i in range(len(geno)/2):
            val *= 1 - (geno[i*2]+geno[i*2+1])*pen[i]/2.
        return 1-val
    return func


# if you need some specialized penetrance function, modify this
# function here.
# NOTE:
# 
# 1. geno is the genptype at DSL. For example, if your DSL is [5,10]
#     geno will be something like [0,1,1,1] where 0,1 is the genotype at 
#     locus 5 and 1,1 is the genotype at locus 10.
# 2. in simuComplexDisease.py, 0 is wild type, 1 is disease allele.
def custom(pen):
    ''' a penetrance function that focus on the first DSL '''
    def func(geno):
        return 1
    return func


def getOptions(details=__doc__):
    ''' get options from options structure,
        if this module is imported, instead of ran directly,
        user can specify parameter in some other way.
    '''
    # get all parameters, __doc__ is used for help info
    allParam = simuOpt.getParam(options, 
        '''    This program simulates the evolution of a complex common disease, subject 
     to the impact of mutation, migration, recombination and population size change. 
     Click 'help' for more information about the evolutionary scenario.''', details, nCol=2)
    # when user click cancel ...
    if len(allParam) == 0:
        sys.exit(1)
    # -h or --help
    if allParam[0]:    
        print simuOpt.usage(options, __doc__)
        sys.exit(0)
    # --saveConfig
    simuOpt.saveConfig(options, allParam[-2], allParam)
    # --verbose or -v (these is no beautifying of [floats]
    if allParam[-1]:                 # verbose
        simuOpt.printConfig(options, allParam)
    # return the rest of the parameters
    return allParam[1:-2]



def drawCaseControlSamples(pop, numSample, dirPrefix, reAnalyzeOnly):
    ''' 
        pop: population
        numSample: number of samples for each penetrance settings
        dirPrefix: where to save samples, dirPrefix0/caseControltxt etc
            will be used.
        reAnalyzeOnly: load populations only
    '''
    samples = []
    if reAnalyzeOnly:
        for ns in range(numSample):
            sampleFile = os.path.join('%s%d' % (dirPrefix, ns), 'caseControl.txt')
            print "Loading sample ", ns+1, ' of ', numSample
            try:
                samples.append(LoadPopulation(sampleFile))
            except Exception, err:
                print "Can not load exisiting sample. Can not use --reAnalyzeOnly option"
                raise err
    else:
        print "Generating case control samples..."
        # get number of affected
        Stat(pop, numOfAffected=True)
        print "Number of affected individuals: ", pop.dvars().numOfAffected
        print "Number of unaffected individuals: ", pop.dvars().numOfUnaffected
        nCase = min(pop.dvars().numOfAffected , N/2)
        nControl = min(pop.dvars().numOfUnaffected, N/2)
        try:
            samples = CaseControlSample(pop, nCase, nControl, times=numSample)
        except Exception, err:
            print "Can not draw case control sample. "
            print type(err), err
        for ns in range(len(samples)):
            # if N=800, 400 case and 400 controls
            # remove DSL
            samples[ns].removeLoci(remove=pop.dvars().DSL)
            sampleFile = os.path.join('%s%d' % (dirPrefix, ns), "caseControl.txt")
            _mkdir('%s%d' % (dirPrefix, ns))
            print "Write case-control sample %s in simuPOP format: %s" % (ns, sampleFile)
            samples[ns].savePopulation(sampleFile)
    return samples


def drawAffectedSibpairSamples(pop, numSample, dirPrefix, reAnalyzeOnly):
    ''' 
        pop: population
        numSample: number of samples for each penetrance settings
        dirPrefix: dirPrefix0, 1, etc will be used as directories
        reAnalyzeOnly: load populations only
    '''
    # get allele frequency of no-DSL markers
    af = []
    Stat(pop, alleleFreq=range(pop.totNumLoci()))
    # remember that we will remove DSL, so their allelefreq should 
    # be removed.
    for x in range( pop.totNumLoci() ):
        if x not in pop.dvars().DSL:
            af.append( pop.dvars().alleleFreq[x] )
    # 
    samples = []
    if reAnalyzeOnly:
        for ns in range(numSample):
            sampleFile = os.path.join('%s%d' % (dirPrefix, ns), 'affectedSibpairs.txt')
            print "Loading sample ", ns+1, ' of ', numSample
            try:
                samples.append(LoadPopulation(sampleFile))
            except Exception, err:
                print "Can not load exisiting sample. Can not use --reAnalyzeOnly option"
                raise err
    else:
        print "Generating affected sibpair samples..."
        try:
            # get number of affected/unaffected sibpairs
            # There may not be enough to be sampled
            AffectedSibpairSample(pop, countOnly=True)
            nAff = min(pop.dvars().numAffectedSibpairs, N/4)
            print "Number of (both) affected sibpairs: ", pop.dvars().numAffectedSibpairs
            samples = AffectedSibpairSample(pop, name='sample1',
                    size=nAff, times=numSample)
        except Exception, err:
            print type(err)
            print err
            print "Can not draw affected sibpars."
        # svae in simuPOP and linkage format
        for ns in range(numSample):
            sampleFile = os.path.join('%s%d' % (dirPrefix, ns), "affectedSibpairs.txt")
            _mkdir('%s%d' % (dirPrefix, ns))
            # remove DSL
            samples[ns].removeLoci(remove=pop.dvars().DSL)
            print "Write affected sibpair sample in simuPOP format: %s " % sampleFile
            samples[ns].savePopulation(sampleFile)
            linDir = os.path.join('%s%d' % (dirPrefix, ns), "Linkage")
            _mkdir(linDir)
            for ch in range(0, pop.numChrom() ):
                print "Write to chromosome %d in Linkage format: %s/Aff_%d" % (ch, linDir, ch)
                SaveLinkage(pop=samples[ns], popType='sibpair', output = linDir+"/Aff_%d" % ch,
                    chrom=ch, recombination=pop.dvars().recRate[0],
                    alleleFreq=af, daf=0.1)                
    return samples


# create output directory if necessary
# a more friendly version of mkdir
def _mkdir(d):
    try:
        if not os.path.isdir(d):
            os.makedirs(d)
        if not os.path.isdir(d):
            raise
    except:
        print "Can not make output directory ", d
        sys.exit(1)


def popStat(pop):
    'Calculate population statistics '
    # K -- populaiton prevalance
    print "Calculating population statistics "
    Stat(pop, numOfAffected=True)
    result = {}
    result['K'] = pop.dvars().numOfAffected * 1.0 / pop.popSize()
    # P11 = [ ] = proportion of 11 | affected, 
    # P12 = [ ] = proportion of 12 | affected
    DSL = pop.dvars().DSL
    P11 = [0.]*len(DSL)
    P12 = [0.]*len(DSL)
    P22 = [0.]*len(DSL)
    for ind in range(pop.popSize()):
        if pop.individual(ind).affected():
            for x in range(len(DSL)):
                s1 = pop.individual(ind).allele(DSL[x], 0)
                s2 = pop.individual(ind).allele(DSL[x], 1)
                if s1 == 0 and s2 == 0:
                    P11[x] += 1
                elif s1 == 1 and s2 == 1:
                    P22[x] += 1
                else:
                    P12[x] += 1
                    
    N = pop.dvars().numOfAffected
    result['P11'] = [ x/N for x in P11 ]
    result['P12'] = [ x/N for x in P12 ]
    result['P22'] = [ x/N for x in P22 ]
    result['Fprime'] = [ (P12[x]/2. + P22[x])/N for x in range(len(DSL)) ]
    # Ks = Pr(Xs=1 | Xp=1 ) = Pr(Xs=1, Xp=1) | P(Xp=1)
    Xsp = 0.
    for ind in range(pop.popSize()/2):
        s1 = pop.individual(ind*2).affected()
        s2 = pop.individual(ind*2+1).affected()
        if s1 and s2:
            Xsp += 1
    result['Ks'] = 2*Xsp / pop.dvars().numOfAffected
    # Lambda = Ks/K
    result['Ls'] = result['Ks'] / result['K']
    return result
     
    
def analyzePopulation(dataset, peneFunc, penePara, N, 
        numSample, outputDir, loci, geneHunter, mappingMethods, reAnalyzeOnly):
    '''
    This function organize all previous functions and
        1. Load a population
        2. apply different kinds of penetrance functions
        3. draw sample
        4. save samples
        5. apply TDT, Linkage and chi-sq tests
        6. return a result dictionary
    '''
    res = {}
    # load population
    print "Loading population %s " % dataset
    pop = LoadPopulation(dataset)
    # If you decide to have a look at penetrance values
    # add the following line, and add infoFields=['penetrance'] to
    # penetrance operators
    #
    # pop.addInfoField('penetrance')
    #
    res.update({
        'dataset':  dataset,
        'logfile':  dataset[0:-4] + '.log',
        'alleleFreq':   [1- pop.dvars().alleleFreq[i][0] for i in pop.dvars().DSL],
        'pene==Func':   peneFunc,
    })
    # get all the variables from pop
    res.update(pop.vars())
    #
    # apply penetrance
    nDSL = len(pop.dvars().DSL)
    if len(penePara) == 1:
        para = penePara * nDSL
    elif len(penePara) == nDSL:
        para = penePara
    else:
        print "Length of penetrance parameter should be one or the number of DSL"
        sys.exit(0)
    if 'recessive' == peneFunc:
        print "Using recessive penetrance function"
        func = recessive(para)
    elif 'additive' == peneFunc:
        print "Using additive penetrance function"
        func = additive(para)
    elif 'custom' == peneFunc:
        print "Using customized penetrance function"
        func = custom(para)    
    else:
        print "Wrong penetrance function %s " % peneFunc
        sys.exit(1)
    # set affectedness for all individuals, including ancestors
    for i in range(0, pop.ancestralDepth()+1):
        # apply penetrance function to all current and ancestral generations
        pop.useAncestralPop(i)
        PyPenetrance(pop, loci=pop.dvars().DSL, func=func)
    # reset population to current generation.
    pop.useAncestralPop(0)
    #
    # now, draw samples 
    # return a sample population, for its chromosome structure
    # (without DSL)
    caseControlSamples = drawCaseControlSamples(pop, 
        numSample,        # number of sample for each setting
        os.path.join(outputDir, peneFunc),   # prefix of dir names
        reAnalyzeOnly     # whether or not load sample directly
    )
    affctedSibpairSamples = drawAffectedSibpairSamples(pop, 
        numSample,        # number of sample for each setting
        os.path.join(outputDir, peneFunc),   # prefix of dir names
        reAnalyzeOnly     # whether or not load sample directly
    )
    # calculate population statistics like prevalence
    res.update( popStat(pop) )
    #
    def lociAtChrom(ch, absLoci=[]):
        if absLoci == []:
            # all loci (compared to pop, we do not have the DSL)
            return range(caseControlSamples[0].numLoci(ch))
        loci = []
        for loc in absLoci:
            (c, l) = caseControlSamples[0].chromLocusPair(loc)
            if c == ch:
                loci.append(l)
        return loci           
    # for each sample
    res['TDT'] = []
    res['LOD'] = []
    res['ChiSq'] = []
    for sn in range(numSample):
        res['TDT'].append([])
        res['LOD'].append([])
        res['ChiSq'].append([])
        print "Processing sample %s%d" % (peneFunc, sn)
        for ch in range(pop.numChrom()):
            if 'TDT' in mappingMethods:
                print 'Applying TDT method to chromosome %d of sample %d' % (ch, sn)
                res['TDT'][sn].extend(TDT_gh(
                    os.path.join(outputDir, '%s%d' % (peneFunc, sn), 'Linkage', 'Aff_%d' % ch), 
                    loci=lociAtChrom(ch, loci), gh=geneHunter))
            if 'Linkage' in mappingMethods:
                print 'Applying Linkage method to chromosome %d of sample %d' % (ch, sn)
                res['LOD'][sn].extend(LOD_gh(
                    os.path.join(outputDir, '%s%d' % (peneFunc, sn), 'Linkage', 'Aff_%d' % ch), 
                    loci=lociAtChrom(ch, loci), gh=geneHunter))
        if 'Association' in mappingMethods:
            print 'Applying chi-sq association tests to sample %d' % sn
            res['ChiSq'][sn] = ChiSq_test(
                os.path.join(outputDir, '%s%d' % (peneFunc, sn), 'caseControl.txt'), 
                loci=loci)
    return res


if __name__ == '__main__':
    allParam = getOptions()
    # unpack options
    (markerType, dataset, peneFunc, penePara, N, numSample, outputDir,
        loci, geneHunter, mappingMethods, reAnalyzeOnly) = allParam
    # load simuPOP libraries
    if markerType == 'microsatellite':
        simuOpt.setOptions(alleleType='short', quiet=True)
    else:
        simuOpt.setOptions(alleleType='binary', quiet=True)
    #
    from simuPOP import *
    from simuUtil import *
    #
    res = analyzePopulation(dataset,
        peneFunc, penePara, N, numSample, outputDir, 
        loci, geneHunter, mappingMethods, reAnalyzeOnly)
    print
    print "Writing results to file %s/%s.py" % (outputDir, peneFunc)
    resFile = open(os.path.join(outputDir, '%s.py' % peneFunc), 'w')
    print >> resFile, "# analysis of population %s, at %s" % (dataset, time.asctime())
    print >> resFile
    for key in outputVars.keys():
        if res.has_key(key):
            # description
            print >> resFile, '# %s' % outputVars[key]
            if type(res[key]) == type(''):
                print >> resFile, '%s = "%s"' % (key, res[key])
            else:
                print >> resFile, '%s = %s' % (key, str(res[key]))
            print >> resFile
    resFile.close()
    print 'Done'



