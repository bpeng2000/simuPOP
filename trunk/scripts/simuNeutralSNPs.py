#!/usr/bin/env python
#
# Purpose:    simulate the forming and detecton of recombination
#     hotspots.
#
# Bo Peng (bpeng@rice.edu)
#
# $LastChangedDate: 2005-10-20 15:26:39 -0500 (Thu, 20 Oct 2005) $
# $Rev: 72 $
#
# Known bugs:
#     None
# 

"""

Introduction
=============

This program simulates the evolution of a chromosome with SNP markers, under 
the influence of mutation, migration, recombination and population size 
change. Starting from a small founder population, each simulation will go
through the following three stages:

    1. Burn-in the population with mutation and recombination
    2. Split and grow the population without migration
    3. Mix subpopulations at given migration level

Steps 2 and 3 are optional in the sense that you can manipulate the parameters
to simulate constant populations without population structure.

The program is written in Python using simuPOP modules. For more information,
please visit simuPOP website http://simupop.sourceforge.net .

"""

import simuOpt
simuOpt.setOptions(quiet=True, alleleType='binary')

from simuPOP import *
from simuUtil import *
import os, sys, types, exceptions, os.path 

try:
    from simuRPy import *
    hasRPy = True
except:
    print "RPy module not found. Can not plot histogram of allele frequency"
    hasRPy = False
#
# declare all options. getParam will use these information to get parameters
# from a tk/wxPython-based dialog, command line, config file or user input
#
# details about these fields is given in the simuPOP reference manual.
options = [
    {'arg': 'h',
     'longarg': 'help',
     'default': False, 
     'description': 'Print this usage message.',
     'allowedTypes': [types.NoneType, type(True)],
     'jump': -1                    # if -h is specified, ignore any other parameters.
    },
    {'longarg': 'numLoci=',
     'default': 200,
     'configName': 'Number of SNP loci',
     'prompt': 'Number of SNP loci (200):    ',
     'description': 'Number of SNP loci',
     'allowedTypes': [types.IntType, types.LongType],
     'validate':    simuOpt.valueGT(0)
    },
    {'longarg': 'lociPos=',
     'default': [],
     'configName': 'Loci position',
     'prompt': 'Loci position ([]):    ',
     'description': '''Loci position on the chromosome. Assumed to be in kb
        the unit is not important.''',
     'allowedTypes': [types.ListType, types.TupleType],
     'validate':    simuOpt.valueListOf(types.FloatType)
    },
    {'longarg': 'initSize=',
     'default': 1000,
     'configName': 'Initial population size',
     'allowedTypes': [types.IntType, types.LongType],
     'prompt': 'Initial Population size (1000):    ',
     'description': '''Initial population size. This size will be maintained
        till the end of burnin stage''',
     'validate':    simuOpt.valueGT(0)
    },
    {'longarg': 'finalSize=',
     'default': 100000,
     'configName': 'Final population size',
     'prompt': 'Final population size (sum of all subpopulations) (100000): ',
     'allowedTypes': [types.IntType, types.LongType],
     'description': 'Final population size after population expansion.',
     'validate':    simuOpt.valueGT(0)
    }, 
    {'longarg': 'burnin=',
     'default': 1000,
     'configName': 'Length of burn-in stage',
     'allowedTypes': [types.IntType],
     'prompt': 'Length of burn in stage (1000):    ',
     'description': 'Number of generations of the burn in stage.',
     'validate':    simuOpt.valueGT(0)
    },
    {'longarg': 'noMigrGen=',
     'default': 1500,
     'configName': 'Length of split-and-grow stage',
     'prompt': 'Length of split-and-grow stage    (1500):    ',
     'allowedTypes': [types.IntType, types.LongType],
     'description': '''Number of generations when migration is zero. This stage
                is used to build up population structure.''',
     'validate':    simuOpt.valueGT(0)
    },
    {'longarg': 'mixingGen=',
     'default': 50,
     'configName': 'Length of mixing stage',
     'allowedTypes': [types.IntType, types.LongType],
     'prompt': 'Length of mixing stage (population admixing) (50):    ',
     'description': '''Number of generations when migration is present. This stage
                will mix individuals from subpopulations using an circular stepping stone
                migration model.''',
     'validate':    simuOpt.valueGT(0)
    },
    {'longarg': 'growth=',
     'default': 'exponential',
     'configName': 'Population growth model',
     'prompt': 'Population growth style, linear or exponential. (exponential):    ',
     'description': '''How population is grown from initSize to finalSize.
                Choose between linear and exponential''',
     'chooseOneOf': ['exponential', 'linear'],
    },
    {'longarg': 'numSubPop=',
     'default': 5,
     'configName': 'Number of subpopulations to split',
     'allowedTypes': [types.IntType],
     'prompt': 'Number of subpopulations to split (5): ',
     'description': 'Number of subpopulations to be split into after burnin stage.',
     'validate':    simuOpt.valueGT(0)
    },
    {'longarg': 'migrModel=',
     'default': 'stepping stone',
     'configName': 'Migration model',
     'prompt': 'Migration model. (stepping stone):    ',
     'allowedTypes': [types.StringType],
     'description': '''Migration model. Choose between stepping stone (circular),
                island and none. ''',
     'validate':    simuOpt.valueOneOf(['island', 'stepping stone', 'none']),
     'chooseOneOf': ['stepping stone', 'island', 'none']
    }, 
    {'longarg': 'migrRate=',
     'default': 0.,
     'configName': 'Migration rate',
     'prompt': 'Migration rate during mixing stage. (0.) ',
     'description': '''Migration rate during mixing stage. ''',
     'allowedTypes': [types.IntType, types.FloatType],
     'validate':    simuOpt.valueBetween(0,1)
    },
    {'longarg': 'mutaRate=',
     'default': 1e-4,
     'configName': 'Mutation rate',
     'prompt': 'Mutation rate. (1e-4):    ',
     'allowedTypes': [types.IntType, types.FloatType],
     'description': '''Mutation rate''',
     'validate': simuOpt.valueBetween(0,1)
    },
    {'longarg': 'recRate=',
     'default': [1e-4],
     'configName': 'Recombination rate',
     'allowedTypes': [types.ListType, types.TupleType],
     'prompt': 'Recombination rate between adjacent markers. (1e-4):',
     'description': '''Recombination rate between adjacent markers. 
        It can be a number or a list with length numLoci-1''',
     'validate':    simuOpt.valueListOf( simuOpt.valueBetween(0,1))
    },
    {'longarg': 'name=',
     'default': 'simu',
     'allowedTypes': [types.StringType],
     'configName': 'Name of the simulation',
     'prompt': 'Name of the simulation (simu): ',
     'description': '''Name of the simulation, configuration and output will be saved to a directory
        with the same name''',
    },
    {'longarg': 'dryrun',
     'default': False,
     'allowedTypes': [types.IntType],
     'validate':    simuOpt.valueOneOf([True, False]),
     'description':    'Only display how simulation will perform.'
     # do not save to config, do not prompt, so this appeared to be an undocumented option.
    },
    {'arg': 'v',
     'longarg': 'verbose',
     'default': False,
     'allowedTypes': [types.NoneType, types.IntType],
     'description': 'Verbose mode.'
    },
]


def getOptions(details = __doc__):
    ''' get options from options structure,
        if this module is imported, instead of ran directly,
        user can specify parameter in some other way.
    '''
    # get all parameters, __doc__ is used for help info
    allParam = simuOpt.getParam(options, 
        '''    This program simulates the evolution of a set SNP loci, subject 
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
    if allParam[-2] != None: # saveConfig
        try:
            os.makedir(allParam[-2])
            simuOpt.saveConfig(options, '%s/%s.cfg' % (allParam[-2], allParam[-2]), allParam)
        except:
            pass
    # --verbose or -v (these is no beautifying of [floats]
    if allParam[-1]:                 # verbose
        for p in range(len(options)):
            if options[p].has_key('configName'):
                if type(allParam[p]) == types.StringType:
                    print options[p]['configName'], ':\t"'+str(allParam[p])+'"'
                else:
                    print options[p]['configName'], ':\t', str(allParam[p])
    # return the rest of the parameters
    return allParam[1:-1]


def plotAlleleFreq(pop):
    'plot the histogram of allele frequency'
    if not hasRPy:
        return True
    # 
    freq = pop.dvars().alleleFreq
    freq0 = [freq[i][0] for i in range(pop.totNumLoci())]
    r.hist(freq0, nclass=50, xlim=[0,1], xlab='frequency', ylab='hist', 
        main='Histogram of allele frequencies')


# simulate function, 
def simuHotSpot( numLoci, lociPos, initSize, finalSize, burnin, noMigrGen, mixingGen, 
        growth, numSubPop, migrModel, migrRate, mutaRate, recRate, name, dryrun):
    ''' run the simulation, parameters are:
        numLoci:        number of SNP loci on the only chromosome
        lociPos:        loci position on the chromosome. Should be in 
            increasing order.
        initSize:     initial size
        finalSize:    ending population size
        burnin, noMigrGen, mixingGen: length of three stages
        growth, mumSubPop, migrModel: migration related parameters
        migrRate, muaRate, recRate:     rates
        name:   name of the simulation, and output directory and file
    '''
    # event generations
    split    = burnin 
    mixing = split + noMigrGen
    endGen = split + noMigrGen + mixingGen    
    # demographic model
    if growth == 'linear':
        popSizeFunc = LinearExpansion(initSize, finalSize, endGen,
            burnin, split, numSubPop)
    elif growth == 'exponential':
        popSizeFunc = ExponentialExpansion(initSize, finalSize, endGen,
            burnin, split, numSubPop)
    else:
        raise exceptions.ValueError("Growth model can be one of linear and exponential.")
    # a migrator, stepping stone or island
    if numSubPop > 1 and migrModel == 'island' and migrRate > 0:
        migrOp = migrator(migrIslandRates(migrRate, numSubPop),
            mode=MigrByProbability, begin=mixing) 
    elif numSubPop > 1 and migrModel == 'stepping stone' and migrRate > 0:
        migrOp = migrator(migrSteppingStoneRates(migrRate, numSubPop, circular=True),
            mode=MigrByProbability, begin=mixing) 
    else:
        migrOp = noneOp()
    # population
    # default loci position is 1,2,3,..., with no unit
    if lociPos == []:
        lociPos = range(1, numLoci+1)
    if len(lociPos) != numLoci:
        print "If loci position is given, it should have length numLoci"
        sys.exit(1)
    pop = population(subPop=popSizeFunc(0), ploidy=2,
        loci = [numLoci], maxAllele = 1, lociPos = lociPos)
    # simulator
    simu = simulator( pop, 
        randomMating( newSubPopSizeFunc=popSizeFunc ),
        rep = 1)
    # evolve! If --dryrun is set, only show info
    simu.evolve( 
        preOps = [
            # initialize all loci with two haplotypes (111,222)
            initByValue(value=[[x]*numLoci for x in range(2)],
                proportions=[.5]*2)
            ],
        ops = [
            # k-allele model for mutation of SNP
            kamMutator(rate=mutaRate, maxAllele=1),
            # recombination rate
            recombinator(rate=recRate),
            # split population after burnin, to each sized subpopulations
            splitSubPop(0, proportions=[1./numSubPop]*numSubPop, at=[split]),
            # migration
            migrOp,
            # report statistics
            stat(popSize=True, alleleFreq=range(pop.totNumLoci()), LD=[0,1], step=10),
            # report progress
            pyEval(r'"Generation %d, population size %d, allelefre=%.3g, %.3g, LD=%.3g\n" % (gen, popSize, alleleFreq[0][1], alleleFreq[1][1], LD_prime[0][1])', step=10),
            # plot histogram
            pyOperator(func=plotAlleleFreq, step=50),
            # show elapsed time
            ticToc(at=[ split, mixing, endGen])
            ],
        end=endGen, 
        dryrun=dryrun 
    )
    if dryrun:
        print "Stop since in dryrun mode."
        sys.exit(1)
    # save population 
    SavePopulation(pop, os.path.join(name, '%s.txt' % name))


if __name__ == '__main__':
    simuHotSpot( *getOptions() )
    
