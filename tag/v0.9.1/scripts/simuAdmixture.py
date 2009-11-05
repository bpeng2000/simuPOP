#!/usr/bin/env python
'''
This script simulates an admixed population based on the HapMap dataset. Please
read this help message carefully, making sure your know how this script works,
then run a few test commands, before you explore the capacity of this script.


Step 0: Prepare HapMap dataset (call scripts/loadHapMap.py if available)
=========================================================================

This script makes use of the HapMap dataset. The dataset is downloaded, imported
and saved in simuPOP format automatically, using script scripts/loadHapMap.py.
If loadHapMap.py can not be imported (not in the working directory or in $PYTHONPATH),
please try to run loadHapMap.py manually and provide a path with files hapmap_XX.pop
to parameter --HapMap_dir.


Step 1: Determine which populations and markers to use
======================================================

The initial population consists of one, two or three hapmap populations
(param --pops), and a selected set of markers. You can start from
all hapmap markers or a marker list in the format of
'chromosome position name', such as (no header is required).

1 2103664 rs1496555
1 2708522 rs1338382
1 2719853 rs10492936
1 2734227 rs10489589
...

If more fields are given, they will be ignored.

You can refine your selection using
  1. which chromosome(s) to use (param --chrom)
  2. number of markers to use on each chromosome (param --numMarkers)
  3. starting and ending positions (param --startPos and --endPos)
  4. minimal allele frequency (param --minAF)
  5. minimal allele frequency differences between hapmap populations
    (param --minDiffAF). This criteria can be used to find markers
    of high ancestray information content.
  6. minimal distance between markers (param --minDist)

Note that 'position' in the marker list is assumed to be in base pair
(as in Affymetrix or Illumina annotation data). Marker positions
are converted to centiMorgan by dividing the positions by 10^6 (i.e.
1 centiMorgan = 1 M basepairs). Starting and ending position should be
inputted in centiMorgan. Note that sometimes not all requirements can
be met at the same time.

Each simulation will be given a name and all files will be saved to a
directory named after it. A file markers.lst will be saved to directory
$name.


Step 2: Evolve the population
==============================

Instant population expansion
-----------------------------

The population is expanded instantly by copying individual 10 (param --initCopy)
time to avoid quick loss of heterogenity due to small population sizes.


Recombination, mutation, migration and selection
-------------------------------------------------

During the evolution, recombination at a rate of 0.01 per cM or Mb 
(param --recIntensity) will be applied. If a physical map is used, the
recombination rate between two adjacent markers is recIntensity * physical
distance (in Mb) between them. If a genetic map is used, the recombination
rate between two adjacent markers is recIntentisy * genetic distance (in cM)
between them. We use fine-scale genetic map that is downloaded from HapMap,
estimated using methods described in McVean et al, (2004) Science 304: 581.

Gene conversion is allowed. The impact of gene conversion depends on the 
density of markers because gene conversion generally works over short
distances.

Mutation at a rate of 1e-7 per nucleotide per generation (param --mutaRate)
is applied during evolution.

Low-level background migrations between populations are allowed. At each
generation, The migration rate between each pair of populations is 0.0001 
(or 0.01%, param --backMigrRate).

Selection on a number of loci can be applied to selected loci. These loci
are supposed to have disease predisposing alleles (though selection does
not have to work against them). Because we assume that these loci will
be used to simulate a disease or a quantitative trait, we control the allele
frequency of these loci so that they will have consistent disease allele
frequency at the end of the simulation.

A special controlled mating scheme is used for this purpose, which requires
simulated disease allele frequency trajectories. The trajectories can be
simulated using a backward (Peng 2007, PLoS Genetics) or a forward-time
approach. In a forward-time approach, the allele frequency is repeatedly
simulated forward-in-time until it reaches a designed frequency range.
In a backward-time approach, the allele frequency is simulated backward-in-time
until it reaches zero. This implies that there is no disease allele
at these loci at the beginning of the simulation so these alleles are
removed at first.

Slow population expansion
--------------------------

The population then evolves for a relatively short period of time (param --initGen)
with no or slow population expansion (param --initSize). This step is designed to
mix these copied individuals. 

We consider populations at the end of this stage as the populations around 20k years
ago (Pritchard et al (1999), Mol Biol Evol, 16), that have been evolved separately 
from the Out-Of-Africa population for abut 20k years. Note that 20k years means
1000 generations (param --expandGen).


Rapid population expansion
---------------------------

Evolve the population subject to rapid population expansion for another
1000 (param --expandGen) generations. This is to mimic the rapid
population expansion in the past 20k years. Exponential population
growth model is used.

The resulting population of this generation is saved as $name/expanded.pop
(--param expandedName). If this file exists, and parameter --useSavedExpanded
is specified, the population will be loaded directly.

A parameter --scale can be used to speed up the simulation. With this parameter,
the intensity of mutation, recombinatin, and migration are magnified by --scale
and the actually evolved generations are reduced by a factor of --scale. This
technique is primarily used to control allele frequency and linkage disequilibrium
patterns. Please see Peng 2008, in preparation, for a detailed description.

Step 3. Mix the subpopulations (optional)
==========================================

A migration rate matrix can be given to migrate individuals between
population for a specified generations. Migration is stopped afterwards
to allow 
namely 'Hybrid Isolations' and 'Continuous Gene Flow' are provided.
The first model simply mix the subpopulations and form a single population.
The second model allows stable migration between subpopulations during
the migration period. More advanced migration model, with changing
migration rates can be specified using a 'Customized' model. To use
the last model, you will have to modify the 'migrFunc' function in
this script. Note that it is possible to create a separate population,
with individuals migrated from existing populations.

e.g.

'Hybrid Isolations':  Merge all HapMap populations instantly.

'Continuous Gene Flow', two HapMap populations, with migration rate
    [[1, 0],
     [0.1, 0.9]]
  10% of individuals will migrate from population 1 to 0 at each
  generation. Note that the population sizes will change as a result
  of migration so the exact number of migrants varies from generation
  to generation.

'Continuous Gene Flow', three HapMap populations, with migration rate
    [[1, 0, 0],
     [0.1, 0.9, 0],
     [0.1, 0, 0.9]]
   10% of individuals from population 2 and 3 migrate to population 1.

'Continuous Gene Flow', two HapMap populations, with migration rate
    [[0.8, 0, 0.2],
     [0, 0.8, 0.2]]
    A new population is created, and gets 20% of individuals from
    population 1 and 2 at each generation.


The result of this stage will be saved to $name/admixed.pop (--param admixedName)


Test scripts
==============

1. Example1:

This example uses mostly default parameters, it can be executed by

simuAdmixture.py  --name='example1' --chrom='[2]' \
    --numMarkers='[2000]' --startPos='[51]'


'''

from simuOpt import *
setOptions(alleleType='binary')
from simuPOP import *
from hapMapUtil import getMarkersFromName, getMarkersFromRange

import os, sys, math
from types import *
from exceptions import ValueError, SystemError
from simuUtil import SaveQTDT, SaveMerlinPedFile, MigrIslandRates

HapMap_pops = ['CEU', 'YRI', 'JPT+CHB']

options = [
    {'arg': 'h',
     'longarg': 'help',
     'default': False,
     'description': 'Print this usage message.',
     'allowedTypes': [NoneType, type(True)],
     'jump': -1                    # if -h is specified, ignore any other parameters.
    },
    {'longarg': 'name=',
     'default': 'simu',
     'useDefault': True,
     'allowedTypes': [StringType],
     'label': 'Name of the simulation',
     'description': '''Name of this simulation. A directory with this name
                will be created. Configuration file (.cfg), marker list and
                various populations will be saved to this directory''',
    },
    {'longarg': 'useSavedExpanded=',
     'default': False,
     'useDefault': True,
     'allowedTypes': [BooleanType],
     'jump': 'expandedName',
     'label': 'Use saved expanded population',
     'description': '''If set to true, load specified or saved $name/expanded.pop and
                skip population expansion'''
    },
    #
    {'separator': 'Progress record and report'},
    {'longarg': 'step=',
     'default': 100,
     'label': 'Progress report interval',
     'useDefault': True,
     'allowedTypes': [IntType, LongType],
     'description': '''Gap between generations at which population statistics are
                calculated and reported. (This parameter is affected by --scale)'''
    },
    {'longarg': 'saveStep=',
     'default': 0,
     'label': 'Save population interval',
     'useDefault': True,
     'allowedTypes': [IntType, LongType],
     'description': '''Initial, expanded and admixed populations will be saved. This option
                allows you to save populations every --saveStep generations, starting
                from population expansion. If saveStep = 0 (default), no intermediate population
                will be saved. Otherwise, populations at generation 0, saveStep, 2*saveStep, ...
                will be saved as expand_xx.pop where xx is generation number.''',
    },
    {'longarg': 'saveName=',
     'default': 'expand_',
     'useDefault': True,
     'description': '''Prefix of the intermediately saved populations, relative to simulation path''',
     'allowedTypes': [StringType],
    },
    {'separator': 'Populations and markers to use'},
    {'longarg': 'HapMap_dir=',
     'default': 'HapMap',
     'useDefault': True,
     'label': 'HapMap data directory',
     'description': '''Directory to store HapMap data in simuPOP format. Hapmap
                data file hapmap_??.pop in this directory, if exits, will be
                loaded directly. Otherwise, module loadHapMap.py (usually under
                /path/to/simuPOP/scripts) will be used to download, import, and
                save HapMap data in simuPOP formats. If this module can not be
                imported, you can either add its path to environmental variable
                $PYTHONPATH or run this script manually.''',
     'allowedTypes': [StringType],
     #'validate': valueValidDir(),
    },
    {'longarg': 'pops=',
     'default' : ['CEU'],
     'useDefault': True,
     'label' : 'HapMap populations',
     'description': '''Which HapMap populations to use?''',
     'allowedTypes': [TupleType, ListType],
     'chooseFrom': HapMap_pops,
     'validate': valueListOf(valueOneOf(HapMap_pops)),
    },
    {'longarg': 'markerList=',
     'default': '',
     'useDefault': True,
     'label': 'Marker list file',
     'description': '''A file with a list of marker names, in the form of
                "chrom_number marler_pos marker_name". Markers that on a chromosome that are not
                in the chromosome list (parameter --chrom) are ignored. The first header line and
                lines start with # is ignored. If numMarkers, startPos, endingPos, minDist 
                are also specified, the first numMarkers between startPos and endingPos will be used.
                This script assumes that the marker position in the
                list file is in base pair, and will use pos/1000000 as cM to
                compare marker location. If more fields are given, others are ignored.''',
     'allowedTypes': [StringType],
     'validate': valueOr(valueEqual(''), valueValidFile()),
    },
    {'longarg': 'chrom=',
     'default': [2],
     'label': 'Chromosomes to use',
     'description': '''A list of chromosomes to use from the HapMap data. When multiple
                chromosomes are involves, numMarkers, if used, should be a list that specicy
                number of markers on each chromosome. The same rule applies to startPos
                and endingPos as well.''',
     'allowedTypes': [TupleType, ListType],
     'validate': valueListOf(valueBetween(1, 22)),
    },
    {'longarg': 'numMarkers=',
     'default': [1000],
     'label': 'Number of markers to use',
     'description': '''Number of markers to use from the marker list file. If 0 is used,
                all markers that satisfy conditions startPos, endingPos, minDist will
                be used.''',
     'allowedTypes': [TupleType, ListType],
     'validate': valueOr(valueGT(0), valueListOf(valueGE(0)))
    },
    {'longarg': 'startPos=',
     'default': [0],
     'useDefault': True,
     'label': 'staring position',
     'description': '''Starting position of the markers. If multiple
                chromosomes are used, the positions for each
                chromosome can be specified as a list.''',
     'allowedTypes': [TupleType, ListType],
     'validate': valueOr(valueGE(0), valueListOf(valueGE(0)))
    },
    {'longarg': 'endingPos=',
     'default': [0],
     'useDefault': True,
     'label': 'Ending position',
     'description': '''Ending position of the markers. Ignored if its value
                is 0.  If multiple chromosomes are used, the positions for each
                chromosome can be specified as a list. ''',
     'allowedTypes': [TupleType, ListType],
     'validate': valueOr(valueGE(0), valueListOf(valueGE(0)))
    },
    {'longarg': 'minAF=',
     'default': 0,
     'useDefault': True,
     'label': 'Minimal allele frequency',
     'description': '''Minimal allele frequency, only used for picking markers
                from the HapMap dataset''',
     'allowedTypes': [IntType, LongType, FloatType],
     'validate': valueGE(0)
    },
    {'longarg': 'minDiffAF=',
     'default': 0,
     'useDefault': True,
     'label': 'Minimal allele frequency difference',
     'description': '''Minimal allele frequency difference between two HapMap population,
                , can only be used when two HapMap populations are used. This options can be
                used to choose markers with high ancestry information content.''',
     'allowedTypes': [IntType, LongType, FloatType],
     'validate': valueGE(0)
    },
    {'longarg': 'minDist=',
     'default': 0,
     'useDefault': True,
     'label': 'Minimal distance between markers (cM)',
     'allowedTypes': [IntType, LongType, FloatType],
     'description': '''Minimal distance between markers (in the unit of cM).
                Can be used for both methods.''',
    },
    {'longarg': 'initName=',
     'default': 'init.pop',
     'useDefault': True,
     'description': '''Name of the initial population, relative to simulation path''',
     'allowedTypes': [StringType],
    },
    #
    {'separator': 'Mutation, recombination, etc'},
    {'longarg': 'mutaRate=',
     'default': 5e-7,
     'useDefault': True,
     'label': 'Mutation rate',
     'allowedTypes': [IntType, FloatType],
     'description': '''Mutation rate using a k-allele model with k = 2.''',
     'validate': valueBetween(0,1),
    },
    {'longarg': 'recMap=',
     'default': 'genetic',
     'useDefault': True,
     'label': 'Marker map to use',
     'description': '''Use physical (base pair) or genetic map to perform
                recombination. If physical map is used, the recombination rate
                would be marker distance in basepair / 1M * recIntensity.
                If genetic map is used, the recombination rate would be map
                distance * recIntensity. The hapmap populations use physical
                distance as loci potitions, and store genetic distance as
                a population variable genDist.
                ''',
     'allowedTypes': [StringType],
     'chooseOneOf': ['physical', 'genetic']
     },
    {'longarg': 'recIntensity=',
     'default': 0.01,
     'label': 'Recombination intensity',
     'useDefault': True,
     'allowedTypes': [FloatType],
     'description': '''Recombination intensity per cm/Mb, this should not be changed unless
                you really know what you are doing. When a physical map is used, this is the
                recombination intensity between adjacent markers. For example, two markers
                that are 10kb apart (0.00001 cM apart) will have recombination
                rate 10^-5*0.01 (the default value) = 10^-6. If a genetic map is used,
                the recombination rate is recIntensity times the map distance between
                two adjacent markers.
     ''',
     'validate': valueBetween(0,1),
    },
    {'longarg': 'convProb=',
     'label': 'Gene conversion probability',
     'default': 0,
     'useDefault': True,
     'allowedTypes': [IntType, FloatType],
     'description': '''Gene conversion is considered as a sub-event during recombination.
                    If a non-zero --convProb value is given, a recombination event will
                    have this probability of becoming an gene conversion event, which 
                    conceputally will lead to another recombination(-back) event --convLength
                    after the current marker. Gene conversion is by default disabled.''',
     'validate': valueBetween(0, 1)
    },
    {'longarg': 'convMode=',
     'label': 'Model for conversion length',
     'default': 'Tract length',
     'useDefault': True,
     'allowedTypes': [StringType],
     'description': '''How to determine the length of a gene conversion. The exact meaning
                    of parameter --convParam is determined by this parameter.
                    'Tract length': --convParam is the length of converted region in cM.
                        Note that the marker distance is usually around 10kb (0.001cM) and
                        the track lengths range from 50 - 2500 bp.
                    'Number of markers': convert a fixed number of markers
                    'Geometric distribution': The number of markers converted is determined
                        by a geometric distribution.
                    'Exponential distribution': The tract length is determined by an
                        exponential distribution.
                    ''',
     'chooseOneOf': ['Tract length', 'Number of markers', 'Geometric distribution',
        'Exponential Distribution'],
     'validate': valueOneOf(['Tract length', 'Number of markers', 'Geometric distribution',
        'Exponential Distribution']),
    },
    {'longarg': 'convParam=',
     'label': 'Conversion parameter',
     'default': 0.02,
     'useDefault': True,
     'allowedTypes': [IntType, FloatType],
     'description': '''The meaning of this parameter is determined by --convMode. By default,
                when --convMode='Tract length', this parameter means that each gene conversion
                event will convert a region of 0.02cM ~ 20kb region.''',
     'validate': valueGE(0)
    },
    {'longarg': 'forCtrlLoci=',
     'label': 'Forward controlled loci',
     'default': [],
     'useDefault': True,
     'allowedTypes': [TupleType, ListType],
     'description': '''A list of markers (by name) whose allele frequency will be
                controlled during this stage of evolution. A forward-time trajectory
                simulation algorithm will be used. Currently, only one of
                --forCtrlLoci and --backCtrlLoci is allowed. Note that allele frequencies
                are only controlled in the expansion stage.'''
    },
    {'longarg': 'forCtrlFreq=',
     'label': 'Ending allele frequency at forward controlled loci',
     'default': [],
     'useDefault': True,
     'allowedTypes': [TupleType, ListType],
     'description': '''A list of allele frequency ranges for each controlled locus.
                If a single range is given, it is assumed for all markers. An example
                of the parameter is [[0.18, 0.20], [0.09, 0.11]]. If there are multiple
                populations, the disease alleles are distributed in proportion to
                their distribution in the hapmap population.'''
    },
    {'longarg': 'backCtrlLoci=',
     'label': 'Backward controlled loci',
     'default': [],
     'useDefault': True,
     'allowedTypes': [TupleType, ListType],
     'description': '''A list of markers (by name) whose mutants, if any, will be removed
                at the beginning of population expansion stage. A mutant will be introduced
                as the result of mutation. The frequency trajectory will be simulated
                using a backward approach (see Peng 2007, PLoS Genetics). Currently,
                only one of --forCtrlLoci and --backCtrlLoci is allowed. Note that allele
                frequencies are only controlled in the expansion stage.''',
    },
    {'longarg': 'backCtrlFreq=',
     'label': 'Ending allele frequency at backward controlled loci',
     'default': [],
     'useDefault': True,
     'allowedTypes': [TupleType, ListType],
     'description': '''A list of allele frequency (not a list of ranges as parameter controlledFreq).
                if there are several populations, allele frequency should be given in the order of
                LOC0: sp0, sp1, sp2, LOC1: sp0, sp1, sp2,...''',
    },
    {'longarg': 'fitness=',
     'default': [1, 1, 1],
     'label': 'Fitness of genotype AA,Aa,aa',
     'useDefault': True,
     'allowedTypes': [ListType, TupleType],
     'description': '''Fitness of genotype, can be:
                f1, f2, f3: if one DSL, the fitness for genotype AA, Aa and aa
                f1, f2, f3: if multiple DSL, the same fitness for each locus
                [a1, a2, a3, b1, b2, b3, ...] if mlSelModel = 'additive'
                    or multiplicative, fitness at each locus. The overall fitness
                    is determined by mlSelModel
                [a1, a2, a3, b1, b2, b3, c1, c2, c3, ...] and mlSelModel = interaction.
                    For example, in the 2-DSL case, the numbers are (by row)
                        BB Bb bb
                    AA  a1 a2 a3
                    Aa  b1 b2 b3
                    aa  c1 c2 c3
                3^n numbers are needed for n DSL.
        ''',
     'validate': valueListOf(valueGE(0.)),
    },
    {'longarg': 'mlSelModel=',
    'default': 'none',
    'useDefault': True,
    'label': 'Multi-locus selection model',
    'description': '''Model of overall fitness value given fitness values for each DSL.
                multiplicative: f =  Prod(f_i)
                additive: f = 1-Sum(1-f_i)
                interaction: the intepretation of fitness parameter is different.
                    see fitness.
                Note that selection will be applied to all generations, but backControlledLoci
                will only have wild-type allele before a mutant is introduced.
                ''',
    'allowedTypes': [StringType],
    'chooseOneOf': ['additive', 'multiplicative', 'interaction', 'none']
    },
    {'longarg': 'backMigrRate=',
     'default': 0.0001,
     'useDefault': True,
     'allowedTypes': [IntType, FloatType],
     'label': 'Background migration rate',
     'description': '''If more than one hapmap populations are chosen, a low-level
                of migration is allowed between these populations. An island model
                will be used and the migration rate refers to the probability of
                migrating to another population at each generation. For example,
                if three populations are involved, the migration matrix will be
                    [1-2r, r, r,
                      r, 1-2r, 2,
                      r, r, 1-2r]
                Note that real migration rate is scaled by parameter --scale, and this background
                migration will stop at the admixture stage where another migrator will take over. 
                '''
    },
    {'longarg': 'scale=',
     'default': 10,
     'useDefault': True,
     'allowedTypes': [IntType, LongType, FloatType],
     'label': 'Acceleration scale',
     'description': '''This parameter is used to speed up recombination, mutation
                and selection. Briefly speaking, certain parts of the evolutionary
                process is accelerated but random genetic drift is kept. Please
                refer to Peng 2008 for more details''',
     'validate': valueGT(0),
    },
    {'separator': 'Population expansion'},
    {'longarg': 'initCopy=',
     'default': 20,
     'useDefault': True,
     'label': 'Initial propagation',
     'description': '''How to expand the initial small HapMap sample to
                 avoid quick loss of heterogenity. By default, each individual
                 is copied 10 times.''',
     'allowedTypes': [IntType, LongType],
     'validate': valueGT(0)
    },
    {'longarg': 'initGen=',
     'default': 20,
     'useDefault': True,
     'label': 'Generations to evolve',
     'description': '''Number of generations to evolve to get the seed
                population. The actual evolved population is scaled down by
                parameter --scale. (If scale==10, initGen=1000, the actually
                evolved generation is 100).''',
     'allowedTypes': [IntType, LongType],
     'validate': valueGT(0)
    },
    {'longarg': 'initSize=',
     'default': 5000,
     'useDefault': True,
     'label': 'Size of the seed population',
     'description': '''Size of the seed population. The default value is the recommended
                value when all hapmap populations are used (60+60+90)*20. You may want
                to reduce it according to the populations used.''',
     'allowedTypes': [IntType, LongType],
     'validate': valueGE(100)
    },
    {'longarg': 'expandGen=',
     'default': 500,
     'useDefault': True,
     'label': 'Generations to expand',
     'description': '''Number of generations to evolve during the population
                expansion stage. The actual evolved population is scaled down by
                parameter --scale. (If scale==10, expandGen=1000, the actually
                evolved generation is 100).''',
     'allowedTypes': [IntType, LongType],
     'validate': valueGT(0)
    },
    {'longarg': 'expandSize=',
     'default': 50000,
     'useDefault': True,
     'label': 'Expanded population size',
     'description': '''Size of the expanded population. The default value if the recommended
                value when all hapmap populations are used (60+60+90)*200. You may want to
                reduce it according to the population used, or increase it if disease
                prevalence if low and insufficient cases are generated.''',
     'allowedTypes': [IntType, LongType],
     'validate': valueGE(100)
    },
    {'longarg': 'expandedName=',
     'default': 'expanded.pop',
     'useDefault': True,
     'description': '''Name of the expanded population, relative to simulation path''',
     'allowedTypes': [StringType],
    },
    #
    {'separator': 'Population admixture'},
    {'longarg': 'admixGen=',
     'default': 0,
     'useDefault': True,
     'label': 'Admix generations',
     'description': '''Length of the admixture stage, If set to zero, the admixture stage
                is ignored''',
     'allowedTypes': [IntType, LongType],
     'validate': valueGE(0),
    },
    {'longarg': 'migrGen=',
     'default': 0,
     'useDefault': True,
     'label': 'Migration generations',
     'description': '''Number of generations with migration. This number should be
                less than or equal to admixGen''',
     'allowedTypes': [IntType, LongType],
     'validate': valueGE(0),
    },
    {'longarg': 'migrRate=',
     'default': [[0.99, 0.01], [0., 1.]],
     'useDefault': True,
     'label': 'Migration rate matrix',
     'description': '''Migration rate matrix. A_ij of this matrix represents the
                probability of moving from population i to j, A_ii is the probability
                of staying in the same population, which is calculated as
                1-sum_(j \\ne i) A_ij. It is possible to create another
                subpopulation in this way, like sending some individuals from both parental
                populations to a new subpopulation.
                ''',
     'allowedTypes': [TupleType, ListType],
     'validate': valueListOf(valueListOf(valueBetween(0,1))),
    },
    {'longarg': 'ancestry',
     'default': True,
     'useDefault': True,
     'allowedTypes': [BooleanType],
     'label': 'Record individual ancestry',
     'description': '''If set, several information fields named after HapMap populations
                will be added to each individual and record the percent of ancestry from
                each population. For example, if a parent has CEU:0.5, YRI:0.5 and another
                parent has CEU:0, YRI:1, their offspring' ancestry values will be CEU:0.25,
                YRI: 0.75.''',
    },
    {'longarg': 'matingScheme=',
     'default': 'random',
     'label': 'Mating scheme during population mixing',
     'useDefault': True,
     'chooseOneOf': ['random', 'assortative', 'customized'],
     'allowedTypes': [StringType],
     'validate': valueOneOf(['random', 'customized']),
     'description': '''Mating scheme used during the population mixing stage. If 'random'
                is chosen, migrants will mate freely with all individuals in the population.
                If 'customized' is chose, an assortative mating scheme will be used in which
                migrants tend to mate within their ethnic group. This serves as an example
                for more complicated mating schemes that can be defined.''',
    },
    {'longarg': 'admixedName=',
     'default': 'admixed.pop',
     'useDefault': True,
     'description': '''Name of the admixed, relative to simulation path''',
     'allowedTypes': [StringType],
    },
]


class Tee(object):
    '''
    A Tee object. Write to this object will write to stdout, and to
    specified file objects.
    '''
    def __init__(self, file):
        self.file = file
        if isinstance(sys.stdout, Tee):
            self.stdout = sys.stdout.stdout
        else:
            self.stdout = sys.stdout
        sys.stdout = self

    def __del__(self):
        self.close()
        
    def close(self):
        if self.file is not None:
            self.file.close()
            self.file = None
        if self.stdout is not None:
            sys.stdout = self.stdout
            self.stdout = None

    def write(self, data):
        self.stdout.write(data)
        self.file.write(data)

    def writelines(self, data):
        for i in seq:
            self.write(i)

    def flush(self):
        self.file.flush()
        self.stdout.flush()


class admixtureParams:
    ''' This class is used to wrap all parameters to a single object so that
    I do not have to pass a bunch of parameters here and there.
    This class also clean up/validate parameters and calcualtes some derived
    parameters for later uses.
    '''
    def __init__(self, name='simu', useSavedExpanded=False, step=100,
            saveStep=0, saveName='expand_',
            HapMap_dir='HapMap', pops=['CEU'], markerList='', chrom=[2],
            numMarkers=[1000], startPos=0, endingPos=0, minAF=0, minDiffAF=0, minDist=0,
            initName='init.pop', mutaRate=5e-7, recMap='genetic', recIntensity=0.01,
            convProb=0, convMode='Tract length', convParam=0.02,
            forCtrlLoci=[], forCtrlFreq=[], backCtrlLoci=[], backCtrlFreq=[],
            fitness=[1,1,1], mlSelModel='none', backMigrRate=0.0001,
            scale=10, initCopy=20, initGen=20, initSize=5000,
            expandGen=500, expandSize=50000, expandedName='expanded.pop',
            admixGen=0, migrGen=0, migrRate=[[0.99, 0.01], [0, 1.]],
            ancestry=True, matingScheme='random', admixedName='admixed.pop'):
        # expand all params to different options
        (self.name, self.useSavedExpanded, self.step, self.saveStep, self.saveName,
            self.HapMap_dir, self.pops, self.markerList, self.chrom, self.numMarkers,
            self.startPos, self.endingPos, self.minAF, self.minDiffAF, self.minDist,
            self.initName, self.mutaRate, self.recMap, self.recIntensity, self.convProb,
            self.convMode, self.convParam, self.forCtrlLoci, self.forCtrlFreq,
            self.backCtrlLoci, self.backCtrlFreq, self.fitness, self.mlSelModel,
            self.backMigrRate, self.scale,
            self.initCopy, self.initGen, self.initSize,
            self.expandGen, self.expandSize, self.expandedName,
            self.admixGen, self.migrGen, self.migrRate,
            self.ancestry, self.matingScheme, self.admixedName) \
        = (name, useSavedExpanded, step, saveStep, saveName,
            HapMap_dir, pops, markerList, chrom, numMarkers, startPos, endingPos,
            minAF, minDiffAF, minDist, initName, mutaRate, recMap,
            recIntensity, convProb, convMode, convParam, forCtrlLoci, forCtrlFreq,
            backCtrlLoci, backCtrlFreq, fitness, mlSelModel, backMigrRate, scale,
            initCopy, initGen, initSize, expandGen, expandSize, expandedName,
            admixGen, migrGen, migrRate, ancestry, matingScheme, admixedName)
        # preparations
        self.createSimulationDir()
        self.initFile = self.setFile(self.initName)
        self.expandedFile = self.setFile(self.expandedName)
        self.admixedFile = self.setFile(self.admixedName)
        #
        self.ctrlLoci = self.forCtrlLoci + self.backCtrlLoci
        # adjust parameters startPos, endPos etc.
        self.prepareMarkerParams()
        # this parameter does not need to be configurable.
        self.ldSampleSize = 200
        # marker list file and ld map file.
        self.trajFile = os.path.join(self.name, 'trajectory.csv')
        self.markerListFile = os.path.join(self.name, 'markers.lst')
        self.markerMapFile = os.path.join(self.name, 'ld.map')
        self.logFile = os.path.join(self.name, self.name + '.log')
        Tee(open(self.logFile, 'w'))
        self.convMode = {
            'Tract length': CONVERT_TractLength,
            'Number of markers': CONVERT_NumMarkers,
            'Geometric distribution': CONVERT_GeometricDistribution,
            'Exponential Distribution': CONVERT_ExponentialDistribution
            }[self.convMode]
        #
        self.prepareFitnessParams()
        #
        if self.migrGen > self.admixGen:
            self.migrGen = self.admixGen
        self.curScale = 1.

    def scaleParam(self, scale):
        if scale != 1:
            self.mutaRate *= scale
            self.recIntensity *= scale
            self.backMigrRate *= scale
            self.step = int(self.step / scale)
            self.saveStep = int(self.saveStep / scale)
            self.initGen = int(self.initGen / scale)
            self.expandGen = int(self.expandGen / scale)
            self.curScale *= scale
            if self.curScale == 1.:
                print "The simulation is not accelerated."
            else:
                print "The simulation will be accelerated by %.1f times." % self.curScale
            if self.initGen == 0:
                raise ValueError('No initial stage. It is possible '
                    'that you scale parameter is larger than initGen')
            if self.expandGen == 0:
                raise ValueError('No expansion stage. It is possible '
                    'that you scale parameter is larger than initGen')


    def createSimulationDir(self):
        '''Create a directory with simulation name'''
        if not os.path.isdir(self.name):
            print 'Creating directory', self.name
            os.makedirs(self.name)
        if not os.path.isdir(self.name):
            raise SystemError('Can not create directory %s, exiting' % self.name)

    def saveConfiguration(self):
        '''Save configuration to $name.cfg'''
        cfgFile = os.path.join(self.name, self.name + '.cfg')
        print 'Save configuration to', cfgFile
        # save current configuration
        saveConfig(options, cfgFile, allParam)

    def setFile(self, filename):
        '''Return $name/filename unless filename is absolute'''
        if os.path.isabs(filename):
            return filename
        else:
            return os.path.join(self.name, filename)

    def setCtrlLociIndex(self, pop):
        '''Translate ctrlLoci to ctrlLociIdx, etc'''
        if len(self.forCtrlLoci) != 0 and len(self.backCtrlLoci) != 0:
            raise ValueError('This script currently only allows one kind of controlled loci' + \
                'Please specify only one of --forCtrlLoci and --backCtrlLoci')
        if len(self.backCtrlLoci) > 0 and len(self.pops) > 1:
            raise ValueError('''This script can only handle backward simulated trajectory in 
                a single hapmap population.''')
        #
        try:
            self.forCtrlLociIdx = pop.lociByNames(self.forCtrlLoci)
            self.backCtrlLociIdx = pop.lociByNames(self.backCtrlLoci)
            self.ctrlLociIdx = pop.lociByNames(self.ctrlLoci)
        except:
            names = pop.lociNames()
            for locus in self.ctrlLoci:
                if not locus in names:
                    raise ValueError('Can not find locus ' + locus + ' in this population. ' +
                        'Please check markers.lst for a list of used markers and their frequency.')
        # this is used for statistical output
        pop.dvars().ctrlLoci = self.ctrlLociIdx

    def expandToList(self, par, size, err=''):
        '''If par is a number, return a list of specified size'''
        if type(par) in [IntType, LongType]:
            return [par]*size
        elif type(par) in [TupleType, ListType] and len(par) == 1:
            return list(par)*size
        elif len(par) != size:
            raise ValueError(err)
        else:
            return par

    def prepareMarkerParams(self):
        '''validate marker parameters'''
        if not os.path.isdir(self.HapMap_dir):
            print 'HapMap directory %s does not exist, creating one.' % self.HapMap_dir
            os.makedirs(self.HapMap_dir)
            if not os.path.isdir(self.HapMap_dir):
                raise ValueError('Can not create directory %s to store hapmap data, exiting' % self.HapMap_dir)
        if len(self.chrom) == 0:
            raise ValueError('Please specify one or more chromosomes')
        # in case that chrom is a tuple
        self.chrom = list(self.chrom)
        numChrom = len(self.chrom)
        self.numMarkers = self.expandToList(self.numMarkers, numChrom,
            'Please specify number of marker for each chromosome')
        self.startPos = self.expandToList(self.startPos, numChrom,
            'Wrong starting positions')
        self.endingPos = self.expandToList(self.endingPos, numChrom,
            'Wrong endinging positions')
        # now, which subpopulations are needed?
        self.popsIdx = []
        for idx,sp in enumerate(HapMap_pops):
            if sp in self.pops:
                print "Using hapmap population %s" % sp
                self.popsIdx.append(idx)
        print "Loading populations ", self.popsIdx

    def prepareFitnessParams(self):
        # parameters for fitness...
        self.mlSelModel = {
            'additive':SEL_Additive,
            'multiplicative':SEL_Multiplicative,
            'interaction': 'interaction',
            'none': None
            }[self.mlSelModel]
        numDSL = len(self.ctrlLoci)
        if numDSL > 1 and self.mlSelModel is None:
            self.fitness = [1, 1, 1]
        elif self.mlSelModel == 'interaction':
            if numDSL == 1:
                raise ValueError("Interaction model can only be used with more than one DSL");
            if len(self.fitness) != 3**numDSL:
                raise ValueError("Please specify 3^n fitness values for n DSL");
        elif len(self.fitness) == 3:
            self.fitness = self.fitness*numDSL
        elif len(self.fitness) != numDSL*3:
            raise ValueError("Please specify fitness for each DSL")
        #
        if len(self.forCtrlFreq) > 0:
            if type(self.forCtrlFreq[0]) in [TupleType, ListType]:
                if len(self.forCtrlFreq) != len(self.forCtrlLoci):
                    raise ValueError('Please specify frequency range for each controlled locus')
                for rng in self.forCtrlFreq:
                    if len(rng) != 2:
                        raise ValueError('Wrong allele frequency range: %s. A list of frequency pairs is expected.' % rng)
            # give only one
            else:
                if len(self.forCtrlFreq) != 2:
                    raise ValueError('Wrong allele frequency range: %s' % self.forCtrlFreq)
                self.forCtrlFreq = [self.forCtrlFreq] * len(self.forCtrlLoci)
        # backward controlled freq
        if len(self.backCtrlFreq) == 1:
            self.backCtrlFreq = self.backCtrlFreq * len(self.backCtrlLoci) * len(self.pops)
        elif len(self.backCtrlFreq) != len(self.backCtrlLoci) * len(self.pops):
            raise ValueError('Number of backward controlled freq does not match the number of '
                'controlled loci multiplied by number of populations')


#####################################################################
# You have realized how many lines of code is used for parameter
# handling and comments. Now, the utility function part...
#####################################################################

# Example of a cutomized mating scheme
def customizedMatingScheme(pop):
    '''
    The population is divided into two virtual subpopulations depending
    on individual ancestry values. Individuals with YRI < 0.5 (native)
    and YRI >= 0.5 (migrants) mate mostly within their own virtual subpopulations.
    Only 20% of the individuals mate randomly with others.
    '''
    pop.setVirtualSplitter(infoSplitter(info='YRI',
        cutoff = [0.5]))
    return heteroMating(
        [randomMating(), # random mating for both subpopulations
         randomMating(subPop=0, virtualSubPop=0, weight=-0.80),
         randomMating(subPop=0, virtualSubPop=1, weight=-0.80)])



######################################################################

def expDemoFunc(N0, N1, N2, gen1, gen2):
    '''
    Return an exponential population expansion demographic function that has
    two stages of expansion.

    N0: a list of initial subpopulation sizes.
    N1: middle population size.
    N2: ending population size.
    
    gen1: generations to evolve in the slow-expansion stage.
    gen2: generations to evolve in the fast-expansion stage.
    '''
    if type(N1) in [IntType, LongType]:
        midSize = [int(N1*1.0*x/sum(N0)) for x in N0]
    elif len(N1) != len(N0):
        raise exceptions.ValueError("Number of subpopulations should be the same")
    else:
        midSize = N1
    if type(N2) in [IntType, LongType]:
        endSize = [int(N2*1.0*x/sum(midSize)) for x in midSize]
    elif len(N2) != len(N0):
        raise exceptions.ValueError("Number of subpopulations should be the same")
    else:
        endSize = N2
    #
    rate1 = [(math.log(midSize[x]) - math.log(N0[x]))/gen1 for x in range(len(N0))]
    rate2 = [(math.log(endSize[x]) - math.log(midSize[x]))/gen2 for x in range(len(N0))]
    def func(gen, oldSize=[]):
        if gen < gen1:
            return [int(N0[x]*math.exp(gen*rate1[x])) for x in range(len(N0))]
        else:
            return [int(midSize[x]*math.exp((gen-gen1)*rate2[x])) for x in range(len(N0))]
    return func


def effPopSize(func, gen):
    '''Estimate effective population size for a given demographic function'''
    nSP = len(func(0))
    Ne = [0]*nSP
    for i in range(gen):
        for j in range(nSP):
            Ne[j] += 1./func(i)[j]
    return [gen/x for x in Ne]


def writeMarkerInfo(pop, par):
    'Save marker info'
    # print marker list fine
    Stat(pop, alleleFreq=range(0, pop.totNumLoci()))
    # write marker information
    print 'Writing a marker list file'
    markers = open(par.markerListFile, 'w')
    print >> markers, 'Name\tchrom\tlocation\t%s\tfreq(allele1)' % \
        ('\t'.join([x + '_freq(allele1)' for x in par.pops]))
    for ch in range(pop.numChrom()):
        for loc in range(pop.chromBegin(ch), pop.chromEnd(ch)):
            print >> markers, '%s\t%d\t%.6f\t%s\t%.3f' % (pop.locusName(loc),
                par.chrom[ch], pop.locusPos(loc),
                '\t'.join(['%.3f' % pop.dvars(x).alleleFreq[loc][1] for x in range(pop.numSubPop())]),
                pop.dvars().alleleFreq[loc][1])
    markers.close()


def writeTrajectory(popFunc, trajFunc, gen, file):
    'Save trajectory to a file'
    sz = popFunc(0)
    t = trajFunc(0)
    numSP = len(sz)
    numLoci = len(t) / len(sz)
    file = open(file, 'w')
    print >> file, 'gen, %s, %s' % (', '.join(['sp_%d' % x for x in range(numSP)]),
        ' ,'.join(['traj_loc%d_sp%d' % (x, y) for x in range(numSP) for y in range(numLoci)]))
    for g in range(gen):
        print >> file, '%d, %s, %s' % (g, ', '.join([str(x) for x in popFunc(g)]),
            ', '.join(['%.4f' % x for x in trajFunc(g)]))
    file.close()


def writeMapFile(pop, par):
    '''Write a marker map file that can be used by haploview'''
    # write a map file, used by haploview
    print 'Writing a map file ld.map to be used by haploview'
    file = open(par.markerMapFile, 'w')
    for loc in range(pop.totNumLoci()):
        print >> file, pop.locusName(loc), int(pop.locusPos(loc)*1000000)
    file.close()


def getOperators(pop, par, progress=False, savePop=False, vsp=False, mutation=False,
        migration=False, recombination=False, selection=False):
    '''Return mutation and recombination operators'''
    ops = []
    if progress:
        # statistics calculation and display
        exp = ['gen %3d', 'size=%s']
        preGen = 'gen*scale'
        postGen = '(gen+1)*scale-1'
        var = ['%s', 'subPopSize']
        if len(par.ctrlLoci) > 0:
            exp.append('alleleFreq=%s')
            var.append('", ".join(["%%.3f" %% alleleFreq[x][1] for x in ctrlLoci])')
        if len(par.pops) > 1:
            exp.append('Fst=%.3f')
            var.append('AvgFst')
        if vsp:
            exp.append('VSP=%s')
            var.append('virtualPopSize')
        if pop.dvars().stage == 'expand':
            keyGens = [par.initGen - 1, -1]
        elif pop.dvars().stage == 'mix':
            keyGens = [par.migrGen - 1, -1]
        ops.extend([
            stat(popSize = True, alleleFreq = par.ctrlLociIdx, Fst = range(pop.totNumLoci()),
                step = par.step, stage=PreMating),
            pyEval(r'"At the beginning of %s\n" %% (%s)' % (', '.join(exp), ', '.join(var) % preGen),
                step=par.step, stage=PreMating),
            stat(popSize = True, alleleFreq = par.ctrlLociIdx, Fst = range(pop.totNumLoci()),
                at = keyGens),
            pyEval(r'"At the end of %s\n" %% (%s)' % (', '.join(exp), ', '.join(var) % postGen),
                at = keyGens)
        ])
    if savePop and par.saveStep > 0:
        ops.extend([
            pyEval(r"'Saving current generation to %s%%d.pop\n' %% (gen*scale)" % par.saveName,
                step=par.saveStep, stage=PreMating),
            savePopulation(outputExpr="'%s/%s%%d.pop' %% (gen*scale)" % (par.name, par.saveName),
                step=par.saveStep, stage=PreMating),
        ])
    if mutation:
        ops.append(kamMutator(rate=par.mutaRate, loci=range(pop.totNumLoci())))
    if migration and len(par.pops) > 1:
        ops.append(migrator(MigrIslandRates(par.backMigrRate, len(par.pops))))
    if recombination:
        if par.recMap == 'physical':
            ops.append(recombinator(intensity=par.recIntensity, convProb=par.convProb,
                convMode=par.convMode, convParam=par.convParam))
            print 'Scaled recombination at %.3f cM/Mb over %.2f Mb physical distance (first chromosome)' % \
                (par.recIntensity * 100, pop.lociDist(0, pop.numLoci(0)-1))
        else: # use map distance
            try:
                pos = [pop.dvars().genDist[pop.locusName(x)] for x in range(pop.totNumLoci())]
            except Exception,e:
                print e
                print 'Invalid or incomplete population variable genDist'
                print 'Please run loadHapMap again to set up genetic distance'
            loc = []
            rate = []
            for ch in range(pop.numChrom()):
                beg = pop.chromBegin(ch)
                end = pop.chromEnd(ch)
                loc.extend(range(beg, end - 1))
                rate.extend([(pos[x+1] - pos[x])*par.recIntensity for x in range(beg, end - 1)])
            print 'Scaled recombination at %.3f cM/Mb over %.2f centiMorgan genetic (%.2f Mb physical) distance (first chromosome)' % \
                (par.recIntensity*100, (pop.dvars().genDist[pop.locusName(pop.numLoci(0)-1)] - \
                    pop.dvars().genDist[pop.locusName(0)]), pop.lociDist(0, pop.numLoci(0)-1))
            # recombination rate at the end of each chromosome will be invalid
            # but this does not matter
            ops.append(recombinator(rate=rate, loci = loc,
                convProb=par.convProb, convMode=par.convMode, convParam=par.convParam))
    if selection:
        if par.mlSelModel in [SEL_Additive, SEL_Multiplicative]:
            ops.append(mlSelector(
                # with five multiple-allele selector as parameter
                [ maSelector(locus=par.ctrlLociIdx[x], wildtype=[0],
                    fitness=[par.fitness[3*x], par.fitness[3*x+1], par.fitness[3*x+2]]) \
                        for x in range(len(par.ctrlLociIdx)) ],
                mode=par.mlSelModel))
        elif par.mlSelModel == 'interaction':
            # multi-allele selector can handle multiple DSL case
            ops.append(maSelector(loci=par.ctrlLociIdx, fitness=par.fitness, wildtype=[0]))
    return ops



#####################################################################
# Finally, the real actions.
#####################################################################

def createInitialPopulation(par):
    '''Create an initial population, with parameters (from the par structure)
    HapMap_dir:     directory that stores hapmap data.
    chrom:          chromosomes to use
    markerList:     list of markers to use
    numMarkers:     number of markers per chromosome
    startPos:       starting position on each chromosome
    endPos:         ending position on each chromosome
    minAF:          minimal allele frequency
    minDiffAF:      minimal allele frequency differences among HapMap populations
    minDist:        minimal distance between adjecent markers
    pops:           hapmap populations to use
    '''
    # load markers!
    for ch in par.chrom:
        if not os.path.isfile(os.path.join(par.HapMap_dir, 'hapmap_%d.pop' % ch)):
            try:
                import loadHapMap
                loadHapMap.loadHapMap([ch], par.HapMap_dir)
            except Exception, e:
                print e
            if not os.path.isfile(os.path.join(par.HapMap_dir, 'hapmap_%d.pop' % ch)):
                raise ValueError('''Failed to load or download hapmap data for chromosome %d
                    Please copy script loadHapMap.py to the current directory, or add
                    path to this script to environmental variable$PYTHONPATH,
                    or run this script manually to download, import, and save HapMap
                    data in simuPOP format''' % ch)
    useHapMapMarker = par.markerList == ''
    ch_pops = []
    if useHapMapMarker:
        genDist = {}
        for ch, sp, ep, nm in zip(par.chrom, par.startPos, par.endingPos, par.numMarkers):
            ch_pops.append(getMarkersFromRange(par.HapMap_dir, par.popsIdx,
                ch, sp, ep, nm, par.minAF, par.minDiffAF, par.minDist))
            genDist.update(ch_pops[-1].dvars().genDist)
        # merge all populations (different chromosomes)
        if len(ch_pops) > 1:
            pop = MergePopulationsByLoci(ch_pops)
            pop.dvars().genDist = genDist
        else:
            pop = ch_pops[0].clone()
    else:
        # read the list
        print 'Reading marker list %s' % par.markerList
        mlist = open(par.markerList)
        names = {}
        lastpos = [0]*len(par.chrom)
        for line in mlist.readlines():
            if line.startswith('#') or line.strip() == '':
                continue
            try:
                fields = line.split()
                ch = int(float(fields[0]))
                pos = float(fields[1])/1000000.
                name = fields[2]
            except:
                print "Ignoring line '%s'" % line
                continue
            if ch not in par.chrom:
                continue
            chIdx = par.chrom.index(ch)
            if pos < par.startPos[chIdx]:
                continue
            if par.endingPos[chIdx] != 0 and pos > par.endingPos:
                continue
            if par.minDist > 0 and pos - par.lastpos[chIdx] < par.minDist:
                continue
            if not names.has_key(ch):
                names[ch] = []
            names[ch].append(name)
            lastpos[chIdx] = pos
        pop = getMarkersFromName(par.HapMap_dir, names,
            chroms=par.chrom, hapmap_pops=par.popsIdx,
            minDiffAF=par.minDiffAF, numMarkers=par.numMarkers)
    # if this population fine?
    if pop.numChrom() != len(par.chrom):
        raise ValueError('Something wrong. The population does not have enough chromosomes')
    # We do not hapmap does not have sex information. To evolve the population naturally
    # we set random sex to all individuals.
    InitSex(pop)
    # write marker and map file
    writeMarkerInfo(pop, par)
    writeMapFile(pop, par)
    #
    par.setCtrlLociIndex(pop)
    # write a LD plot.
    pop.dvars().stage = 'hapmap'
    print 'Saving initial population to ', par.initFile
    pop.savePopulation(par.initFile)
    return pop


def freeExpand(pop, par):
    '''Expand an initial population freely'''
    #
    popSizeFunc = expDemoFunc(pop.subPopSizes(), par.initSize, par.expandSize, 
        par.initGen, par.expandGen)
    print 'Estimated effective population size is', effPopSize(popSizeFunc, par.initGen + par.expandGen)
    #
    # evolve it. This is the simplest case.
    print "Evolving the population freely..."
    simu = simulator(pop, randomMating(newSubPopSizeFunc = popSizeFunc))
    simu.evolve(
        ops = getOperators(pop, par,
            progress=True, savePop=True, selection=True,
            mutation=True, migration=True, recombination=True),
        gen = par.initGen + par.expandGen)
    return simu.extract(0)


def forCtrlExpand(pop, par):
    '''Expand a population using forward controlled loci'''
    # simulate a frequency trajectory
    Stat(pop, alleleFreq=par.ctrlLociIdx)
    currentFreq = []
    # in the order: LOC0: sp0, sp1, sp2, LOC1: sp0, sp1, sp2, ...
    for idx,loc in enumerate(par.ctrlLociIdx):
        print "Current overall frequency of allele 1 at %s: %.3f (aiming at: %.3f ~ %.3f)" % \
            (pop.locusName(loc), pop.dvars().alleleFreq[loc][1],
            par.forCtrlFreq[idx][0], par.forCtrlFreq[idx][1])
        for sp in range(pop.numSubPop()):
            currentFreq.append(pop.dvars(sp).alleleFreq[loc][1])
    print 'Simulating frequency trajectory ...'
    popSizeFunc = expDemoFunc(pop.subPopSizes(), par.initSize, par.expandSize, 
        par.initGen, par.expandGen)
    print 'Estimated effective population size is', effPopSize(popSizeFunc, par.initGen + par.expandGen)
    #
    traj = ForwardFreqTrajectory(
        curGen = 0,
        endGen = par.initGen + par.expandGen,
        curFreq = currentFreq,
        freq = par.forCtrlFreq,
        fitness = par.fitness,
        migrRate = par.backMigrRate,
        NtFunc = popSizeFunc,
        maxAttempts = 10000
    )
    if len(traj) == 0:
        raise SystemError('Failed to generated trajectory after 10000 attempts. '
            'This usually means that the demographic and genetic settings are '
            'very extreme which makes it very likely for an allele to reach designed'
            'allele frequency. Please adjust your parameters and try again.')
    # define a trajectory function
    def trajFunc(gen):
        return [x[gen] for x in traj]
    #for i in range(par.initGen + par.expandGen + 1):
    #    print trajFunc(i)
    # record trajectory
    print 'Writing allele frequency trajectories to %s' % par.trajFile
    writeTrajectory(popSizeFunc, trajFunc, par.initGen + par.expandGen,
        par.trajFile)
    #
    print "Using controlled random mating on markers %s" % (', '.join(par.ctrlLoci))
    pop.addInfoField('fitness')
    simu = simulator(pop,
        controlledRandomMating(
            loci = par.ctrlLociIdx,
            alleles = [1]*len(par.ctrlLoci),
            freqFunc = trajFunc,
            newSubPopSizeFunc = popSizeFunc)
    )
    simu.evolve(
        ops = getOperators(pop, par,
            progress=True, selection=True,
            mutation=True, migration=True, recombination=True),
        gen = par.initGen + par.expandGen
    )
    pop = simu.extract(0)
    Stat(pop, alleleFreq=par.ctrlLociIdx)
    for i,loc in enumerate(par.ctrlLociIdx):
        print "Locus %s: designed freq: (%.3f, %.3f), simulated freq: %.3f" % \
            (pop.locusName(loc), par.forCtrlFreq[i][0],
            par.forCtrlFreq[i][1], pop.dvars().alleleFreq[loc][1])
    return pop


def backCtrlExpand(pop, par):
    '''Expand seed population using backward controlled loci'''
    # clear these loci
    print 'Clearing mutants at backward-controlled loci'
    for idx,loc in enumerate(par.backCtrlLociIdx):
        for ind in pop.individuals():
            ind.setAllele(0, loc, 0)
            ind.setAllele(0, loc, 1)
    print 'Simulate allele frequency trajectory using a backward approach'
    # NOTE:
    popSizeFunc = expDemoFunc(pop.subPopSizes(), par.initSize, par.expandSize, 
        par.initGen, par.expandGen)
    print 'Estimated effective population size is', effPopSize(popSizeFunc, par.initGen + par.expandGen)
    allTraj = []
    introOps = []
    for sp in range(len(par.pops)):
        def spSizeFunc(gen, sz=[]):
            return [popSizeFunc(gen, sz)[sp]]
        spFreq = [par.backCtrlFreq[x*len(par.pops) + sp] for x in range(len(par.backCtrlLoci))]
        traj = FreqTrajectoryMultiStoch(
            curGen = par.initGen + par.expandGen,
            freq = spFreq,
            NtFunc = spSizeFunc,
            fitness = par.fitness,
            minMutAge = 0,
            maxMutAge = par.expandGen,
            restartIfFail = True)
        if len(traj) == 0:
            raise ValueError('''Failed to simulate trajectory for subpopulation %d
                Initial allele frequency: %s
                Ending allele frequency: %s''' % (sp, currentFreq, par.backCtrlFreq))
        allTraj.append(traj)
        # how to introduce mutants to this subpopulation?
        for idx,loc in enumerate(par.backCtrlLoci):
            genIntro = par.expandGen - len(traj[i]) + 1
            indIntro = sum(popSizeFunc(g)[:sp]) # mutate the first individual at that subpopulation
            introOps.append(pointMutator(locus=loc, toAllele=1, inds=[indIntro],
                at = [genIntro], stage=PreMating))
    # define a trajectory function
    def trajFunc(gen):
        freq = []
        for i in range(len(par.backCtrlLoci)):
            for spTraj in traj: # spTraj is an array for each subpopulation
                t = spTraj[i]
                if gen < par.initGen + par.expandGen - len(t) + 1:
                    freq.append(0)
                else:
                    freq.append(t[gen - par.initGen - par.expandGen + len(t) - 1])
        return freq
    # record trajectory
    print 'Writing allele frequency trajectories to %s' % par.trajFile
    writeTrajectory(popSizeFunc, trajFunc, par.initGen + par.expandGen,
        par.trajFile)
    #
    print 'Start population expansion using a controlled random mating scheme'
    pop.addInfoField('fitness')
    simu = simulator(pop,
        controlledRandomMating(
            loci = par.backCtrlLociIdx,
            alleles = [1]*len(par.backCtrlLoci),
            freqFunc = trajFunc,
            newSubPopSizeFunc = popSizeFunc)
    )
    simu.evolve(
        ops = getOperators(pop, par,
            progress=True, selection=True,
            mutation=True, migration=True, recombination=True)
            + introOps,
        gen = par.initGen + par.expandGen
    )
    pop = simu.extract(0)
    Stat(pop, alleleFreq = par.backCtrlLociIdx)
    for i,loc in enumerate(par.backCtrlLociIdx):
        print "Locus %s: designed freq: %.3f, freq: %.3f" % \
            (pop.alleleName(loc), par.backCtrlFreq[i], pop.dvars().alleleFreq[loc][1])
    return pop


def mixExpandedPopulation(pop, par):
    ''' Evolve the seed population
    '''
    par.setCtrlLociIndex(pop)
    # migration part.
    print 'Migrate %d generations using migration rate %s' % (par.migrGen, par.migrRate)
    migr = migrator(rate=par.migrRate, mode=MigrByProbability,
        end=par.migrGen)
    #
    ancOps = noneOp()
    if par.ancestry and len(par.pops) > 1:
        def calcAncestry(parAncestry):
            '''parAncestry will be ancestry values of parents
            e.g. CEU_dad, YRI_dad, CEU_mom, YRI_mom
            This function is supposed to return offspring
            ancestry values'''
            sz = len(par.pops)
            if len(parAncestry) != 2*sz:
                raise ValueError('Invalid ancestry array passed')
            return [(parAncestry[x] + parAncestry[x+sz])/2. for x in range(sz)]
        #
        pop.addInfoFields(par.pops, 0)
        # initialize these fields
        for i,sp in enumerate(par.pops):
            # i: subpopulation index
            # sp: field name
            val = []
            for j in range(len(par.pops)):
                if i == j:
                    # initialize as 1
                    val.extend([1]*pop.subPopSize(j))
                else:
                    # initialize as 0
                    val.extend([0]*pop.subPopSize(j))
            pop.setIndInfo(val, sp)
        ancOps = pyTagger(func=calcAncestry, infoFields=par.pops)
    #
    if par.matingScheme == 'random':
        simu = simulator(pop, randomMating())
    else:
        print 'Using a customized mating scheme'
        simu = simulator(pop, customizedMatingScheme(pop))
    simu.evolve(
        ops = getOperators(pop, par, vsp = par.matingScheme != 'random',
            progress=True, selection=True,
            mutation=True, migration=False, recombination=True)
            + [migr, ancOps],
        gen = par.admixGen
    )
    pop = simu.extract(0)
    # save this population
    print "Calculating allele frequency..."
    pop.vars().clear()
    Stat(pop, alleleFreq=range(pop.totNumLoci()))
    return pop


def simuAdmixture(par):
    '''The main program'''
    # accerate
    par.scaleParam(par.scale)
    # if both files exists, skip this stage
    if par.useSavedExpanded and os.path.isfile(par.expandedFile):
        print 'Loading expanded population from file ', par.expandedFile
        expandedPop = LoadPopulation(par.expandedFile)
        if expandedPop.numSubPop() != len(par.pops):
            raise ValueError("Seed population has different number of subpopulation than required.")
    else:
        pop = createInitialPopulation(par)
        # used to generate plots
        pop.dvars().scale = par.curScale
        pop.dvars().stage = 'expand'
        #
        newSize = [x*par.initCopy for x in pop.subPopSizes()]
        print 'Propagating population to size %s' % newSize
        pop.resize(newSize, propagate=True)
        #
        if len(par.ctrlLoci) == 0:
            # freely expand
            expandedPop = freeExpand(pop, par)
        elif len(par.forCtrlLoci) != 0:
            # forward controlled expansion
            expandedPop = forCtrlExpand(pop, par)
        else:
            # backward controlled expansion
            expandedPop = backCtrlExpand(pop, par)
        # save expanded population
        print 'Saving expanded population to %s...' % par.expandedFile
        expandedPop.savePopulation(par.expandedFile)
    #
    # admixture, not accerlation
    par.scaleParam(1./par.scale)
    par.step = 1
    expandedPop.dvars().scale = 1
    expandedPop.dvars().stage = 'mix'
    if par.admixGen <= 0 or len(par.pops) == 1:
        print 'No migration stage'
        return
    admixedPop = mixExpandedPopulation(expandedPop, par)
    print 'Saving admixed population to ', par.admixedFile
    admixedPop.savePopulation(par.admixedFile)


short_desc = '''This program simulates an admixed population based on
two or more HapMap populations. Please follow the intructions
of the help message to prepare HapMap population.'''

# determine which script to run.
if __name__ == '__main__':
    #
    # PARAMETER HANDLING
    #
    # get all parameters
    allParam = getParam(options, short_desc, __doc__, nCol=2)
    # when user click cancel ...
    if len(allParam) == 0:
       sys.exit(1)
    # -h or --help
    if allParam[0]:
        print usage(options, __doc__)
        sys.exit(0)
    cfgFile = allParam[1] + '.cfg'
    print 'Save configuration to', cfgFile
    # save current configuration
    saveConfig(options, cfgFile, allParam)
    # create a parameter class and run simuAdmixture
    simuAdmixture(admixtureParams(*allParam[1:]))
