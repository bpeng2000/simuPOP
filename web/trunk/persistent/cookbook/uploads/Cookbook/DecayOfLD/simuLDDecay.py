#!/usr/bin/env python
#
# Demonstrate the decay of linkage disequilibrium
#
# Author: Bo Peng (bpeng@mdanderson.org)
#

"""
This program demonstrate the decay of linkage disequilibrium due
to recombination.
"""

import simuOpt, os, sys, types, time
from simuPOP import *

try:
    from simuRPy import *
except:
    print "simuRPy import failed. Please check your rpy installation."
    print "LD values will not be plotted"
    useRPy = False
else:
    useRPy = True

options = [
    {'arg':'s:',
     'longarg':'size=',
     'default':1000,
     'label':'Population Size',
     'allowedTypes':[types.IntType, types.LongType],
     'validate':simuOpt.valueGT(0),
    },
    {'arg':'e:',
     'longarg':'gen=',
     'default':50,
     'allowedTypes':[types.IntType, types.LongType],
     'label':'Generations to evolve',
     'description':'Length of evolution',
     'validate':simuOpt.valueGT(0)
    },
    {'arg':'r:',
     'longarg':'recRate=',
     'default':0.01,
     'label':'Recombination Rate',
     'allowedTypes':[types.FloatType],
     'validate':simuOpt.valueBetween(0.,1.),
    },
    {'arg':'n:',
     'longarg':'numRep=',
     'default':5,
     'label':'Number of Replicate',
     'allowedTypes':[types.IntType, types.LongType],
     'description':'Number of replicates',
     'validate':simuOpt.valueGT(0)
    },
    {'longarg':'measure=',
     'default':'D',
     'label':'LD measure',
     'description':'Choose linkage disequilibrium measure to be outputted.',
     'chooseOneOf':['D', "D'", 'R2'],
     'validate': simuOpt.valueOneOf(['D', "D'", 'R2']),
    },
    {'longarg':'saveFigure=',
     'label':'Save figure to filename',
     'default':'',
     'allowedTypes':[types.StringType],
     'description': '''If specified, save the figures to files such as filename_10.eps.
        The format the figures is determined by file extension.
        '''
    },
    {'longarg':'save=',
     'default':'',
     'allowedTypes':[types.StringType],
     'description':'Save current paremeter set to specified file.'
    },
]


def simuLDDecay(popSize, gen, recRate, numRep, method, saveFigure, useRPy):
    '''Simulate the decay of linkage disequilibrium as a result
    of recombination.
    '''
    # diploid population, one chromosome with 2 loci
    # random mating with sex
    simu = simulator(
        population(size=popSize, ploidy=2, loci=[2]),
        randomMating(), rep = numRep)

    # get method value used to plot and evolve
    if method=="D'":
        methodplot = "LD_prime[0][1]"
        upperlim = 1
        methodeval = r"'%.4f\t' % LD_prime[0][1]"
    elif method=='R2':
        methodplot = "R2[0][1]"
        upperlim = 1
        methodeval = r"'%.4f\t' % R2[0][1]"
    else:
        methodplot = "LD[0][1]"
        upperlim = 0.25
        methodeval = r"'%.4f\t' % LD[0][1]"

    if useRPy:
        print saveFigure
        plotter = varPlotter(methodplot, 
            ylim = [0, upperlim], saveAs=saveFigure,
            update = gen - 1, ylab=method,
            main="Decay of Linkage Disequilibrium r=%f" % recRate)
    else:
        plotter = noneOp()

    simu.evolve(
        # everyone will have the same genotype: 01/10
        preOps = [
            initSex(),
            initByValue([0,1,1,0])
        ],
        ops = [
            recombinator(rates = recRate),
            stat(alleleFreq=[0], LD=[0, 1]),
            pyEval(methodeval),
            pyOutput('\n', reps=-1),
            plotter
        ],
        gen = gen
    )


if __name__ == '__main__':
    # get all parameters
    pars = simuOpt.simuParam(options, __doc__)
    # cancelled or -h, --help
    if not pars.getParam():
        sys.exit(0)

    if pars.save != '':
        pars.saveConfig(pars.save)

    simuLDDecay(pars.size, pars.gen, pars.recRate, pars.numRep,
        pars.measure, pars.saveFigure, useRPy)

    # wait five seconds before exit
    if useRPy:
        print "Figure will be closed after five seconds."
        time.sleep(5)
