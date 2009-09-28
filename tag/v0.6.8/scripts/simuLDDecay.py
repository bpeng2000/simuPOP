#!/usr/bin/env python
#
# Demonstrate the decay of linkage disequilibrium between loci
#
# Author: Bo Peng (bpeng@rice.edu)
#
# Date:   Apr. 2005
# Last Updated: Apr. 2005
# 

# 
# OPTIONS:
#

"""
This program demonstrate the decay of linkage disequilibrium.
"""

import simuOpt, os, sys, types

options = [
  {'arg':'h', 'longarg':'help', 'default':False, 
   'description':'Print this usage message.', 'jump':-1},
  {'arg':'s:', 'longarg':'size=', 'default':1000, 
   'configName':'Population Size', 'allowedTypes':[types.IntType, types.LongType],
   'validate':simuOpt.valueGT(0),
   'prompt':'Population size (1000): ',
   'description':'Population size'},
  {'arg':'e:', 'longarg':'endGen=', 'default':50,
   'allowedTypes':[types.IntType, types.LongType],
   'configName':'Ending Generation', 'prompt':'Length of evolution (50): ',
   'description':'Length of evolution',
   'validate':simuOpt.valueGT(0)
   },
  {'arg':'r:', 'longarg':'recRate=', 'default':0.01,
   'configName':'Recombination Rate', 'allowedTypes':[types.FloatType],
   'prompt': 'Recombination rate (0.01): ', 
   'description':'Recombination rate',
   'validate':simuOpt.valueBetween(0.,1.),   
  },
  {'arg':'n:', 'longarg':'replicate=', 'default':5, 
   'configName':'Number of Replicate',
   'allowedTypes':[types.IntType, types.LongType],
   'prompt':'Number of replicates (5): ',
   'description':'Number of replicates',
   'validate':simuOpt.valueGT(0)
  },
  {'longarg':'saveConfig=', 'default':'', 'allowedTypes':[types.StringType],
   'description':'Save current paremeter set to specified file.'},
  {'arg':'v', 'longarg':'verbose', 'default':False, 
   'description':'Verbose mode.'},
  ]


from simuPOP import *
from simuUtil import *

try:
  from simuRPy import *
except:
  print "simuRPy import failed. Please check your rpy installation."
  print "LD values will not be plotted"
  useRPy = False
else:
  useRPy = True

# get all parameters
allParam = simuOpt.getParam(options, __doc__)

if len(allParam) > 0:  # successfully get the params
  (help, popSize, endGen, recRate, numRep, saveConfig, verbose) = allParam
else:
  sys.exit(0)

if saveConfig != '':
  simuOpt.saveConfig(options, saveConfig, allParam)

if help:
  print simuOpt.usage(options, __doc__)
  sys.exit(1)
  
# print out info if in verbose mode
if verbose:
  print "Pop size: ", popSize
  print "End gen: ", endGen
  print "Recombination rate: ", recRate
  print "Number of replicates: ", numRep
  
# diploid population, one chromosome with 2 loci
# random mating with sex
simu = simulator(
  population(size=popSize, ploidy=2, loci=[2]),
  randomMating(),
  rep = numRep)

if useRPy:
  plotter = varPlotter("LD[0][1]", numRep=numRep, win=endGen, 
    ylim = [0,0.25], xlab="generation", 
    ylab="D", title="Decay of Linkage Disequilibrium r=%.3f" % recRate)
else:
  plotter = noneOp()
  
# everyone will have the same genotype: 12/21
simu.evolve(
  preOps = [initByValue([1,2,2,1])],
  ops = [
    recombinator( rate = recRate),
    stat( LD=[0,1] ),
    pyEval(r"'%.4f\t' % LD[0][1]"),
    endl(rep=REP_LAST),
    plotter
    ],
  end=endGen
)

# wait till user press enter to quite and code R figure.
raw_input("Press any key to close graphics window and exit...")