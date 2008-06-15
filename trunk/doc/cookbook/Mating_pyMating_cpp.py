#!/usr/bin/env python

'''
 This file demonstrate the use of pyMating, using a parent choosr that
 choose a female that is geographically closest to a random male. A hybrid
 parent chooser pyParentsChooser is used, which will call a Python
 generator function repeatedly to get parents.

 Such hybrid- and pure- Python operators and mating schemes provide a
 very powerful and flexible interface to implement customized genetic effects
 and mating schemes. However, because these functions are implemented in Python,
 they can significantly reduce the performance of your simuPOP script if complex
 algorithms are involved, especially when the Python functions are called
 repeatedly. This problem can be addressed by implementing these functions in
 C++.

 This example demonstrates how to implement some functions in C++, and wrap
 them so that they can be imported into python. This is basically how simuPOP
 is written, and is an important technique to improve the efficiency of
 your simuPOP scripts.

 Several files are involved in this process:
 1. This python file that import the C++ module.
 2. .h and/or .cpp files to re-impmenent the most time-consuming parts in C++.
 3. An interface file Mating_pyMating_cpp.i, which tells an automatic wrapper
    generating program SWIG how to wrap the code.

 To compile and load functions defined in this interface file, you will need
 to:

 1. download and install SWIG.

 2. generate a wrap using command:

	> swig -python -templatereduce -c++ -shadow -nodefaultctor  -keyword Mating_pyMating_cpp.i

	A wrapper file Mating_pyMating_cpp_wrap.cxx will be generated. Options -c++
    -shadow are not needed if the header file only contains C/C++ functions.

 3. compile the wrapper, and your .cpp files (if available)

    Under unix/linux, using g++, you can compile this file using

	> g++ -fpic -c Mating_pyMating_cpp_wrap.cxx -I /usr/local/include/python2.5/
	> g++ -shared Mating_pyMating_cpp_wrap.o /usr/lib64/libstdc++.so.5 -o _Mating_pyMating_cpp_impl.so

 4.	You can then try to import your module using

	> python -c 'import Mating_pyMating_cpp_impl'

Note that options used are system dependent. It is important to note the _ before the .so
module name. XXX.py is generated by swig, which import _XXX.so. This is not needed
if you do not use C++ and shadow classes.

 $Date$
 $Revision$
 $HeadURL$


'''


from simuPOP import *
from random import normalvariate, randint

# if a python module rpy is available, use R to plot the location
# of all individuals.
try:
    from rpy import *
    has_rpy = True
except:
    has_rpy = False

# try to load a more efficient version of parentsChooser, which is defined in
# Mating_pyMating_cpp.h and .i. This file must be compiled to a Python-lodablebe
# module to be imported into this script.
try:
    from Mating_pyMating_cpp_impl import *
    has_cpp_chooser = True
except:
    print "Module Mating_pyMating_cpp_cpp can not be loaded"
    print "The python version will be used"
    has_cpp_chooser = False


def locOfOffspring(loc):
    '''set offspring loc from parental locs'''
    # loc = (dad_x, dad_y, mom_x, mom_y)
    #
    # move to (dad_x + mom_x)/2 + N(0, 1), (dad_y + mom_y)/2 + N(0,1)
    new_x = (loc[0]+loc[2])/2. + normalvariate(0, 1)
    new_y = (loc[1]+loc[3])/2. + normalvariate(0, 1)
    # limit to region [-5, 5] x [-5, 5]
    new_x = min(new_x, 5)
    new_x = max(new_x, -5)
    new_y = min(new_y, 5)
    new_y = max(new_y, -5)
    return (new_x, new_y)


def plotInds(pop):
    '''plot the location of individuals. This requires R and rpy. '''
    if not has_rpy:
        return True
    r.postscript('loc_%d.eps' % pop.gen())
    r.plot(0, 0, xlim=[-5, 5], ylim=[-5, 5], type='n',
        xlab='x', ylab='y',
        main='Locations of individuals at generation %d' % pop.gen())
    for ind in pop.individuals():
        r.points(ind.info(0), ind.info(1))
    r.dev_off()
    return True


def parentsChooser(pop, sp):
    '''Choose parents according to their locations. Because this is only a
       demonstration, performance is not under consideration.
    '''
    ################### The C++ version ############
    if has_cpp_chooser:
        # create an object with needed information ...
        pc = parentsChooser_cpp(
            [x.info('x') for x in pop.individuals() if x.sex() == Male],
            [x.info('y') for x in pop.individuals() if x.sex() == Male],
            [x.info('x') for x in pop.individuals() if x.sex() == Female],
            [x.info('y') for x in pop.individuals() if x.sex() == Female],
            random.randint(0, 1e8))
        while True:
            # and return indexes of parents
            yield pc.chooseParents()
    ##################### The Python version ###############
    males = [x for x in range(pop.popSize()) if pop.individual(x).sex() == Male]
    females = [x for x in range(pop.popSize()) if pop.individual(x).sex() == Female]
    if len(males) == 0 or len(females) == 0:
        print 'Lacking male or female. Existing'
        yield (None, None)
    while True:
        # randomly choose a male
        male = males[random.randint(0, len(males)-1)]
        # choose its closest female
        diff_x = [pop.individual(x).info(0) - pop.individual(male).info(0) for x in females]
        diff_y = [pop.individual(x).info(1) - pop.individual(male).info(1) for x in females]
        dist = [diff_x[i]**2 + diff_y[i]**2 for i in range(len(females))]
        female = females[dist.index(min(dist))]
        #print male, female
        yield (male, female)


def simuGeoMating(size, gen):
    '''
    size  population size
    gen   number of generations to run
    '''
    pop = population(size, loci=[1], infoFields=['x', 'y'])
    simu = simulator(pop,
        pyMating(pyParentsChooser(parentsChooser), mendelianOffspringGenerator())
    )
    simu.evolve(
        preOps = [initByFreq([0.5, 0.5])],
        ops = [
            pyEval(r'"%s\n" % gen'),
            pyTagger(func=locOfOffspring, infoFields=['x', 'y']),
            pyOperator(func=plotInds),
        ],
        end = gen
    )

if __name__ == '__main__':
    simuGeoMating(1000, 4)
