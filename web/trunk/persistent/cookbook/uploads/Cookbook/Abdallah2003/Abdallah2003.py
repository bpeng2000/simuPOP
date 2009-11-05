# simulation for
# Abdallah2003
#
#

import simuOpt
simuOpt.setOptions(optimized=True)

import math
from simuPOP import *

# if validPops.bin already exists, load
# it directly. Otherwise, re-simulate
#
# population size
sz = 1000
# SNP or multiallelic marker? maxAllele=1 or 5
ma = 5

# parameter
# number of valid populations to be sampled.
samples = 2 # just to make this script runs quicker for the routine syntax checkup.

# 30 marker loci with the a QTL locus (location 0),
simu = simulator(population(size=sz, ploidy=2, 
    loci=[31], lociPos=[x/30.*3 for x in range(0,31)],
    infoFields=['fitness']),
    randomMating(ops=recombinator(rates=0.001)))

valid = 0
fixed = 0
validPops = []
while True:
    if valid >= samples:
        break

    simu.setGen(0)
    ret = simu.evolve(
        initOps = [
            # init SNP
            #initByFreq([.5,.5], atLoci=range(1,31)),
            # init MST
            initSex(),
            initByValue(value=[[0]*30,[1]*30,[2]*30,[3]*30,[4]*30],
                loci=range(1, 31), proportions=[.2]*5),
            # init QTL
            initByValue([0], loci=[0]),
        ],
        preOps = [
            # mutation
            smmMutator(rates=1e-4, loci=range(1,31), maxAllele=100),
            # LD=[[0,x] for x in [1,10,25]]),
            #varPlotter("[LD_prime[0][1],LD_prime[0][10],LD_prime[0][25]]",
            #    varDim=3, byRep=1, history=True, update=10, ylim=[0,1]),
            # introduce mutation at 100 gen to 10 individuals
            pointMutator(inds=[0], loci=[0], allele=1, at = [100]),
            # selective advantage
            mapSelector(loci=0, fitness={(0,0):1, (0,1):1.5, (1,1):2},
                begin = 100, end=110),
        ], 
        postOps = [
            # calculate LD
            stat(alleleFreq=range(0,31)),
            # check fixation
            terminateIf('alleleFreq[0][0]==1.', begin = 110),
            #pyEval('gen,alleleFreq[0][0]', begin = 100),
            #endl(rep=REP_LAST, begin = 100),
        ],
        gen=200
    )
    if ret[0] < 200:
        print "fixed at gen ", ret[0], "(count: " , fixed, ")"
        fixed += 1
    else:     # save valid population
        print "valid (count:", valid, ")"
        valid += 1
        validPops.append(simu.population(0).clone())


# now I have a list of valid population, then what?

for i in range(0,samples):
    # calculate statistics
    Stat(validPops[i], LD=[ [0,x] for x in range(1,31) ], alleleFreq=range(0,31))

# separate into groups by allelefreq
LDprime = []
R2 = []
var_LD = []
var_R2 = []
count = [0]*5
for i in range(0,5):
    LDprime.append([0]*30 )
    R2.append([0]*30 )    
    var_LD.append([0]*30 )
    var_R2.append([0]*30 )
    
# get average 
for i in range(0,samples):
    fq = 1. - validPops[i].dvars().alleleFreq[0][1]
    if fq < 0.05:
        idx = 0
    elif fq < 0.10:
        idx = 1
    elif fq < 0.15:
        idx =2
    elif fq < 0.20:
        idx = 3
    else:
        idx = 4
    count[idx] += 1
    for j in range(1,31):
        LDprime[idx][j-1] += validPops[i].dvars().LD_prime[0][j]
        R2[idx][j-1] += math.sqrt(validPops[i].dvars().R2[0][j])
        var_LD[idx][j-1] += validPops[i].dvars().LD_prime[0][j]**2
        var_R2[idx][j-1] += validPops[i].dvars().R2[0][j]
    
        
# get average and variance
for i in range(0,5):
    if count[i] > 0:
        for j in range(0,30):
            LDprime[i][j] /= count[i]
            R2[i][j] /= count[i]
            var_LD[i][j] = (var_LD[i][j] - count[i]*(LDprime[i][j]**2))/(count[i]-1)
            var_R2[i][j] = (var_R2[i][j] - count[i]*(R2[i][j]**2))/(count[i]-1)


from rpy import *
# plot average LD'
r.png()
r.par(mfrow=[2,2])
# mean LD'
r.plot(LDprime[0], type='l', ylab="mean LD'", xlab='dist', ylim=[0,1],
    lty=1, main='mean LD')
for i in range(1,5):
    r.lines(LDprime[i], type='l', lty=i+1)
r.legend(x=22, y=1, lty=range(1,6), legend=['p<0.05','0.05<p<0.10',
    '0.10<p<0.15','0.15<p<0.20','p>0.20'])
# mean R2
r.plot(R2[0], type='l', ylab="mean R", xlab='dist', ylim=[0,1],
    lty=1, main="mean R")
for i in range(1,5):
    r.lines(R2[i], type='l', lty=i+1)

# variance LD
r.plot(var_LD[0], type='l', ylab="var LD'", xlab='dist', ylim=[0,.1],
    lty=1, main="variance LD")
for i in range(1,5):
    r.lines(var_LD[i], type='l', lty=i+1)

# variance of R2
r.plot(var_R2[0], type='l', ylab="var R'", xlab='dist', ylim=[0,.02],
    lty=1, main="variance R")
for i in range(1,5):
    r.lines(var_R2[i], type='l', lty=i+1)

