#!/usr/bin/env python
#
# testing operator behaviors for simupoop.
#
# Bo Peng (bpeng@rice.edu)
#
# $LastChangedRevision$
# $LastChangedDate$
#

import simuOpt
simuOpt.setOptions(quiet=True)

from simuPOP import *
import unittest, os, sys

# record active generations in pop.dvars().hist
def genRecorder(pop):
    try:
        pop.dvars().hist.append(pop.dvars().gen)
    except:
        pop.dvars().hist = [pop.dvars().gen]
    return True

def opRecorder(*args, **kwargs):
    return pyOperator(func=genRecorder, *args, **kwargs)

class TestOperator(unittest.TestCase):

    def testStage(self):
        'Testing stage parameter of operators'
        simu = simulator(
            population(size=[20, 80], loci=[3]),
                randomMating())
        simu.evolve(
            preOps = [initByFreq([0.2, 0.8])],
            ops = [
                recombinator(rates=0.001),
                stat(stage=PrePostMating),
                stat(alleleFreq=[1]),
                kamMutator(k=10, rates=0.00005, loci=[0,2])
            ],
            postOps = [stat()],
            #dryrun=True,
            gen=10
        )

    def testActiveGen(self):
        'Testing active generation specifications'
        def getActiveGens(endGen=20, *args, **kwargs):
            d = opRecorder(*args, **kwargs)
            simu = simulator(population(), cloneMating())
            simu.evolve(ops=[d], gen=endGen)
            return simu.population(0).dvars().hist
        self.assertEqual(getActiveGens(begin=2, end=10),
            range(2,11))
        self.assertEqual(getActiveGens(begin=2, end=10, step=2),
            range(2,11,2))
        self.assertEqual(getActiveGens(begin=2, step=2),
            range(2,20,2))
        self.assertEqual(getActiveGens(step=2), range(0,19,2))
        self.assertEqual(getActiveGens(), range(0,20))
        self.assertEqual(getActiveGens(at=[2,5,9]), [2,5,9])
        self.assertEqual(getActiveGens(at=[2,5,-1]), [2,5,19])
        self.assertEqual(getActiveGens(begin=-10), range(10,20))
        # 20=-1, 16=-5
        self.assertEqual(getActiveGens(begin=-10, end=-5), range(10,16))
        #
        self.assertEqual(getActiveGens(begin=-10, step=2, end=-5), range(10,16,2))
        self.assertRaises( exceptions.ValueError,
            getActiveGens, begin=-10, step=-3, end=-5 )

    def testReplicate(self):
        'Testing replicate related functions'
        simu = simulator(population(), cloneMating(), rep=3)
        simu.evolve(
            ops = [opRecorder(rep=-1)],
            gen=10
        )
        try:
            simu.population(0).dvars().hist
        except exceptions.AttributeError:
            pass
        try:
            simu.population(1).dvars().hist
        except exceptions.AttributeError:
            pass
        self.assertEqual(simu.population(2).dvars().hist, range(10))

    def assertFileContent(self, file, text):
        f = open(file)
        t = f.read()
        f.close()
        self.assertEqual(t, text)

    def testOutput(self):
        'Testing output specifications'
        simu = simulator( population(),
                cloneMating(), rep=5)
        simu.evolve([
            pyOutput("a", output=">a.txt"),
            ], gen=10)
        # although everyone have written to this file,
        # only the last one will be kept
        self.assertFileContent("a.txt", 'a')
        os.remove('a.txt')
        #
        # you can ignore >
        simu.setGen(0)
        simu.evolve([
            pyOutput("a", output="a.txt"),
            ], gen=10)
        # although everyone have written to this file,
        # only the last one will be kept
        self.assertFileContent("a.txt", 'a')
        os.remove('a.txt')
        #
        # >>
        simu.setGen(0)
        simu.evolve([
            pyOutput("a", output=">>a.txt"),
            ], gen=10)
        # a is appended 5 rep * 11 generations
        self.assertFileContent("a.txt", 'a'*50)
        os.remove('a.txt')
        #
        # rep = ...
        simu.setGen(0)
        simu.evolve([
            pyOutput("a", output=">>a.txt", rep=-1),
            ], gen=10)
        # a is appended 5 rep * 11 generations
        self.assertFileContent("a.txt", 'a'*10)
        os.remove('a.txt')

    def testOutputExpr(self):
        'Testing the usage of output expression'
        simu = simulator( population(),
            cloneMating(), rep=5)
        # each replicate
        simu.evolve([
            pyOutput("a", output="!'rep%d.txt'%rep"),
            ], gen=10)
        # although everyone have written to this file,
        # only the last one will be kept
        for i in range(5):
            self.assertFileContent("rep%d.txt"%i, 'a')
            os.remove('rep%d.txt'%i)
        #
        # you can ignore >
        simu.setGen(0)
        simu.evolve([
            pyOutput("a", output="!'>rep%d.txt'%rep"),
            ], gen=10)
        # although everyone have written to this file,
        # only the last one will be kept
        for i in range(5):
            self.assertFileContent("rep%d.txt"%i, 'a')
            os.remove('rep%d.txt'%i)
        #
        # >>
        simu.setGen(0)
        simu.evolve([
            pyOutput("a", output="!'>>rep%d.txt'%rep"),
            ], gen=10)
        # a is appended 1 rep * 11 generations
        for i in range(5):
            self.assertFileContent("rep%d.txt"%i, 'a'*10)
            os.remove('rep%d.txt'%i)
        # each generation?
        simu.setGen(0)
        simu.evolve([
            pyOutput("a", output="!'>>gen%d.txt'%gen"),
            ], gen=10)
        # a is appended 1 rep * 11 generations
        for i in range(10):
            self.assertFileContent("gen%d.txt"%i, 'a'*5)
            os.remove('gen%d.txt'%i)

    def testOutputFunc(self):
        '''Testing output to a function'''
        simu = simulator(population(), cloneMating(), rep=5)
        def func1(msg):
            self.assertEqual(msg, 'func1')
        def func2(msg):
            self.assertEqual(msg, 'func2')
        # each replicate
        simu.evolve([
            pyOutput("func1", output=func1),
            pyOutput("func2", output=func2),
            ], gen=10)

    def testInfoEval(self):
        '''Testing operator infoEval'''
        pop = population(10, infoFields=['a', 'b'])
        InfoEval(pop, expr='b', stmts='b=a+1', output='')
        # information field b is NOT updated
        self.assertEqual(pop.indInfo('b'), tuple([0]*10))
        #
        # use population variable
        pop.vars()['c'] = 5
        # this should fail because there is no information field c
        self.assertRaises(exceptions.RuntimeError, InfoEval, pop, 'c+4')
        # usePopVars is needed
        InfoEval(pop, 'c+4', usePopVars=True, output='')


    def testInfoExec(self):
        '''Testing operator infoExec'''
        pop = population(10, infoFields=['a', 'b'])
        InfoExec(pop, 'b=a+1')
        self.assertEqual(pop.indInfo('b'), tuple([1]*10))
        InfoExec(pop, 'a+=1')
        self.assertEqual(pop.indInfo('a'), tuple([1]*10))
        # this will not do anything because there is no c to be updated.
        InfoExec(pop, 'c=a+b')
        #
        # use population variable
        pop.vars()['c'] = 5
        # this should fail because there is no information field c
        self.assertRaises(exceptions.RuntimeError, InfoExec, pop, 'b=c+4')
        # usePopVars is needed
        InfoExec(pop, 'b=c+4', usePopVars=True)
        self.assertEqual(pop.indInfo('b'), tuple([9]*10))
        #
        # as an operator
        simu = simulator(pop, cloneMating())
        simu.evolve(
            preOps = [infoExec('b=0')],
            ops = [
                infoEval(r"'\t%.1f' % b", stage=PostMating, output=''),
                infoExec('b+=1', output=''),
                pyOutput('\n', output=''),
            ],
            gen = 4
        )


    def testCloseOutput(self):
        '''Testing global function CloseOutput'''
        pop = population(100, loci=[2])
        Dump(pop, output='a.pop')
        size = len(open('a.pop').read())
        self.assertRaises(exceptions.RuntimeError, CloseOutput, 'a.pop')
        Dump(pop, output='>>a.pop')
        CloseOutput('a.pop')
        self.assertEqual(len(open('a.pop').read()), size)
        self.assertRaises(exceptions.RuntimeError, CloseOutput, 'a.pop')
        self.assertRaises(exceptions.RuntimeError, CloseOutput, 'b.pop')
        Dump(pop, output='>>a.pop')
        Dump(pop, output='>>a.pop')
        self.assertEqual(len(open('a.pop').read()), size * 2)
        #
        Dump(pop, output='>>>a.pop')
        Dump(pop, output='>>>a.pop')
        self.assertEqual(len(open('a.pop').read()), size * 4)
        CloseOutput('a.pop')
        self.assertRaises(exceptions.RuntimeError, CloseOutput, 'a.pop')


if __name__ == '__main__':
    unittest.main()
