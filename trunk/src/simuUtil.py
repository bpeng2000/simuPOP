#!/usr/bin/env python

############################################################################
#    Copyright (C) 2004 by Bo Peng                                         
#    bpeng@mdanderson.org
#                                                                          
#    $LastChangedDate$          
#    $Rev$                       
#                                                                          
#    This program is free software; you can redistribute it and/or modify  
#    it under the terms of the GNU General Public License as published by  
#    the Free Software Foundation; either version 2 of the License, or     
#    (at your option) any later version.                                   
#                                                                                                                                                    
#    This program is distributed in the hope that it will be useful,             
#    but WITHOUT ANY WARRANTY; without even the implied warranty of                
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.    See the                 
#    GNU General Public License for more details.                                                    
#                                                                                                                                                    
#    You should havereceived a copy of the GNU General Public License         
#    along with this program; if not, write to the                                                 
#    Free Software Foundation, Inc.,                                                                             
#    59 Temple Place - Suite 330, Boston, MA    02111-1307, USA.                         
############################################################################


"""
simuPOP utilities.

This module provides some commonly used operators
and format conversion utilities.


Function list:

- getGenotype: get genotype of specified loci, subpopulation, individual range
               etc and return as an array.
- listVars:    list a dictionary (usually pop.vars()) in a human readable format,
               use wxPython if it is available
- ConstSize
  LinearExpansion
  ExponentialExpansion
  InstantExpansion
               Sample demographic functions. Return a function that can be passed
               to newSubPopSizeFunc.
- MigrIslandRates
  MigrSteppingStoneRates
               Migration rate for two popular migration models.
- tab
  endl       
               two operators
- dataAggregator
  CollectValue
  collector
               a data collector to collect information over the generations
               Currently used by simuRPy, possibly needs an overhaul.
- trajFunc
  FreqTrajectoryMultiStochWithSubPop
               simulate trajectory in the case of subpopulation, a wrapper
               to C++ version FreqTrajectoryMultiStoch
- SaveFstat
  saveFstat (operator)
  LoadFstat
  LoadGCData
  SaveLinkage
  saveLinkage (operator)
  SaveQTDT
  SaveCSV
               Save, and sometimes load from various format. Some functions
               need more testing.
- TDT_gh
  LOD_gh
  ChiSq_test
  LOD_merlin
  VC_merlin
  Regression_merlin
               Various gene mapping routines, calling genehunter or merlin
               They work on samples saved in specified formats.
               need more testing.
- Sibpair_TDT_gh
  Sibpair_LOD_gh
  Sibpair_LOD_merlin
  CaseControl_ChiSq
  QtraitSibs_Reg_merlin
  QtraitSibs_VC_merlin
  LargePeds_Reg_merlin
  LargePeds_VC_merlin
               Various gene mapping routines, acting on a population.
               These functions need more testing.
               
"""

import exceptions, operator, types, os, sys, getopt, re, math, tempfile, shutil

from simuPOP import *

def getGenotype(pop, atLoci=[], subPop=[], indRange=[], atPloidy=[]):
    '''Obtain genotype as specified by parameters
        atLoci:     subset of loci, default to all
        subPop:     subset of subpopulations, default ao all
        indRange:   individual ranges 
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
        arr = pop.arrGenotype(True)
        for r in indRange:
            for i in range(r[0], r[1]):
                for p in ploidy:
                    for loc in loci:
                        geno.append( arr[ gs*i + p*tl + loc] )
    elif len(subPop) > 0:
        for sp in subPop:
            arr = pop.arrGenotype(sp, True)
            for i in range(pop.subPopSize(sp)):
                for p in ploidy:
                    for loc in loci:
                        geno.append(arr[ gs*i + p*tl +loc]) 
    else:
        arr = pop.arrGenotype(True)
        if len(ploidy) == 0 and len(atLoci) == 0:
            geno = pop.arrGenotype(True)
        else:
            for i in range(pop.popSize()):
                for p in ploidy:
                    for loc in loci:
                        geno.append( arr[ gs*i + p*tl +loc] )
    return geno


def _listVars(var, level=-1, name='', subPop=True, indent=0, curLevel=0):
    ''' called by listVars. Will list variables recursively'''
    if type(var) == type( dw({}) ):
        var = var.__dict__
    # all level or level < specified maximum level
    if level < 0 or (level > 0 and curLevel < level):
        # list is list or typle type
        if type(var) == types.ListType or type(var) == types.TupleType:
            index = 0
            for x in var:
                # literals
                if type(x) != types.ListType and type(x) != types.DictType:
                    # this will save a huge amount of output for sparse matrix
                    # generated by Stat(LD=[]) etc.
                    if x != None: 
                        if type(var) == types.ListType:
                            print ' '*indent, '['+str(index)+']\t', x
                        else:
                            print ' '*indent, '('+str(index)+')\t', x
                # nested stuff
                elif type(x) == types.ListType or type(x) == types.DictType:
                    if type(var) == types.ListType:
                        print ' '*indent, '['+str(index)+']\n',
                    else:
                        print ' '*indent, '('+str(index)+')\n',
                    _listVars(x, level, name, False, indent+2, curLevel + 1)
                index += 1            
        elif type(var) == types.DictType:
            # none array first
            for x in var.items():
                if not type(x[1]) in [types.ListType, types.DictType, types.TupleType]:
                    if name == '' or x[0] == name:
                        print ' '*indent, x[0], ':\t', x[1]
            # array but not subPop
            for x in var.items():
                if x[0] != 'subPop' and type(x[1]) in [types.ListType, types.DictType, types.TupleType]:
                    if name == '' or x[0] == name:
                        print ' '*indent, x[0], ':\n',
                        _listVars(x[1], level, name, False, indent+2, curLevel + 1)
            # subPop
            if subPop == True and var.has_key('subPop'):
                print ' '*indent, 'subPop\n',
                _listVars(var['subPop'], level, name, False, indent+2, curLevel + 1)
        else:
            print ' '*indent, var
    else: # out of the range of level
        if type(var) == types.ListType or type(var) == types.TupleType:
            print ' '*indent, 'list of length', len(var)
        elif type(var) == types.DictType:
            print ' '*indent, 'dict with keys [',
            for num in range(0,len(var.keys())):
                if type(var.keys()[num]) == types.StringType:
                    print "'"+ var.keys()[num] + "',",
                else:
                    print var.keys()[num], ",",
                if num != len(var.keys())-1 and num%4 == 3:
                    print '\n' + ' '*(indent+5),
            print ']'
        else:
            print ' '*indent, var


def ListVars(var, level=-1, name='', subPop=True, useWxPython=True):
    ''' 
        list a variable in tree format, either in text format or in a 
            wxPython window.
        
        var:    any variable to be viewed. Can be a dw object returned
                        by dvars() function
        level:  level of display.
        name:   only view certain variable
        subPop: whether or not display info in subPop
        useWxPython: if True, use terminal output even if wxPython is available.
    '''
    if not useWxPython:
        _listVars(var, level, name, subPop, 0, 0)
        return 

    # a wxPython version of listVars
    try:
        import wx, wx.py.filling as fill
    except:
        _listVars(var, level, name, subPop, 0, 0)
        return

    app = wx.App()
    wx.InitAllImageHandlers()
    if var==None:
        fillFrame = fill.FillingFrame()
    else:
        if type(var) == type( dw({}) ):
            fillFrame = fill.FillingFrame(rootObject=var.__dict__,
                rootLabel='var')
        else:
            fillFrame = fill.FillingFrame(rootObject=var,
                rootLabel='var')                
    fillFrame.Show(True)
    app.SetTopWindow(fillFrame)
    app.MainLoop()


#
# demographic changes
def ConstSize(size, split=0, numSubPop=1, bottleneckGen=-1, bottleneckSize=0):
    ''' The population size is constant, but will split into
        numSubPop subpopulations at generation split
    '''
    def func(gen, oldSize=[]):
        if gen == bottleneckGen:
            if gen < split:
                return [bottleneckSize]
            else:
                return [int(bottleneckSize/numSubPop)]*numSubPop
        # not bottleneck
        if gen < split:
            return [size]
        else:
            return [int(size/numSubPop)]*numSubPop
    return func

def LinearExpansion(initSize, endSize, end, burnin=0, split=0, numSubPop=1, bottleneckGen=-1, bottleneckSize=0):
    ''' Linearly expand population size from intiSize to endSize
        after burnin, split the population at generation split.
    '''
    inc = (endSize-initSize)/float(end-burnin)
    def func(gen, oldSize=[]):
        if gen == bottleneckGen:
            if gen < split:
                return [bottleneckSize]
            else:
                return [bottleneckSize/numSubPop]*numSubPop
        # not bottleneck
        if gen <= burnin:
            tot = initSize
        else:
            tot = initSize + inc*(gen-burnin)
        #
        if gen < split:
            return [int(tot)]
        elif gen > end:
            return [int(endSize/numSubPop)]*numSubPop
        else:
            return [int(tot/numSubPop)]*numSubPop
    return func


def ExponentialExpansion(initSize, endSize, end, burnin=0, split=0, numSubPop=1, bottleneckGen=-1, bottleneckSize=0):
    ''' Exponentially expand population size from intiSize to endSize
        after burnin, split the population at generation split.
    '''
    rate = (math.log(endSize)-math.log(initSize))/(end-burnin)
    def func(gen, oldSize=[]):
        if gen == bottleneckGen:
            if gen < split:
                return [bottleneckSize]
            else:
                return [bottleneckSize/numSubPop]*numSubPop
        # not bottleneck
        if gen <= burnin:
            tot = initSize
        else:
            tot = int(initSize*math.exp((gen-burnin)*rate))
        if gen < split:
            return [int(tot)]
        elif gen > end:
            return [int(endSize/numSubPop)]*numSubPop
        else:
            return [int(tot/numSubPop)]*numSubPop
    return func

def InstantExpansion(initSize, endSize, end, burnin=0, split=0, numSubPop=1, bottleneckGen=-1, bottleneckSize=0):
    '''    Instaneously expand population size from intiSize to endSize
        after burnin, split the population at generation split.
    '''
    def func(gen, oldSize=[]):
        if gen == bottleneckGen:
            if gen < split:
                return [bottleneckSize]
            else:
                return [bottleneckSize/numSubPop]*numSubPop
        # not bottleneck
        if gen <= burnin:
            tot = initSize
        else:
            tot = endSize
        if gen < split:
            return [int(tot)]
        else:
            return [int(tot/numSubPop)]*numSubPop        
    return func


# for internal use only
def testDemoFunc(end, func):
    g = range(end)
    rng = [min( [ func(x)[0] for x in g]), 
            max( [ sum(func(x)) for x in g])]
    r.plot(g, [sum(func(x)) for x in g], ylim=rng, type='l', xlab='gen', ylab='subPopSize(0)')
    r.lines(g, [func(x)[0] for x in g], type='l', xlab='gen', ylab='subPopSize(0)', lty=2)


# migration rate matrix generators
def MigrIslandRates(r, n):
    '''
     migration rate matrix

     x m/(n-1) m/(n-1) ....
     m/(n-1) x ............
     .....
     .... m/(n-1) m/(n-1) x
     
    where x = 1-m
    '''
    # n==1?
    if n == 1:
        return [[1]]
    #
    m = []
    for i in range(0,n):
        m.append( [r/(n-1.)]*n)
        m[-1][i] = 1-r
    return m                         
    

def MigrSteppingStoneRates(r, n, circular=False):
    '''
     migration rate matrix, circular step stone model (X=1-m)
  
   X   m/2               m/2
   m/2 X   m/2           0
   0   m/2 x   m/2 ......0
   ...
   m/2 0 ....       m/2  X

   or non-circular
  
   X   m/2               m/2
   m/2 X   m/2           0
   0   m/2 X   m/2 ......0
   ...
   ...              m   X
    ''' 
    if n < 2: 
        raise exceptions.ValueError("Can not define step stone model for n < 2")
    elif n == 2:
        return [[1-r,r],[r,1-r]]
    # the normal case (n>2)
    m = []
    for i in range(0, n):
        m.append([0]*n)
        m[i][i] = 1-r
        m[i][(i+1)%n] = r/2.
        m[i][(i+n-1)%n] = r/2.
    if not circular:
        m[0][1] = r
        m[0][-1] = 0
        m[n-1][0] = 0
        m[n-1][n-2] = r
    return m

 
# 
# operator tab (I can use operator output
# but the name conflicts with parameter name
# and I would not want to go through the trouble
# of a walkaround (like aliasing output)
def tab(output=">", outputExpr="", **kwargs):
    parm = ''    
    for (k,v) in kwargs.items():
        parm += ' , ' + str(k) + '=' + str(v)
    cmd = r'''pyEval( r'"\t"' ''' + ', output="""' + output + \
        '""", outputExpr="""' + outputExpr + '"""' + parm + ')'
    # print cmd
    return eval(cmd)


def endl(output=">", outputExpr="", **kwargs):
    parm = ''    
    for (k,v) in kwargs.items():
        parm += ' , ' + str(k) + '=' + str(v)
    cmd = r'''pyEval( r'"\n"' ''' + ', output="""' + output + \
        '""", outputExpr="""' + outputExpr + '"""' + parm + ')'
    # print cmd
    return eval(cmd)


# aggregator
# used by varPlotters
class dataAggregator:
    """
    collect variables so that plotters can plot them all at once

    You can of course put it in other uses

    Usage:
        a = dataAggregator( maxRecord=0, recordSize=0)
            maxRecord:    if more data is pushed, the old ones are discarded
            recordSize: size of record
        a.push(gen, data, idx=-1)
            gen:    generation number
            data:   one record (will set recordSize if the first time), or
            idx:    if idx!=-1, set data at idx.
        a.clear()
        a.range()    # return min, max of all data
        a.data[i]    # column i of the data
        a.gen        #
        a.ready()    # if all column has the same length, so data is ready
        
    Internal data storage:
        self.gen    [ .... ]
        self.data   column1 [ ...... ]
                    column2 [ ...... ]
                                .......
    each record is pushed at the end of 
    """ 
    def __init__(self, maxRecord=0, recordSize=0):
        """
        maxRecord: maxRecorddow size. I.e., maximum generations of data to keep
        """
        self.gen = []
        self.data = []
        self.maxRecord = maxRecord
        self.recordSize = recordSize
    
    def __repr__(self):
        s = str(self.gen) + "\n"
        for i in range(0, len(self.data)):
            s += str(self.data[i]) + "\n"
        return s

    def clear(self):
        self.gen = []
        self.data = []
     
    def ready(self):
        return self.recordSize>0 and len(gen)>0 and len( data[0] ) == len( data[-1] )
        
    def flatData(self):
        res = []
        for d in self.data:
            res.extend( d )
        return res

    def dataRange(self):
        if len(self.gen) == 0:
            return [0,0]

        y0 = min( [ min(x) for x in self.data] )
        y1 = max( [ max(x) for x in self.data] )
        return [y0,y1]
        
    def push(self, _gen, _data, _idx=-1 ):
        # first add data to allData
        if len(self.gen) == 0:     # the first time
            self.gen = [ _gen ]
            if _idx == -1:        # given a full array of data
                if self.recordSize == 0:    
                    self.recordSize = len(_data)
                elif self.recordSize != len(_data):
                    raise exceptions.ValueError("Data length does not equal specfied record size")
                for i in range(self.recordSize):
                    self.data.append( [_data[i]] )
                return
            elif _idx == 0:     # the only allowed case
                if type(_data) in [type(()), type([])]:
                    raise exceptions.ValueError("If idx is specified, _data should not be a list.")
                self.data = [ [_data] ]
                return
            else:                                                # data out of range
                raise exceptions.ValueError("Appending data with wrong idx")
        elif len(self.gen) == 1:             # still the first generation
            if self.gen[-1] == _gen:        # still working on this generation
                if _idx == -1:    # give a full array?
                    raise exceptions.ValueError("Can not reassign data from this generation")
                elif self.recordSize != 0 and    _idx >= self.recordSize:
                    raise exceptions.ValueError("Data exceeding specified record size")
                elif _idx == len(self.data):    # append
                    if type(_data) in [type(()), type([])]:
                        raise exceptions.ValueError("If idx is specified, _data should not be a list.")
                    self.data.append( [_data] )
                elif _idx < len(self.data):    # change exsiting one?
                    raise exceptions.ValueError("You can not change exisiting data")
                else:                                                # data out of range
                    raise exceptions.ValueError("Appending data with wrong idx")
            else:                                                    # go to the next one!
                if self.recordSize == 0:         # not specified
                    self.recordSize = len(self.data)
                elif self.recordSize != len(self.data):
                    raise exceptions.ValueError("The first row is imcomplete")
                self.gen.append( _gen )
                if _idx == -1:        # given a full array of data
                    if self.recordSize != len(_data):
                        raise exceptions.ValueError("Data length does not equal specfied record size")
                    for i in range(self.recordSize):
                        self.data[i].append( _data[i] )
                    return
                elif _idx == 0:     # the only allowed case
                    if type(_data) in [type(()), type([])]:
                        raise exceptions.ValueError("If idx is specified, _data should not be a list.")
                    self.data[0].append(_data)
                    return
                else:                                                # data out of range
                    raise exceptions.ValueError("Appending data with wrong idx")
        else:     # already more than one record
            # trim data if necessary
            if self.maxRecord > 0 :
                if _gen - self.gen[0] >= self.maxRecord:
                    self.gen = self.gen[1:]
                    for i in range(0, self.recordSize):
                        self.data[i] = self.data[i][1:]
            if self.gen[-1] == _gen:     # still this generation
                if _idx == -1:    # give a full array?
                    raise exceptions.ValueError("Can not reassign data from this generation")
                elif _idx >= self.recordSize:
                    raise exceptions.ValueError("Data exceeding specified record size")
                elif _idx < len(self.data):    # change exsiting one?
                    if type(_data) in [type(()), type([])]:
                        raise exceptions.ValueError("If idx is specified, _data should not be a list.")
                    self.data[_idx].append( _data )
                else:                                                # data out of range
                    raise exceptions.ValueError("Appending data with wrong idx")
            else:                                                    # go to the next one!
                self.gen.append( _gen )
                if _idx == -1:        # given a full array of data
                    if self.recordSize != len(_data):
                        raise exceptions.ValueError("Data length does not equal specfied record size")
                    for i in range(self.recordSize):
                        self.data[i].append( _data[i] )
                    return
                elif _idx == 0:     # the only allowed case
                    if type(_data) in [type(()), type([])]:
                        raise exceptions.ValueError("If idx is specified, _data should not be a list.")
                    self.data[0].append(_data)
                    return
                else:                                                # data out of range
                    raise exceptions.ValueError("Appending data with wrong idx")


# data collector
#
def CollectValue(pop, gen, expr, name):
    value = eval(expr, globals(), pop.vars())
    d = pop.vars()
    if not d.has_key(name):
        d[name] = {}
    d[name][gen] = value


# wrapper
def collector(name, expr, **kwargs):
    # deal with additional arguments
    parm = ''
    for (k,v) in kwargs.items():
        parm += str(k) + '=' + str(v) + ', '
    # pyEval( exposePop=1, param?, stmts="""
    # Collect(pop, expr, name)
    # """)
    opt = '''pyExec(exposePop=1, %s
        stmts=r\'\'\'CollectValue(pop, gen,
            expr="""%s""", name="""%s""")\'\'\')''' \
        % ( parm, expr, name) 
    #print opt
    return eval(opt)


def trajFunc(endingGen, traj):
    ''' return freq at each generation from a 
        simulated trajctories. '''
    def func(gen):
        freq = []
        for tr in traj:
            if gen < endingGen - len(tr) + 1:
                freq.append( 0 )
            else:
                freq.append( tr[ gen - (endingGen - len(tr) + 1) ] )
        return freq
    return func


def FreqTrajectoryMultiStochWithSubPop(
        curGen, 
        numLoci,
        freq, 
        NtFunc, 
        minMutAge, 
        maxMutAge,
        fitness=[], 
        mode = 'uneven',
        ploidy=2,
        restartIfFail=True,
        fitnessFunc=None):
    ''' Simulate frequency trajectory with subpopulation structure,
        migration is currently ignored. The essential part of this 
        script is to simulate the trajectory of each subpopulation 
        independently by calling FreqTrajectoryMultiStoch with properly
        wrapped NtFunc function. 

        If mode = 'even' (default) When freq is the same length 
            of the number of loci. The allele frequency at the last 
            generation will be multi-nomially distributed. If freq
            for each subpop is specified in the order of loc1-sp1, loc1-sp2, ..
                loc2-sp1, .... This freq will be used directly.
        If mode = 'uneven'. The number of disease alleles
            will be proportional to the interval lengths of 0 x x x 1 while x are 
            uniform [0,1]. The distribution of interval lengths, are roughly 
            exponential (conditional on overall length 1). '
        If mode = 'none', subpop will be ignored.
        
        This script assume a single-split model of NtFunc
    '''
    numSP = len(NtFunc(curGen))
    if maxMutAge == 0: 
        maxMutAge = endGen
    TurnOnDebug(DBG_GENERAL)
    if numSP == 1 or mode == 'none':
        # given in the form of [[.1,.2]]
        if type(freq[0]) in [type((0,)), type([])]:
            freq = freq[0]
        traj = FreqTrajectoryMultiStoch(
                curGen=curGen,
                freq=freq, 
                NtFunc=NtFunc, 
                fitness=fitness, 
                fitnessFunc=fitnessFunc,
                minMutAge=minMutAge, 
                maxMutAge=maxMutAge, 
                ploidy=ploidy,
                restartIfFail=True)
        #print traj
        if True in [len(t) < max(2, minMutAge) for t in traj]:
            print "Failed to generate trajectory. You may need to set a different set of parameters."
            print "len: ", [len(t) for t in traj]
            print 'curGen: ', curGen
            print 'freq: ', freq
            print 'begin size: ', NtFunc(0)
            print 'ending size: ', NtFunc(curGen)
            print 'fitness: ', fitness
            print 'minMutAge: ', minMutAge
            print 'maxMutAge: ', maxMutAge
            print 'ploidy: ', ploidy
            sys.exit(1)
        return (traj, [curGen-len(x)+1 for x in traj], trajFunc(curGen, traj))
    # other wise, do it in two stages
    # get the split generation.
    split = curGen;
    while(True):
        if len(NtFunc(split)) == 1:
            break
        split -= 1
    split += 1
    # set default for min/max mutage
    if minMutAge < curGen - split:
        minMutAge = split
    if minMutAge > maxMutAge:
        print "Minimal mutant age %d is larger then maximum age %d" % (minMutAge, maxMutAge)
        sys.exit(1)
    # now, NtFunc(split) has subpopulations
    # 
    # for each subpopulation
    # layout for freqALL 
    #     [  loc 0   ][loc 1 ][loc 2  ]
    # for each locus
    #     [ loc  0 ] = [at subpop 0, subpop 1, subpop 2...]
    #
    # That is to say, index is for locus i in subpop sp
    #   freqAll[sp+i*numSP],
    if type(freq[0]) in [type((0,)), type([])]:
        # freq is given as [subpop 0][subpop 1] [subpop 2]
        freqAll = [0]*(numLoci*numSP)
        for (sp, f) in enumerate(freq):
            for (loc, s) in enumerate(f):
                freqAll[sp+loc*numSP] = s
    else:
        if len(freq) == numSP*numLoci:
            freqAll = freq
        elif len(freq) == numLoci:
            freqAll = [0]*(numLoci*numSP)
            if mode == 'even':
                for i in range(numLoci):
                    wt = NtFunc(curGen)
                    ps = sum(wt)
                    # total allele number
                    totNum = int(freq[i]*ps)
                    # in subpopulations, according to population size
                    num = rng().randMultinomialVal(totNum, [x/float(ps) for x in wt])
                    for sp in range(numSP):
                        freqAll[sp+i*numSP] = num[sp]/float(wt[sp])
            elif mode == 'uneven':
                for i in range(numLoci):
                    wt = NtFunc(curGen)
                    # total allele number
                    totNum = int(freq[i]*sum(wt))
                    while(True):
                        # get [ x x x x x ] while x is uniform [0,1]
                        num = [0,1]+[rng().randUniform01() for x in range(numSP-1)]
                        num.sort()
                        for sp in range(numSP):
                            freqAll[sp+i*numSP] = (num[sp+1]-num[sp])*totNum/wt[sp]
                        if max(freqAll) < 1:
                            break;
            else:
                print "Wrong mode parameter is used: ", mode
            print "Using ", mode, "distribution of alleles at the last generation"
            print "Frequencies at the last generation: sp0-loc0, loc1, ..., sp1-loc0,..."
            for sp in range(numSP):
                print "SP ", sp, ': ',
                for i in range(numLoci):
                    print "%.3f " % freqAll[sp+i*numSP],
                print
        else:
            raise exceptions.ValueError("Wrong freq length")
    spTraj = [0]*numSP*numLoci
    for sp in range(numSP):
        print "Generting trajectory for subpopulation %d (generation %d - %d), freq=%s" % (sp, split, curGen, [freqAll[sp+x*numSP] for x in range(numLoci)])
        # FreqTraj... will probe Nt for the next geneartion.
        def spPopSize(gen):
            if gen < split:
                return [NtFunc(split-1)[0]]
            else:
                return [NtFunc(gen)[sp]]
        while True:
            t = FreqTrajectoryMultiStoch(
                curGen=curGen,
                freq=[freqAll[sp+x*numSP] for x in range(numLoci)], 
                NtFunc=spPopSize, 
                fitness=fitness,
                fitnessFunc=fitnessFunc,
                minMutAge=curGen-split, 
                maxMutAge=curGen-split, 
                ploidy=ploidy,
                restartIfFail=False) 
                # failed to generate one of the trajectory
            if 0 in [len(x) for x in t]:
                print "Failed to generate trajectory. You may need to set a different set of parameters."
                sys.exit(1)
            if 0 in [x[0] for x in t]:
                print "Subpop return 0 index. restart "
            else:
                break;
        # now spTraj has SP0: loc0,1,2..., SP1 loc 0,1,2,..., ...
        for i in range(numLoci):
            spTraj[sp+i*numSP] = t[i]
    # add all trajectories
    traj = []
    for i in range(numLoci):
        traj.append([])
        for g in range(split, curGen+1):
            totAllele = sum( [
                spTraj[sp+i*numSP][g-split] * NtFunc(g)[sp] for sp in range(numSP) ])
            traj[i].append( totAllele / sum(NtFunc(g)) )
    # 
    print "Starting allele frequency (at split) ", [traj[i][0] for i in range(numLoci)]
    print "Generating combined trajsctory with range: ", minMutAge, " - ", maxMutAge
    trajBeforeSplit = FreqTrajectoryMultiStoch(
        curGen=split,
        freq=[traj[i][0] for i in range(numLoci)], 
        NtFunc=NtFunc, 
        fitness=fitness,
        fitnessFunc=fitnessFunc,
        minMutAge=minMutAge-len(traj[0])+1, 
        maxMutAge=maxMutAge-len(traj[0])+1, 
        ploidy=ploidy,
        restartIfFail=True) 
    if 1 in [len(x) for x in trajBeforeSplit]:
        print "Failed to generated trajectory. (Tried more than 1000 times)"
        sys.exit(0)
    def trajFuncWithSubPop(gen):
        if gen >= split:
            return [spTraj[x][gen-split] for x in range(numLoci*numSP)]
        else:
            freq = []
            for tr in trajBeforeSplit:
                if gen < split - len(tr) + 1:
                    freq.append( 0 )
                else:
                    freq.append( tr[ gen - (split - len(tr) + 1) ] )
        return freq
    trajAll = []
    for i in range(numLoci):
        trajAll.append( [] )
        trajAll[i].extend(trajBeforeSplit[i])
        trajAll[i].extend(traj[i][1:])    
    # how exactly should I return a trajectory?
    return (trajAll, [curGen-len(x)+1 for x in trajAll ], trajFuncWithSubPop)



#########################################################################
###
### The following are file import / export (mostly) functions
###
### These functions will observe the same interface for convenience
### some options are not needed, but should be provided (and safely
### ignored.)
###
### 1. pop: population to save, can be a string, in which case
###    the population will be loaded from a file.
### 2. output and outputExpr: output filename or pattern.
### 3. loci: loci to save, default to all loci
###    If you want to save all loci on a chromosome, use
###       loci = range(pop.chromBegin(ch), pop.chromEnd(ch))
### 4. shift: value add to allele number
### 5. combine: if combine alleles, function to use
### 6. fields: information fields to save
###
### X. additional parameters for each file format
###
###
#########################################################################

# save file in FSTAT format     
def SaveFstat(pop, output='', outputExpr='', maxAllele=0, loci=[], shift=1,
    combine=None):
    if output != '':
        file = output
    elif outputExpr != '':
        file = eval(outputExpr, globals(), pop.vars() )
    else:
        raise exceptions.ValueError, "Please specify output or outputExpr"
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
        loci = range(pop.totalNumLoci())
    nl = len(loci)
    if nl > 100:
        print "Warning: Current version (2.93) of FSTAT can not handle more than 100 loci"
    if maxAllele != 0:
        nu = maxAllele
    else:
        nu = pop.maxAllele()
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
        f.write( pop.locusName(loc) +"\n");
    for sp in range(0, pop.numSubPop()):
        # genotype of subpopulation sp, individuals are
        # rearranged in perfect order
        gt = pop.arrGenotype(sp, True)
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


# operator version of the function SaveFstat
def saveFstat(output='', outputExpr='', **kwargs):
    # deal with additional arguments
    parm = ''
    for (k,v) in kwargs.items():
        parm += str(k) + '=' + str(v) + ', '
    # pyEval( exposePop=1, param?, stmts="""
    # saveInFSTATFormat( pop, rep=rep?, output=output?, outputExpr=outputExpr?)
    # """)
    opt = '''pyEval(exposePop=1, %s
        stmts=r\'\'\'SaveFstat(pop, rep=rep, output=r"""%s""", 
        outputExpr=r"""%s""" )\'\'\')''' % ( parm, output, outputExpr) 
    # print opt
    return eval(opt)

# used to parse name
import re


# load population from fstat file 'file'
# since fstat does not have chromosome structure
# an additional parameter can be given
def LoadFstat(file, loci=[]):
    # open file
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
        if nl != reduce(operator.add, loci):
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
        if reduce(operator.add, numLoci, 0) != nl:
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
    if reduce(operator.add, subPopSize) != len(gt):
        raise exceptions.ValueError("Population size does not match")
    # we have all the information, create a population
    pop = population( subPop=subPopSize, loci = numLoci, ploidy=2,
        lociNames=lociNames)
    # 
    gs = pop.totNumLoci()
    popGT = pop.arrGenotype(True)
    for ind in range(0, len(gt)):
        p1 = 2*gs*ind                # begining of first hemo copy
        p2 = 2*gs*ind + gs     # second
        for al in range(0, gs): # allele
            ale = int(gt[ind][al+1])
            popGT[2*gs*ind + al] = ale/(10**nd)
            popGT[2*gs*ind + gs + al] = ale%(10*nd)
            if popGT[2*gs*ind + al] > maxAllele:
                maxAllele = popGT[2*gs*ind + al]
            if popGT[2*gs*ind + gs + al] > maxAllele:
                maxAllele = popGT[2*gs*ind + gs + al]
    pop.setMaxAllele(maxAllele)
    return pop


# read GC data file in http://wpicr.wpic.pitt.edu/WPICCompGen/genomic_control/genomic_control.htm
def LoadGCData(file, loci=[]):
    # open file
    try:
        f = open(file, "r")
    except exceptions.IOError:
        raise exceptions.IOError("Can not open file " + file + " to read.")
    gt = []
    for line in f.readlines():
        gt.append( line.split() )
    f.close()
    # now we have a 2-d matrix of strings
    # population size?
    popSize = len(gt)
    # number of alleles
    numAllele = (len(gt[0]))/2-1
    #
    # loci number
    if reduce(operator.add, loci,0.) == numAllele:
        lociNum = loci
    else:
        lociNum = [numAllele]
    # create population
    pop = population(size=popSize, ploidy=2, loci=lociNum, maxAllele=2)
    # 
    gs = pop.totNumLoci()
    popGT = pop.arrGenotype(True)
    for ind in range(0, len(gt)):
        pop.individual(ind).setAffected( int(gt[ind][1]))
        p1 = 2*gs*ind                # begining of first hemo copy
        p2 = 2*gs*ind + gs     # second
        for al in range(0, gs): # allele
            popGT[2*gs*ind + al] = int(gt[ind][al*2+2])
            popGT[2*gs*ind + gs + al] = int(gt[ind][al*2+3])
    return pop

#        
def SaveLinkage(pop, output='', outputExpr='', loci=[], shift=1, combine=None,
        fields = [], recombination=0.00001, penetrance=[0,0.25,0.5], 
        pre=True, daf=0.001):
    """ save population in Linkage format. Currently only
        support affected sibpairs sampled with affectedSibpairSample
        operator.
         
        pop: population to be saved. Must have ancestralDepth 1.
            paired individuals are sibs. Parental population are corresponding
            parents. If pop is a filename, it will be loaded.

       output: output.dat and output.ped will be the data and pedigree file.
            You may need to rename them to be analyzed by LINKAGE. This allows
            saving multiple files.
            
        outputExpr: expression version of output.

        pre: True. pedigree format to be fed to makeped. Non-pre format it is likely to 
            be wrong now for non-sibpair families.
        
        Note:
            the first child is always the proband.
    """
    if type(pop) == type(''):
        pop = LoadPopulation(pop)
    if output != '':
        file = output
    elif outputExpr != '':
        file = eval(outputExpr, globals(), pop.vars() )
    else:
        raise exceptions.ValueError, "Please specify output or outputExpr"
    # open data file and pedigree file to write.
    try:
        datOut = open(file + ".dat", "w")
        if pre:
            pedOut = open(file + ".pre", "w")
        else:
            pedOut = open(file + ".ped", "w")
    except exceptions.IOError:
        raise exceptions.IOError, "Can not open file " + file + ".dat/.ped to write."
    #
    if loci == []:
        loci = range(pop.totalNumLoci())
    #    
    # file is opened.
    # write data file
    # nlocus
    # another one is affection status 
    # risklocus (not sure. risk is not to be calculated)
    # sexlink autosomal: 0
    # nprogram whatever
    # mutsys: all loci are mutational? 0 right now
    # mutmale
    # mutfemale
    # disequil: assume in LD? Yes.
    datOut.write( '''%d 0 0 5 << nlocus, risklocus, sexlink, nprogram
0 0 0 0 << mutsys, mutmale, mutfemale, disequil
'''    % (len(loci)+1) )
    # order of loci, allegro does not welcome comments after this line.
    # we need one more than the number of loci (including disease marker)
    datOut.write( ' '.join( [str(m+1) for m in range(len(loci) + 1)]) + "\n")
    # describe affected status
    datOut.write( "1 2 << affection status code, number of alleles\n")
    datOut.write( "%f %f << gene frequency\n" % ( 1-daf, daf) )
    datOut.write( "1 << number of factors\n")
    datOut.write( "%f %f %f << penetrance\n" % tuple(penetrance) )
    # describe each locus
    Stat(pop, alleleFreq=loci)
    af = pop.dvars().alleleFreq
    for marker in loci:
        # now, 3 for numbered alleles
        numAllele = len(af[marker])
        print >> datOut, '3 %d << %s' % (numAllele, pop.locusName(marker))
        datOut.write( ''.join(['%.6f ' % af[marker][ale] for ale in range(numAllele)]) + ' << gene frequencies\n' )
    # sex-difference
    # interference
    datOut.write('0 0 << sex difference, interference\n')
    # recombination
    datOut.write( ''.join(['%f '%recombination]*len(loci)) + ' << recombination rates \n ')
    # I do not know what they are
    datOut.write( "1 0.1 0.1\n")
    # done!
    datOut.close()
    # write pedigree file (affected sibpairs)
    # sex: in linkage, male is 1, female is 2
    def sexCode(ind):
        if ind.sex() == Male:
            return 1
        else:
            return 2
    # disease status: in linkage affected is 2, unaffected is 1
    def affectedCode(ind):
        if ind.affected():
            return 2
        else:
            return 1
    # alleles string, since simuPOP allele starts from 0, add 1 to avoid
    # being treated as missing data.
    pldy = pop.ploidy()
    def writeInd(ind, famID, id, fa, mo):
        if pre:
            print >> pedOut, '%d %d %d %d %s %s' % (famID, id, fa, mo, sexCode(ind), affectedCode(ind)),
        else:
            if fa == 0:
                print >> pedOut, '%d %d %d 3 0 0 %d %s 0 %s' % (famID, id, fa, mo, sexCode(ind), affectedCode(ind)),
            else:
                print >> pedOut, '%d %d %d 0 4 4 %d %s 1 %s' % (famID, id, fa, mo, sexCode(ind), affectedCode(ind)),
        for marker in loci:
            if combine is None:
                for p in range(pldy):
                    print >> pedOut, " %d" % (ind.allele(marker, p) + shift), 
            else:
                print >> pedOut, " %d" % combine([ind.allele(marker, p) for p in range(pldy)]), 
        print >> pedOut
    #
    # get unique pedgree id numbers
    from sets import Set
    peds = Set(pop.indInfo('pedindex', False))
    # do not count peds
    peds.discard(-1)
    #
    newPedIdx = 1
    for ped in peds:
        id = 1
        pastmap = {-1:0}
        # go from generation 2, 1, 0 (for example)
        for anc in range(pop.ancestralDepth(), -1, -1):
            newmap = {-1:0}
            pop.useAncestralPop(anc)
            # find all individual in this pedigree
            for i in range(pop.popSize()):
                ind = pop.individual(i)
                if ind.info('pedindex') == ped:
                    dad = int(ind.info('father_idx'))
                    mom = int(ind.info('mother_idx'))
                    if dad == mom and dad != -1:
                        print "Something wrong with pedigree %d, father and mother idx are the same: %s" % \
                            (ped, dad)
                    writeInd(ind, newPedIdx, id, pastmap.setdefault(dad, 0), pastmap.setdefault(mom, 0))
                    newmap[i] = id
                    id += 1
            pastmap = newmap
        newPedIdx += 1
    pedOut.close()    


# operator version of saveLinkage
def saveLinkage(output='', outputExpr='', **kwargs):
    "An operator to save population in linkage format"
    # deal with additional arguments
    parm = ''
    for (k,v) in kwargs.items():
        parm += str(k) + '=' + str(v) + ', '
    # pyEval( exposePop=1, param?, stmts="""
    # saveInFSTATFormat( pop, rep=rep?, output=output?, outputExpr=outputExpr?)
    # """)
    opt = '''pyEval(exposePop=1, %s
        stmts=r\'\'\'SaveLinkage(pop, rep=rep, output=r"""%s""", 
        outputExpr=r"""%s""" )\'\'\')''' % ( parm, output, outputExpr) 
    # print opt
    return eval(opt)


# save in merlin qtdt format
def SaveQTDT(pop, output='', outputExpr='', loci=[], affectionCode=['U', 'A'], 
        fields=[], combine=None, shift=1, **kwargs):
    """ save population in Merlin/QTDT format. The population must have
        pedindex, father_idx and mother_idx information fields.
         
        pop: population to be saved. If pop is a filename, it will be loaded.

        output: base filename. 
        outputExpr: expression for base filename, will be evaluated in pop's
            local namespace.

        affectionCode: code for unaffected and affected. '1', '2' are default,
            but 'U', and 'A' or others can be specified.

        loci: loci to output

        fields: information fields to output

        combine: an optional function to combine two alleles of a diploid 
            individual.

        shift: if combine is not given, output two alleles directly, adding
            this value (default to 1).
    """
    if type(pop) == type(''):
        pop = LoadPopulation(pop)
    if output != '':
        file = output
    elif outputExpr != '':
        file = eval(outputExpr, globals(), pop.vars())
    else:
        raise exceptions.ValueError, "Please specify output or outputExpr"
    # open data file and pedigree file to write.
    try:
        datOut = open(file + ".dat", "w")
        mapOut = open(file + ".map", "w")
        pedOut = open(file + ".ped", "w")
    except exceptions.IOError:
        raise exceptions.IOError, "Can not open file " + file + " to write."
    if loci == []:
        loci = range(0, pop.totNumLoci())
    #    
    # write dat file
    # 
    if 'affection' in fields:
        outputAffectation = True
        fields.remove('affection')
        print >> datOut, 'A\taffection'
    else:
        outputAffectation = False
    for f in fields:
        print >> datOut, 'T\t%s' % f
    for marker in loci:
        print >> datOut, 'M\t%s' % pop.locusName(marker)
    datOut.close()
    #
    # write map file
    print >> mapOut, 'CHROMOSOME MARKER POSITION'
    for marker in loci:
        print >> mapOut, '%d\t%s\t%f' % (pop.chromLocusPair(marker)[0] + 1, 
            pop.locusName(marker), pop.locusPos(marker))
    mapOut.close()
    #
    # write ped file
    def sexCode(ind):
        if ind.sex() == Male:
            return 1
        else:
            return 2
    # disease status: in linkage affected is 2, unaffected is 1
    def affectedCode(ind):
        if ind.affected():
            return affectionCode[1]
        else:
            return affectionCode[0]
    #
    pldy = pop.ploidy()
    def writeInd(ind, famID, id, fa, mo):
        print >> pedOut, '%d %d %d %d %d' % (famID, id, fa, mo, sexCode(ind)),
        if outputAffectation:
            print >> pedOut, affectedCode(ind),
        for f in fields:
            print >> pedOut, '%.3f' % ind.info(f),
        for marker in loci:
            for p in range(pldy):
                print >> pedOut, "%d" % (ind.allele(marker, p) + shift), 
        print >> pedOut
    #
    # number of pedigrees
    # get unique pedgree id numbers
    from sets import Set
    if pop.hasInfoField('pedindex') and pop.ancestralDepth() >= 1:
        peds = Set(pop.indInfo('pedindex', False))
        # do not count peds
        peds.discard(-1)
        #
        newPedIdx = 1
        #
        for ped in peds:
            id = 1
            # -1 means no parents
            pastmap = {-1:0}
            # go from generation 2, 1, 0 (for example)
            for anc in range(pop.ancestralDepth(), -1, -1):
                newmap = {-1:0}
                pop.useAncestralPop(anc)
                # find all individual in this pedigree
                for i in range(pop.popSize()):
                    ind = pop.individual(i)
                    if ind.info('pedindex') == ped:
                        dad = int(ind.info('father_idx'))
                        mom = int(ind.info('mother_idx'))
                        if dad == mom and dad != -1:
                            print "Something wrong with pedigree %d, father and mother idx are the same: %s" % \
                                (ped, dad)
                        writeInd(ind, newPedIdx, id, pastmap.setdefault(dad, 0), pastmap.setdefault(mom, 0))
                        newmap[i] = id
                        id += 1
                pastmap = newmap
            newPedIdx += 1
    else:
        # rare case: no pedigree structure, only output the last generation without parents
        for idx, ind in enumerate(pop.individuals()):
            writeInd(ind, idx, 1, 0, 0)
    pedOut.close()



def SaveCSV(pop, output='', outputExpr='', fields=['sex', 'affection'], 
        loci=[], combine=None, shift=1, **kwargs):
    """ save file in CSV format 
    fileds: information fields, 'sex' and 'affection' are special fields that 
        is treated differently.
    genotype: list of loci to output, default to all.   
    combine: how to combine the markers. Default to None.
       A function can be specified, that takes the form 
         def func(markers):
             return markers[0]+markers[1]
    shift: since alleles in simuPOP is 0-based, shift=1 is usually needed to 
        output alleles starting from allele 1. This parameter is ignored if 
        combine is used.
    """
    if output != '':
        file = output
    elif outputExpr != '':
        file = eval(outputExpr, globals(), pop.vars() )
    else:
        raise exceptions.ValueError, "Please specify output or outputExpr"
    if loci == []:
        loci = range(0, pop.totNumLoci())
    try:
        out = open( file, "w")
    except exceptions.IOError:
        raise exceptions.IOError, "Can not open file " + file +" to write."
    # keep the content of pieces in strings first
    content = [''] * pop.numChrom()
    # for each family
    def sexCode(ind):
        if ind.sex() == Male:
            return 1
        else:
            return 2
    # disease status: in linkage affected is 2, unaffected is 1
    def affectedCode(ind):
        if ind.affected():
            return 1
        else:
            return 2
    # write out header
    print >> out, 'id, ', ', '.join(fields), ', ',
    if combine is None:
        print >> out, ', '.join(['marker%s_1, marker%s_2' % (marker, marker) for marker in loci])
    else:
        print >> out, ', '.join(['marker%s' % marker for marker in loci])
    # write out
    id = 1
    pldy = pop.ploidy()
    for ind in pop.individuals():
        print >> out, id,
        for f in fields:
            if f == 'sex':
                print >> out, ', ', sexCode(ind),
            elif f == 'affection':
                print >> out, ', ', affectedCode(ind),
            else:
                print >> out, ', ', ind.info(f),
        for marker in loci:
            if combine is None:
                for p in range(pldy):
                    print >> out, ", %d" % (ind.allele(marker, p) + shift), 
            else:
                print >> out, ", %d" % combine([ind.allele(marker, p) for p in range(pldy)]), 
        print >> out
        id += 1
    out.close() 



def TDT_gh(file, gh='gh'):
    ''' 
    Analyze data using genehunter/TDT. Note that this function may not work under 
    platforms other than linux, and may not work with your version of genehunter.
    As a matter of fact, it is almost unrelated to simuPOP and is provided only
    as an example how to use python to analyze data.
    
    Parameters:
        file: file to analyze. This function will look for file.dat and file.pre 
            in linkage format.
        loci: a list of loci at which p-value will be returned. If the list is empty,
            all p-values are returned.
        gh: name (or full path) of genehunter executable. Default to 'gh'

    Return value:
        A list (for each chromosome) of list (for each locus) of p-values.
    '''
    if not os.path.isfile(file + '.dat') or not os.path.isfile(file + '.pre'):
        print 'Data (%s.dat) or pedigree (%s.pre) file does not exist' % (file, file)
        sys.exit(2)
    # open the pipe for gh
    fin, fout = os.popen2(gh)
    cmds = '''load markers %s.dat
tdt %s.pre
q
''' % (file, file)
    print "Running GENEHUNTER with commands:"
    print cmds
    # write to fin
    print >> fin, cmds
    fin.close()
    # read output 
    # get only loc number and p-value
    scan = re.compile('loc(\d+)\s+- Allele \d+\s+\d+\s+\d+\s+[\d.]+\s+([\d.]+|nan)\s*.*')
    head = re.compile('Marker loc(\d+).*')
    minPvalue = {}
    maxLoc = 0
    for l in fout.readlines():
        try:
            (loc,) = head.match(l).groups()
            maxLoc = max(int(loc), maxLoc)
        except:
            pass
        try:
            # get minimal p-value for all alleles at each locus
            # this is meaningless for binary alleles, and other method should be used
            # for multi-allele loci.
            # GH output: (for 20 markers)
            # marker loc1  <- locus 0
            # ...
            # marker loc19 <- locus 18
            #
            (loc, pvalue) = scan.match(l).groups()
            idx = int(loc) - 1
            if pvalue == 'nan':
                pvalue = -1
            else:
                pvalue = float(pvalue)
            if not minPvalue.has_key(idx):
                minPvalue[idx] = pvalue
            elif minPvalue[idx] > pvalue:
                minPvalue[idx] = pvalue
        except:
            # does not match
            continue
    fout.close()
    # sort by pos,...
    return [minPvalue.setdefault(x, -1) for x in range(maxLoc)]


def LOD_gh(file, gh='gh'):
    ''' 
    Analyze data using the linkage method of genehunter. Note that this function may not 
    work under platforms other than linux, and may not work with your version of 
    genehunter. As a matter of fact, it is almost unrelated to simuPOP and is provided 
    only as an example how to use python to analyze data.

    Parameters:
        file: file to analyze. This function will look for file.dat and file.pre 
            in linkage format.
        loci: a list of loci at which p-value will be returned. If the list is empty,
            all p-values are returned.
        gh: name (or full path) of genehunter executable. Default to 'gh'

    Return value:
        A list (for each chromosome) of list (for each locus) of p-values.    
    '''
    if not os.path.isfile(file + '.dat') or not os.path.isfile(file + '.pre'):
        print 'Data (%s.dat) or pedigree (%s.pre) file does not exist' % (file, file)
        sys.exit(2)
    # open the pipe for gh
    fin, fout = os.popen2(gh)
    # write to fin
    cmds = '''load markers %s.dat
single point on
scan pedigrees %s.pre
photo tmp.txt
total stat
q
''' % (file, file)
    print "Running GENEHUNTER with commands:"
    print cmds
    print >> fin, cmds
    fin.close()
    # read output 
    # get only loc number and p-value
    scan = re.compile('loc(\d+)\s+[^\s]+\s+[^\s]+\s+([^\s]+)\s*.*')
    minPvalue = {}
    start = 0
    for l in fout.readlines():
        if "Totalling pedigrees:" in l:
            start = 1
        if not start:
            continue
        try:
            # get minimal p-value for all alleles at each locus
            (loc, pvalue) = scan.match(l).groups()
            #print loc, pvalue
            minPvalue[int(loc)-1] = float(pvalue)
        except:
            # does not match
            continue
    fout.close()
    # dict to list
    return [minPvalue.setdefault(x, -1) for x in range(len(minPvalue))]



def ChiSq_test(pop):
    ''' perform case control test

    Parameters;
        pop: loaded population, or population file in simuPOP format. 
            This function assumes that pop has two 
            subpopulations, cases and controls, and have 0 as wildtype and 1 as 
            disease allele. pop can also be an loaded population object.
        
    Return value:
        A list of p-value at each locus.

    Note: this function requires rpy module.
    '''
    # I can not load rpy with simuUtil.py, so here it is
    try:
        import rpy
    except:
        print "RPy module can not be loaded, association test can not be performed"
        sys.exit(1)
    if type(pop) == type(''):
        pop = LoadPopulation(pop)
    # at each locus
    pvalues = []
    Stat(pop, alleleFreq=range(pop.totNumLoci()))
    for loc in range(pop.totNumLoci()):
        # allele frequency
        caseNum = pop.dvars(0).alleleNum[loc]
        if len(caseNum) == 1:
            caseNum.append(0)
        elif len(caseNum) > 2:
            raise 'ChiSq: non-SNP markers are not supported.'
        contNum = pop.dvars(1).alleleNum[loc]
        if len(contNum) == 1:
            contNum.append(0)
        elif len(contNum) > 2:
            raise 'ChiSq: non-SNP markers are not supported.'
        pvalues.append(rpy.r.chisq_test(rpy.with_mode(rpy.NO_CONVERSION, 
            rpy.r.matrix)( caseNum+contNum, ncol=2))['p.value'])
    return pvalues


def LOD_merlin(file, merlin='merlin'):
    ''' run multi-point non-parametric linkage analysis using merlin
    '''
    cmd = 'merlin -d %s.dat -p %s.ped -m %s.map --npl' % (file, file, file)
    resline = re.compile('\s+[\d.+-]+\s+[\d.+-]+\s+[\d.+-]+\s+[\d.+-]+\s+[\d.+-]+\s+([\d.+-]+)')
    print "Running:"
    print cmd
    fout = os.popen(cmd)
    pvalues = []
    for line in fout.readlines():
        try:
            (pvalue,) = resline.match(line).groups()
            try:
                pvalues.append(float(pvalue))
            except:
                pvalues.append(-1)
        except:
            pass
    fout.close()
    return pvalues

    
def VC_merlin(file, merlin='merlin'):
    ''' run variance component method 
        file: file.ped, file.dat, file.map and file,mdl are expected.
            file can contain directory name.
    '''
    cmd = 'merlin -d %s.dat -p %s.ped -m %s.map --pair --vc' % (file, file, file)
    resline = re.compile('\s+([\d.+-]+|na)\s+([\d.+-]+|na)%\s+([\d.+-]+|na)\s+([\d.+-]+|na)\s+([\d.+-]+|na)')
    print "Running"
    print cmd
    fout = os.popen(cmd)
    pvalues = []
    for line in fout.readlines():
        try:
            # currently we only record pvalue
            (pos, h2, chisq, lod, pvalue) = resline.match(line).groups()
            try:
                pvalues.append(float(pvalue))
            except:
                # na?
                pvalues.append(-1)
        except AttributeError:
            pass
    fout.close()
    return pvalues


def Regression_merlin(file, merlin='merlin-regress'):
    ''' run merlin regression method
    '''
    # get information
    cmd = '%s -d %s.dat -p %s.ped -m %s.map' % (merlin, file, file, file)
    print "Running"
    print cmd
    fout = os.popen(cmd)
    #
    pvalues = []
    resline = re.compile('\s+([\d.+-]+|na)\s+([\d.+-]+|na)\s+([\d.+-]+|na)\s+([\d.+-]+|na)%\s+([\d.+-]+|na)\s+([\d.+-]+|na)')
    for line in fout.readlines():
        try:
            (pos, h2, stdev, info, lod, pvalue) = resline.match(line).groups()
            try:
                pvalues.append(float(pvalue))
            except:
                # na?
                pvalues.append(-1)
        except AttributeError:
            pass
    fout.close()
    return pvalues
    

def Sibpair_TDT_gh(pop, sampleSize, penetrance=None, recRate=None, daf=None, gh='gh', keep_temp=False):
    '''
    Draw affected sibpair sample from pop, run TDT using GENEHUNTER

    pop: simuPOP population. It can be a string if path to a file is given.
        This population must
        1. have at least one ancestral generation (parental generation)
        2. have a variable DSL (pop.dvars().DSL) indicating
           the Disease susceptibility loci. These DSL will be removed from
           the samples.
        3. has only binary alleles
    pene: penetrance function, if not given (None), existing affection
        status will be used.
    sampleSize: total sample size N. N/4 is the number of families to ascertain.
    recRate: recombination rate, used in the Linkage file. If not given,
        pop.dvars().recRate[0] will be used. If there is no such variable,
        0.0001 is used.
    daf: disease allele frequency. This is needed for the linkage format
        but I am not sure if it is used by TDT.
    gh: executable name of genehunter, full path name can be given.
    keep_temp: if True, do not remove sample data. Default to False.
    '''
    # load population
    if type(pop) == type(''):
        print "Loading population %s " % pop
        pop = LoadPopulation(pop)
    # apply penetrance        
    if penetrance is not None:
        PyPenetrance(pop, loci=pop.dvars().DSL, func=penetrance)
    # draw affected sibpair sample
    print "Generating affected sibpair sample..."
    (sample,) = AffectedSibpairSample(pop, size=sampleSize/4, times=1)
    # remove DSL from the sample
    sample.removeLoci(pop.dvars().DSL)
    # parameters needed by SaveLinkage
    dir = tempfile.mkdtemp()
    try:
        if recRate is not None:
            r = recRate
        else:
            r = pop.dvars().recRate[0]
    except:
        r = 0.0005
    if daf is not None:
        d = daf
    else:
        d = 0.1
    # save in Linkage format and apply TDT
    pvalues = []
    for ch in range(0, pop.numChrom() ):
        SaveLinkage(pop=sample, output = os.path.join(dir, "Aff_%d" % (ch+1)),
            recombination=r, loci = range(sample.chromBegin(ch), sample.chromEnd(ch)), 
            daf=0.1)
        # process by TDT
        pvalues.extend(TDT_gh(os.path.join(dir, "Aff_%d" % (ch+1)), gh=gh))
    if len(pvalues) != sample.totNumLoci():
        print "Only obtain", len(pvalues), "pvalues. (should have", sample.totNumLoci(), ")"
        sys.exit(0)
    # remove temporary directory
    if not keep_temp:
        shutil.rmtree(dir)
    return pvalues

    
def Sibpair_LOD_gh(pop, sampleSize, penetrance=None, recRate=None, daf=None, gh='gh', keep_temp=False):
    '''
    Draw affected sibpair sample from pop, run Linkage analysis using GENEHUNTER

    pop: simuPOP population. It can be a string if path to a file is given.
        This population must
        1. have at least one ancestral generation (parental generation)
        2. have a variable DSL (pop.dvars().DSL) indicating
           the Disease susceptibility loci. These DSL will be removed from
           the samples.
        3. has only binary alleles
    pene: penetrance function, if not given (None), existing affection
        status will be used.
    sampleSize: total sample size N. N/4 is the number of families to ascertain.
    recRate: recombination rate, used in the Linkage file. If not given,
        pop.dvars().recRate[0] will be used. If there is no such variable,
        0.0001 is used.
    daf: disease allele frequency. This is needed for the linkage format
        but I am not sure if it is used by TDT.
    gh: executable name of genehunter, full path name can be given.
    keep_temp: if True, do not remove sample data. Default to False.
    '''
    # load population
    if type(pop) == type(''):
        print "Loading population %s " % pop
        pop = LoadPopulation(pop)
    # apply penetrance        
    if penetrance is not None:
        PyPenetrance(pop, loci=pop.dvars().DSL, func=penetrance)
    # draw affected sibpair sample
    print "Generating affected sibpair sample..."
    (sample,) = AffectedSibpairSample(pop, size=sampleSize/4, times=1)
    # remove DSL from the sample
    sample.removeLoci(pop.dvars().DSL)
    # parameters needed by SaveLinkage
    dir = tempfile.mkdtemp()
    try:
        if recRate is not None:
            r = recRate
        else:
            r = pop.dvars().recRate[0]
    except:
        r = 0.0005
    if daf is not None:
        d = daf
    else:
        d = 0.1
    # save in Linkage format and apply linkage method
    pvalues = []
    for ch in range(0, pop.numChrom()):
        SaveLinkage(pop=sample, output = os.path.join(dir, "Aff_%d" % (ch+1)),
            recombination=r, loci = range(sample.chromBegin(ch), sample.chromEnd(ch)), 
            daf=0.1)
        pvalues.extend(LOD_gh(os.path.join(dir, "Aff_%d" % (ch+1)), gh=gh))
    if len(pvalues) != sample.totNumLoci():
        print "Only obtain", len(pvalues), "pvalues. (should have", sample.totNumLoci(), ")"
        sys.exit(0)
    # remove temporary directory
    if not keep_temp:
        shutil.rmtree(dir)
    return pvalues
    

def Sibpair_LOD_merlin(pop, sampleSize, penetrance=None, merlin='merlin', keep_temp=False):
    '''
    Draw affected sibpair sample from pop, run multi-point linkage
    analysis using merlin

    pop: simuPOP population. It can be a string if path to a file is given.
        This population must
        1. have at least one ancestral generation (parental generation)
        2. have a variable DSL (pop.dvars().DSL) indicating
           the Disease susceptibility loci. These DSL will be removed from
           the samples.
        3. has only binary alleles
    pene: penetrance function, if not given (None), existing affection
        status will be used.
    sampleSize: total sample size N. N/4 is the number of families to ascertain.
    merlin: executable name of merlin, full path name can be given.
    keep_temp: if True, do not remove sample data. Default to False.
    '''
    # load population
    if type(pop) == type(''):
        print "Loading population %s " % pop
        pop = LoadPopulation(pop)
    # apply penetrance        
    if penetrance is not None:
        PyPenetrance(pop, loci=pop.dvars().DSL, func=penetrance)
    # draw affected sibpair sample
    print "Generating affected sibpair sample..."
    (sample,) = AffectedSibpairSample(pop, size=sampleSize/4, times=1)
    Stat(sample, numOfAffected=True)
    # remove DSL from the sample
    sample.removeLoci(pop.dvars().DSL)
    # save in QTDT
    dir = tempfile.mkdtemp()
    pvalues = []
    for ch in range(0, pop.numChrom() ):
        SaveQTDT(pop=sample, output = os.path.join(dir, "Aff_%d" % (ch+1)),
                loci = range(sample.chromBegin(ch), sample.chromEnd(ch)),
                fields=['affection'])
        # process by merlin
        pvalues.extend(LOD_merlin(os.path.join(dir, "Aff_%d" % (ch+1)), merlin=merlin))
    if len(pvalues) != sample.totNumLoci():
        print "Only obtain", len(pvalues), "pvalues. (should have", sample.totNumLoci(), ")"
        sys.exit(0)
    # remove temporary directory
    if not keep_temp:
        shutil.rmtree(dir)
    return pvalues
    

def CaseControl_ChiSq(pop, sampleSize, penetrance=None):
    '''
    Draw affected sibpair sample from pop, run TDT using GENEHUNTER

    pop: simuPOP population. It can be a string if path to a file is given.
        This population must
        1. have at least one ancestral generation (parental generation)
        2. have a variable DSL (pop.dvars().DSL) indicating
           the Disease susceptibility loci. These DSL will be removed from
           the samples.
        3. has only binary alleles
    pene: penetrance function, if not given (None), existing affection
        status will be used.
    sampleSize: total sample size N. N/4 is the number of families to ascertain.
    keep_temp: if True, do not remove sample data. Default to False.
    '''
    # load population
    if type(pop) == type(''):
        print "Loading population %s " % pop
        pop = LoadPopulation(pop)
    # apply penetrance        
    if penetrance is not None:
        PyPenetrance(pop, loci=pop.dvars().DSL, func=penetrance)
    # draw affected sibpair sample
    print "Generating affected sibpair sample..."
    (sample,) = CaseControlSample(pop, sampleSize/2, sampleSize/2, times=1)
    # remove DSL from the sample
    sample.removeLoci(pop.dvars().DSL)
    # parameters needed by SaveLinkage
    pvalues = ChiSq_test(sample)
    if len(pvalues) != sample.totNumLoci():
        print "Only obtain", len(pvalues), "pvalues. (should have", sample.totNumLoci(), ")"
        sys.exit(0)
    return pvalues
          
    

def QtraitSibs_Reg_merlin(pop, sampleSize, qtrait=None, infoField='qtrait', merlin='merlin-regress', keep_temp=False):
    '''
    Draw affected sibpair sample from pop, run TDT using GENEHUNTER

    pop: simuPOP population. It can be a string if path to a file is given.
        This population must
        1. have at least one ancestral generation (parental generation)
        2. have a variable DSL (pop.dvars().DSL) indicating
           the Disease susceptibility loci. These DSL will be removed from
           the samples.
        3. has only binary alleles
    qtrait:     a function to calculate quantitative trait
    infoField:  information field to store quantitative trait. Default to 'qtrait'
    sampleSize: total sample size N. N/4 is the number of families to ascertain.
    merlin: executable name of merlin, full path name can be given.
    keep_temp: if True, do not remove sample data. Default to False.
    '''
    # load population
    if type(pop) == type(''):
        print "Loading population %s " % pop
        pop = LoadPopulation(pop)
    # generate quantitative trait
    if not pop.hasInfoField(infoField):
        pop.addInfoField(infoField)
    if qtrait is not None:
        PyQuanTrait(pop, loci=pop.dvars().DSL, func=qtrait, infoFields=[infoField])
    # set everyone to be affected
    MaPenetrance(pop, loci=[0], penetrance=[1,1,1])
    # draw affected sibpair sample
    print "Generating sibpair sample..."
    (sample,) = AffectedSibpairSample(pop, size=sampleSize/4, times=1)
    # remove DSL from the sample
    sample.removeLoci(pop.dvars().DSL)
    # parameters needed by SaveLinkage
    dir = tempfile.mkdtemp()
    # save in Linkage format
    pvalues = []
    for ch in range(0, pop.numChrom()):
        SaveQTDT(pop=sample, output = os.path.join(dir, "QTDT_%d" % (ch+1)),
            loci = range(sample.chromBegin(ch), sample.chromEnd(ch)), fields=['qtrait'])
        # process by TDT
        pvalues.extend(Regression_merlin(os.path.join(dir, "QTDT_%d" % (ch+1)), merlin=merlin))
    if len(pvalues) != sample.totNumLoci():
        print "Only obtain", len(pvalues), "pvalues. (should have", sample.totNumLoci(), ")"
        sys.exit(0)
    # remove temporary directory
    if not keep_temp:
        shutil.rmtree(dir)
    return pvalues
    

def QtraitSibs_VC_merlin(pop, sampleSize, qtrait=None, infoField='qtrait', merlin='merlin', keep_temp=False):
    '''
    Draw affected sibpair sample from pop, run TDT using GENEHUNTER

    pop: simuPOP population. It can be a string if path to a file is given.
        This population must
        1. have at least one ancestral generation (parental generation)
        2. have a variable DSL (pop.dvars().DSL) indicating
           the Disease susceptibility loci. These DSL will be removed from
           the samples.
        3. has only binary alleles
    qtrait:     a function to calculate quantitative trait
    infoField:  information field to store quantitative trait. Default to 'qtrait'
    sampleSize: total sample size N. N/4 is the number of families to ascertain.
    merlin: executable name of merlin, full path name can be given.
    keep_temp: if True, do not remove sample data. Default to False.
    '''
    # load population
    if type(pop) == type(''):
        print "Loading population %s " % pop
        pop = LoadPopulation(pop)
    # generate quantitative trait
    if not pop.hasInfoField(infoField):
        pop.addInfoField(infoField)
    if qtrait is not None:
        PyQuanTrait(pop, loci=pop.dvars().DSL, func=qtrait, infoFields=[infoField])
    # set everyone to be affected
    MaPenetrance(pop, loci=[0], penetrance=[1,1,1])
    # draw affected sibpair sample
    print "Generating affected sibpair sample..."
    (sample,) = AffectedSibpairSample(pop, size=sampleSize/4, times=1)
    # remove DSL from the sample
    sample.removeLoci(pop.dvars().DSL)
    # parameters needed by SaveLinkage
    dir = tempfile.mkdtemp()
    # save in Linkage format
    pvalues = []
    for ch in range(0, pop.numChrom()):
        SaveQTDT(pop=sample, output = os.path.join(dir, "Aff_%d" % (ch+1)),
            loci = range(sample.chromBegin(ch), sample.chromEnd(ch)), fields=['qtrait'])
        pvalues.extend(VC_merlin(os.path.join(dir, "Aff_%d" % (ch+1)), merlin=merlin))
    if len(pvalues) != sample.totNumLoci():
        print "Only obtain", len(pvalues), "pvalues. (should have", sample.totNumLoci(), ")"
        sys.exit(0)
    # remove temporary directory
    if not keep_temp:
        shutil.rmtree(dir)
    return pvalues
    

def LargePeds_Reg_merlin(pop, sampleSize, qtrait=None, infoField='qtrait', merlin='merlin-regress', keep_temp=False):
    '''
    Draw affected sibpair sample from pop, run TDT using GENEHUNTER

    pop: simuPOP population. It can be a string if path to a file is given.
        This population must
        1. have at least one ancestral generation (parental generation)
        2. have a variable DSL (pop.dvars().DSL) indicating
           the Disease susceptibility loci. These DSL will be removed from
           the samples.
        3. has only binary alleles
    qtrait:     a function to calculate quantitative trait
    infoField:  information field to store quantitative trait. Default to 'qtrait'
    sampleSize: total sample size N. N/4 is the number of families to ascertain.
    merlin: executable name of merlin, full path name can be given.
    keep_temp: if True, do not remove sample data. Default to False.
    '''
    # load population
    if type(pop) == type(''):
        print "Loading population %s " % pop
        pop = LoadPopulation(pop)
    # generate quantitative trait
    if not pop.hasInfoField(infoField):
        pop.addInfoField(infoField)
    if qtrait is not None:
        PyQuanTrait(pop, loci=pop.dvars().DSL, func=qtrait, infoFields=[infoField])
    # draw affected sibpair sample
    print "Generating large pedigress sample..."
    (sample,) = LargePedigreeSample(pop, minTotalSize=N, maxOffspring=5,  
        minPedSize=8, minAffected=0)
    # remove DSL from the sample
    sample.removeLoci(pop.dvars().DSL)
    # parameters needed by SaveLinkage
    dir = tempfile.mkdtemp()
    # save in Linkage format
    pvalues = []
    for ch in range(0, pop.numChrom()):
        SaveQTDT(pop=sample, output = os.path.join(dir, "QTDT_%d" % (ch+1)),
            loci = range(sample.chromBegin(ch), sample.chromEnd(ch)), fields=['qtrait'])
        pvalues.extend(Regression_merlin(os.path.join(dir, "Aff_%d" % (ch+1)), merlin=merlin))
    # remove temporary directory
    if len(pvalues) != sample.totNumLoci():
        print "Only obtain", len(pvalues), "pvalues. (should have", sample.totNumLoci(), ")"
        sys.exit(0)
    if not keep_temp:
        shutil.rmtree(dir)
    return pvalues
    

def LargePeds_VC_merlin(pop, sampleSize,  qtrait=None, infoField='qtrait', merlin='merlin', keep_temp=False):
    '''
    Draw affected sibpair sample from pop, run TDT using GENEHUNTER

    pop: simuPOP population. It can be a string if path to a file is given.
        This population must
        1. have at least one ancestral generation (parental generation)
        2. have a variable DSL (pop.dvars().DSL) indicating
           the Disease susceptibility loci. These DSL will be removed from
           the samples.
        3. has only binary alleles
    qtrait:     a function to calculate quantitative trait
    infoField:  information field to store quantitative trait. Default to 'qtrait'
    sampleSize: total sample size N. N/4 is the number of families to ascertain.
    merlin: executable name of merlin, full path name can be given.
    keep_temp: if True, do not remove sample data. Default to False.
    '''
    # load population
    if type(pop) == type(''):
        print "Loading population %s " % pop
        pop = LoadPopulation(pop)
    # generate quantitative trait
    if not pop.hasInfoField(infoField):
        pop.addInfoField(infoField)
    if qtrait is not None:
        PyQuanTrait(pop, loci=pop.dvars().DSL, func=qtrait, infoFields=[infoField])
    # draw affected sibpair sample
    print "Generating large pedigree sample..."
    (sample,) = LargePedigreeSample(pop, minTotalSize=N, maxOffspring=5,  
        minPedSize=8, minAffected=0)
    # remove DSL from the sample
    sample.removeLoci(pop.dvars().DSL)
    # parameters needed by SaveLinkage
    dir = tempfile.mkdtemp()
    pvalues = []
    for ch in range(0, pop.numChrom()):
        SaveQTDT(pop=sample, output = os.path.join("%s%d" % (dirPrefix, ns), "QTDT_%d" % (ch+1)),
            loci = range(sample.chromBegin(ch), sample.chromEnd(ch)), fields=['qtrait'])
        pvalues = VC_merlin(os.path.join(dir, "Aff_%d" % (ch+1)), merlin=merlin)
    # remove temporary directory
    if len(pvalues) != sample.totNumLoci():
        print "Only obtain", len(pvalues), "pvalues. (should have", sample.totNumLoci(), ")"
        sys.exit(0)
    if not keep_temp:
        shutil.rmtree(dir)
    return pvalues



if __name__ == "__main__":
    pass
