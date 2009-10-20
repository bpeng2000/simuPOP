////////////////////////// INCLUDE FILES //////////////////////////
%{

#include "../config.h"
#include "simupop_cfg.h"
#include "individual.h"
#include "population.h"
#include "operator.h"
#include "simulator.h"

#include "utility.h"
#include "initializer.h"
#include "outputer.h"
#include "terminator.h"
#include "mating.h"
#include "tagger.h"
#include "stator.h"
#include "migrator.h"
#include "mutator.h"
#include "recombinator.h"
#include "selector.h"

%}


////////////////////////// DEFINE CARRAY //////////////////////////
%{
  extern "C"
  {
#include "arraymodule.c"
  }
%}


////////////////////////// CLEAN EXTRA SYMBOLS //////////////////////////

// do not load these constants in ../config.h
%ignore HAVE_DECL_ACOSH;
%ignore HAVE_DECL_ATANH;
%ignore HAVE_DECL_EXPM1;
%ignore HAVE_DECL_FINITE;
%ignore HAVE_DECL_FREXP;
%ignore HAVE_DECL_HYPOT;
%ignore HAVE_DECL_ISFINITE;
%ignore HAVE_DECL_ISINF;
%ignore HAVE_DECL_ISNAN;
%ignore HAVE_DECL_LDEXP;
%ignore HAVE_DEV_NULL;
%ignore HAVE_DLFCN_H;
%ignore HAVE_FLOAT_H;
%ignore HAVE_INTTYPES_H;
%ignore HAVE_ISWPRINT;
%ignore HAVE_LIMITS_H;
%ignore HAVE_MALLOC;
%ignore HAVE_MEMORY_H;
%ignore HAVE_MEMSET;
%ignore HAVE_PTRDIFF_T;
%ignore HAVE_SNPRINTF;
%ignore HAVE_STDBOOL_H;
%ignore HAVE_STDDEF_H;
%ignore HAVE_STDINT_H;
%ignore HAVE_STDLIB_H;
%ignore HAVE_STRINGS_H;
%ignore HAVE_STRING_H;
%ignore HAVE_STRTOUL;
%ignore HAVE_SYS_STAT_H;
%ignore HAVE_SYS_TYPES_H;
%ignore HAVE_UNISTD_H;
%ignore HAVE_BOOL;
%ignore PACKAGE_NAME;
%ignore PACKAGE_STRING;
%ignore PACKAGE_TARNAME;
%ignore PACKAGE_VERSION;
%ignore PACKAGE_BUGREPORT;
%ignore STDC_HEADERS;
%ignore GSL_RANGE_CHECK;


%ignore DBG_CODE_LENGTH;
%ignore SIMUPOP_VAR_NAME;
%ignore SIMUPOP_VER;
%ignore PopSWIGType;

////////////////////////// VECTOR/MATRIX TYPES //////////////////////////

%include "std_vector.i"
%include "std_string.i"

// stl.i for std::pair
%include "stl.i"
%include "std_map.i"

%include "../config.h"
%include "simupop_cfg.h"

// vectors. Since we are not using them
// in python, the names are ignored.

namespace std
{
  // used in invidiaul.h
  %template()      pair<UINT, UINT>;
  // used in populaiton.h
  %template()      pair<UINT, ULONG>;

  %template(vectora)     vector<Allele>;

#ifdef LONGALLELE
#define vectoru vectora
#else
  %template(vectoru)     vector<UINT>;
#endif

  %template()     vector<int>;
  %template()     vector<LONG>;
  %template()     vector<ULONG>;
  %template()     vector<double>;
  %template()     vector<string>;

  %template()     pair<string, double>;
  %template()     map<string, double>;

  %template()     pair<float, float>;
  %template()     vector<pair<float, float> >;

  %template()     vector< vector<int> >;
  %template()     vector< vector<double> >;
}


////////////////////////// SWIG_INIT FUNCTION //////////////////////////
%init
%{
  simuPOP::initialize();
%}


////////////////////////// C++=>PYTHON EXCEPTIONS //////////////////////////

%include exception.i

%exception
{
  try
  {
    $function
  }
  catch(simuPOP::OutOfMemory e)
  {
    SWIG_exception(SWIG_MemoryError, e.message());
  }
  catch(simuPOP::IOError e)
  {
    SWIG_exception(SWIG_IOError, e.message());
  }
  catch(simuPOP::IndexError e)
  {
    SWIG_exception(SWIG_IndexError, e.message());
  }
  catch(simuPOP::TypeError e)
  {
    SWIG_exception(SWIG_TypeError, e.message());
  }
  catch(simuPOP::ValueError e)
  {
    SWIG_exception(SWIG_ValueError, e.message());
  }
  catch(simuPOP::SystemError e)
  {
    SWIG_exception(SWIG_SystemError, e.message());
  }
  catch(...)
  {
    SWIG_exception(SWIG_RuntimeError, "Unknown runtime error happened.");
  }
}


////////////////////////// SIMUPOP TYPES //////////////////////////

%ignore std::operator<<(ostream&, const strDict&);
%ignore std::operator<<(ostream&, const intDict&);

%ignore simuPOP::GappedAlleleIterator;

// the following load a docstring file extracted from doxgen output.
// there will also be a bunch of %ignore directives as well
//
%include "simuPOP_doc.i";

%include "utility.h"
%include "individual.h"
%include "population.h"


%include "operator.h"

%newobject simuPOP::Population::newPopByIndInfo;
%newobject simuPOP::Population::newPopWithPartialLoci;
%newobject simuPOP::Population::clone;
%newobject simuPOP::Simulator::getPopulation;

namespace simuPOP
{  
  %template(individual)         Individual< std::pair<float,float> > ;
  //%template(indTagInt)        Individual<int>;
  //%template(indWithAgeTagInt) IndividualWithAge<int>;
  //%template(indTagPair)       Individual<std::pair<int,int> >;
  %template(population)         Population<individual>;
  %template(baseOperator)       Operator< pop >;
}

%inline
%{
  typedef simuPOP::Individual< std::pair<float,float> > individual;
  typedef simuPOP::Population< individual > pop;
%}

%{
  // this piece can not be processed by SWIG so can not
  // be inlined. 
#ifndef _NO_SERIALIZATION_
  // version 0: 
  BOOST_CLASS_VERSION(individual, 0)
  BOOST_CLASS_VERSION(pop, 0)
#endif
%}

namespace std
{
  %template(vectorop)   vector< simuPOP::Operator<pop> * >;
}

////////////////////////// SIMUPOP CLASSES //////////////////////////

%include "mating.h"
%include "simulator.h"
%include "stator.h"
%include "outputer.h"
%include "initializer.h"
%include "terminator.h"
%include "tagger.h"
%include "migrator.h"
%include "mutator.h"
%include "recombinator.h"
%include "selector.h"


namespace simuPOP
{
  // since operator is a keyword for swig, I have to use another name
  %template(noneOp)              NoneOp< pop >;
  %template(ifElse)              IfElse< pop >;
  %template(pause)               Pause< pop >;
  %template(ticToc)              TicToc< pop >;
  %template(setAncestralDepth)   SetAncestralDepth< pop >;
  %template(turnOnDebug)         TurnOnDebugOp< pop >;
  %template(turnOffDebug)        TurnOffDebugOp< pop >;

  // mating scheme and simulator
  %template(mating)              Mating< pop >;
  %template(noMating)            NoMating< pop >;
  %template(binomialSelection)   BinomialSelection< pop >;
  %template(randomMating)        RandomMating< pop >;
  %template(pyMating)            PyMating<pop>;

  %template(simulator)           Simulator< pop >;

  // operators

  %template(outputer)            Outputer< pop >;
  %template(output)              OutputHelper< pop >;
  %template(dumper)              Dumper< pop >;
  %template(savePopulation)      SavePopulation<pop>;

  %template(initializer)         Initializer< pop >;
  %template(initByFreq)          InitByFreq< pop >;
  %template(initByValue)         InitByValue< pop >;
  %template(spread)              Spread< pop >;
  %template(pyInit)              PyInit< pop >;

  %template(terminator)          Terminator< pop>;
  %template(terminateIf)         TerminateIf< pop>;

  %template(stator)              Stator<pop>;
  %template(pyEval)              PyEval<pop>;
  %template(pyExec)              PyExec<pop>;
  %template(stat)                BasicStat<pop>;

  %template(tagger)              Tagger<pop>;
  %template(inheritTagger)       InheritTagger<pop>;
  %template(parentsTagger)       ParentsTagger<pop>;

  %template(migrator)            Migrator<pop>;
  %template(pyMigrator)          PyMigrator<pop>;
  %template(splitSubPop)         SplitSubPop<pop>;
  %template(mergeSubPops)        MergeSubPops<pop>;

  %template(mutator)             Mutator<pop>;
  %template(kamMutator)          KAMMutator<pop>;
  %template(smmMutator)          SMMMutator<pop>;
  %template(gsmMutator)          GSMMutator<pop>;
  %template(pyMutator)           PyMutator<pop>;
  %template(pointMutator)        PointMutator<pop>;

  %template(recombinator)        Recombinator<pop>;

  %template(selector)            Selector<pop>;
  %template(basicSelector)       BasicSelector<pop>;
  %template(maSelector)          MASelector<pop>;
  %template(mlSelector)          MLSelector<pop>;
  %template(pySelector)          PySelector<pop>;

  %template(penetrance)          Penetrance<pop>;
  %template(basicPenetrance)     BasicPenetrance<pop>;
  %template(maPenetrance)        MAPenetrance<pop>;
  %template(mlPenetrance)        MLPenetrance<pop>;
  %template(pyPenetrance)        PyPenetrance<pop>;

  %template(quanTrait)           QuanTrait<pop>;
  %template(basicQuanTrait)      BasicQuanTrait<pop>;
  %template(maQuanTrait)         MAQuanTrait<pop>;
  %template(mlQuanTrait)         MLQuanTrait<pop>;
  %template(pyQuanTrait)         PyQuanTrait<pop>;

  %template(pySubset)            PySubset<pop>;
  %template(sample)              Sample<pop>;
  %template(randomSample)        RandomSample<pop>;
  %template(caseControlSample)   CaseControlSample<pop>;
  %template(affectedSibpairSample) AffectedSibpairSample<pop>;
  %template(pySample)            PySample<pop>;

}

////////////////////////// SWIG C++ UTILITY FUNCTIONS //////////////////////////

%{
  extern "C"
    PyObject* pointer2pyObj(void * p, char * name)
  {
    swig_type_info *type = SWIG_TypeQuery(name);
    if (type)
    {
      return SWIG_NewPointerObj(p, type, 0);
    }
    else
    {
      return NULL;
    }
  }

  extern "C"
    PyObject* getModuleDict()
  {
    // get simuPOP module (+1, remove _ before Module name
    PyObject* mm = PyImport_AddModule(const_cast<char*>(SWIG_name)+1);
    if(mm == NULL)
      return NULL;
    else
      return PyModule_GetDict(mm);
  }

  extern "C"
    PyObject* getMainDict()
  {
    PyObject* mm = PyImport_AddModule("__main__");
    if(mm == NULL)
      return NULL;
    else
      return PyModule_GetDict(mm);
  }
%}

////////////////////////// SIMUPOP C++ UTILITY FUNCTIONS //////////////////////////

%newobject LoadPopulation;
%newobject LoadSimulator;

%inline
%{
  pop& LoadPopulation(const string& file,
    const string& format="auto")
  {
#ifndef _NO_SERIALIZATION_
    pop *p = new pop(1);
    p->loadPopulation(file, format);
    return *p;
#else
    cout << "This feature is not supported in this platform" << endl;
    return *new pop(1);
#endif
  }

  simuPOP::Simulator<pop>& LoadSimulator(const string& file,
    simuPOP::Mating<pop>& mate,
    string format="auto")
  {
    pop p;
    simuPOP::Simulator<pop> * a = new simuPOP::Simulator<pop>(
      p, mate );
#ifndef _NO_SERIALIZATION_
    a->loadSimulator(file, format);
    return *a;
#else
    cout << "This feature is not supported in this platform" << endl;
#endif
    return *a;
  }
%}


////////////////////////// SIMUPOP PYTHON UTILITY FUNCTIONS //////////////////////////

%pythoncode %{
import exceptions, types

class dw(object):
  def __init__(self, var):
    try:
      self.__dict__ = var
    except exceptions.TypeError:
      raise exceptions.TypeError("The returned value is not a dictionary.\nNote: simu.vars() is a list so simu.dvars() is not allowed. \n  Use simu.dvars(rep) for population namespace.")
  def clear(self):
    self.__dict__.clear()
  def __repr__(self):
    return str(self.__dict__)

def dvars(self, *args, **kwargs):
  return dw(self.vars(*args, **kwargs))

population.dvars = dvars
simulator.dvars = dvars

def LoadSimulatorFromFiles( files, mating):
  simu = simulator(population(1), mating, rep=len(files))
  # now, replace simu.population with pops
  for i in range(0, len(files)):
    pop = LoadPopulation(files[i])
    simu.setPopulation(pop, i)
  return simu

def LoadSimulatorFromPops( pops, mating):
  simu = simulator(population(1), mating, rep=len(pops))
  # now, replace simu.population with pops
  for i in range(0, len(pops)):
    simu.setPopulation(pops[i], i)
  return simu

def SavePopulations(pops, file, format='auto'):
  simu = simulator(population(1), noMating(), rep=len(pops))
  for i in range(0, len(pops)):
    simu.setPopulation(pops[i], i)
  simu.saveSimulator(file, format)

def LoadPopulations(file, format='auto'):
  simu = LoadSimulator(file, noMating(), format);
  pops = []
  for i in range(0, simu.numRep()):
    pops.append( simu.getPopulation(i))
  return pops


carray = cppModule.carray

#### /////////////////// FUNCTION COUNTERPART OF OPERATORS ////////////////////////////


#
# functions to corresponding operators
def Dump(pop, *args, **kwargs):
  dumper(*args, **kwargs).apply(pop)

Dump.__doc__ = "Function version of operator dump whose __init__ function is \n" + dumper.__init__.__doc__

def InitByFreq(pop, *args, **kwargs):
  initByFreq(*args, **kwargs).apply(pop)

InitByFreq.__doc__ = "Function version of operator initByFreq whose __init__ function is \n" + initByFreq.__init__.__doc__

def InitByValue(pop, *args, **kwargs):
  initByValue(*args, **kwargs).apply(pop)

InitByValue.__doc__ = "Function version of operator initByValue whose __init__ function is \n" + initByValue.__init__.__doc__

def PyInit(pop, *args, **kwargs):
  pyInit(*args, **kwargs).apply(pop)
  
PyInit.__doc__ = "Function version of operator pyInit whose __init__ function is \n" + pyInit.__init__.__doc__

def Spread(pop,  *args, **kwargs):
  spread(*args, **kwargs).apply(pop)

Spread.__doc__ = "Function version of operator spread whose __init__ function is \n" + spread.__init__.__doc__

def PyEval(pop, *args, **kwargs):
  pyEval(*args, **kwargs).apply(pop)

PyEval.__doc__ = "Function version of operator pyEval whose __init__ function is \n" + pyEval.__init__.__doc__

def PyExec(pop, *args, **kwargs):
  pyExec(*args, **kwargs).apply(pop)
   
PyExec.__doc__ = "Function version of operator pyExec whose __init__ function is \n" + pyExec.__init__.__doc__

def Stat(pop, *args, **kwargs):
  stat(*args, **kwargs).apply(pop)
  
Stat.__doc__ = "Function version of operator stat whose __init__ function is \n" + stat.__init__.__doc__

def KamMutate(pop, *args, **kwargs):
  kamMutator(*args, **kwargs).apply(pop)
  
KamMutate.__doc__ = "Function version of operator kamMutator whose __init__ function is \n" + kamMutator.__init__.__doc__

def SmmMutate(pop, *args, **kwargs):
  smmMutator(*args, **kwargs).apply(pop)
  
SmmMutate.__doc__ = "Function version of operator smmMutator whose __init__ function is \n" + smmMutator.__init__.__doc__

def GsmMutate(pop, *args, **kwargs):
  gsmMutator(*args, **kwargs).apply(pop)
  
GsmMutate.__doc__ = "Function version of operator gsmMutator whose __init__ function is \n" + gsmMutator.__init__.__doc__

def PyMutate(pop, *args, **kwargs):
  pyMutator(*args, **kwargs).apply(pop)

PyMutate.__doc__ = "Function version of operator pyMutator whose __init__ function is \n" + pyMutator.__init__.__doc__

def PointMutate(pop, *args, **kwargs):
  pointMutator(*args, **kwargs).apply(pop)
 
#PointMutate.__doc__ = "Function version of operator pointMutator whose __init__ function is \n" + pointMutator.__init__.__doc__

def Migrate(pop, *args, **kwargs):
  migrator(*args, **kwargs).apply(pop)

Migrate.__doc__ = "Function version of operator migrator whose __init__ function is \n" + migrator.__init__.__doc__

def PyMigrate(pop, *args, **kwargs):
  pyMigrate(*args, **kwargs).apply(pop)

PyMigrate.__doc__ = "Function version of operator pyMigrate whose __init__ function is \n" + pyMigrator.__init__.__doc__

def SplitSubPop(pop, *args, **kwargs):
  splitSubPop(*args, **kwargs).apply(pop)

#SplitSubPop.__doc__ = "Function version of operator splitSubPop whose __init__ function is \n" + splitSubPop.__init__.__doc__

def MergeSubPops(pop, *args, **kwargs):
  mergeSubPops(*args, **kwargs).apply(pop)
  
#mergeSubPops.__doc__ = "Function version of operator mergeSubPops whose __init__ function is \n" + mergeSubPops.__init__.__doc__

def RemoveSubPops(pop, *args, **kwargs):
  pop.removeSubPops(*args, **kwargs)
  
#RemoveSubPops.__doc__ = "Function versionof member function population::removeSubPop with help info:\n" + population.removeSubPops.__doc__

def RemoveEmptySubPops(pop, *args, **kwargs):
  pop.removeEmptySubPops(*args, **kwargs)
  
#RemoveEmptySubPops.__doc__ = "Function versionof member function population::removeEmptySubPops with help info:\n" + population.removeEmptySubPops.__doc__

def BasicPenetrance(pop, *args, **kwargs):
  basicPenetrance(stage=PostMating, *args, **kwargs).apply(pop)
  
BasicPenetrance.__doc__ = "Function version of operator basicPenetrance whose __init__ function is \n" + basicPenetrance.__init__.__doc__

def MaPenetrance(pop, *args, **kwargs):
  maPenetrance(stage=PostMating, *args, **kwargs).apply(pop)
  
MaPenetrance.__doc__ = "Function version of operator maPenetrance whose __init__ function is \n" + maPenetrance.__init__.__doc__

def MlPenetrance(pop, *args, **kwargs):
  mlPenetrance(stage=PostMating, *args, **kwargs).apply(pop)
  
MlPenetrance.__doc__ = "Function version of operator mlPenetrance whose __init__ function is \n" + mlPenetrance.__init__.__doc__

def PyPenetrance(pop, *args, **kwargs):
  pyPenetrance(stage=PostMating, *args, **kwargs).apply(pop)
  
PyPenetrance.__doc__ = "Function version of operator pyPenetrance whose __init__ function is \n" + pyPenetrance.__init__.__doc__

def BasicQuanTrait(pop, *args, **kwargs):
  basicQuanTrait(*args, **kwargs).apply(pop)
  
BasicQuanTrait.__doc__ = "Function version of operator basicQuanTrait whose __init__ function is \n" + basicQuanTrait.__init__.__doc__

def MaQuanTrait(pop, *args, **kwargs):
  maQuanTrait(*args, **kwargs).apply(pop)
  
MaQuanTrait.__doc__ = "Function version of operator maQuanTrait whose __init__ function is \n" + maQuanTrait.__init__.__doc__

def MlQuanTrait(pop, *args, **kwargs):
  mlQuanTrait(*args, **kwargs).apply(pop)
  
MlQuanTrait.__doc__ = "Function version of operator mlQuanTrait whose __init__ function is \n" + mlQuanTrait.__init__.__doc__

def PyQuanTrait(pop, *args, **kwargs):
  pyQuanTrait(*args, **kwargs).apply(pop)

PyQuanTrait.__doc__ = "Function version of operator pyQuanTrait whose __init__ function is \n" + pyQuanTrait.__init__.__doc__

def TicToc(pop, *args, **kwargs):
  ticToc(*args, **kwargs).apply(pop)
 
#TicToc.__doc__ = "Function version of operator ticToc whose __init__ function is \n" + ticToc.__init__.__doc__

def Sample(pop, *args, **kwargs):
  s = sample(*args, **kwargs)
  s.apply(pop)
  return s.sample(pop)

Sample.__doc__ = "Function version of operator sample whose __init__function is \n" + sample.__init__.__doc__

def RandomSample(pop, *args, **kwargs):
  s = randomSample(*args, **kwargs)
  s.apply(pop)
  return s.samples(pop) 

RandomSample.__doc__ = "Function version of operator randomSample whose __init__function is \n" + randomSample.__init__.__doc__

def CaseControlSample(pop, *args, **kwargs):
  s = caseControlSample(*args, **kwargs)
  s.apply(pop)
  return s.samples(pop)

CaseControlSample.__doc__ = "Function version of operator caseControlSample whose __init__function is \n" + caseControlSample.__init__.__doc__

def PySample(pop, *args, **kwargs):
  s = pySample(*args, **kwargs)
  s.apply(pop)
  return s.samples(pop)

PySample.__doc__ = "Function version of operator pySample whose __init__function is \n" + pySample.__init__.__doc__

def AffectedSibpairSample(pop, *args, **kwargs):
  s = affectedSibpairSample(*args, **kwargs)
  s.apply(pop)
  return s.samples(pop)

#AffectedSibpairSample.__doc__ = "Function version of operator affectedSibpairSample whose __init__function is \n" + affectedSibpairSample.__init__.__doc__

def SavePopulation(pop, *args, **kwargs):
  pop.savePopulation(*args, **kwargs)

SavePopulation.__doc__ = "Function versionof member function population::savePopulation with help info:\n" + population.savePopulation.__doc__

def SaveSimulator(simu, *args, **kwargs):
  simu.saveSimulator(*args, **kwargs)
  
SaveSimulator.__doc__ = "Function versionof member function simulator::saveSimulator with help info:\n" + simulator.saveSimulator.__doc__

#### /////////////////// SIMUPOP PYTHON REDEFINITION FUNCTIONS ////////////////////////
def new_population(self, size=1, ploidy=2, loci=[], sexChrom=False, 
  lociDist=[], subPop=[], ancestralDepth=0, alleleNames=[], lociNames=[],
  maxAllele=MaxAllele):
    ld = lociDist
    if len(lociDist) > 0 and type(lociDist[0]) in [types.TupleType, types.ListType]:
       ld = []
       for i in range(0, len(lociDist)):
         ld.extend( lociDist[i])
    ln = lociNames
    if len(lociNames) > 0 and type(lociNames[0]) in [types.TupleType, types.ListType]:
       ln = []
       for i in range(0, len(lociNames)):
         ln.extend( lociNames[i])
    _swig_setattr(self, population, 'this', 
      cppModule.new_population(size, ploidy, loci, sexChrom, ld, subPop, 
        ancestralDepth, alleleNames, ln, maxAllele))
    _swig_setattr(self, population, 'thisown', 1)

new_population.__doc__ = population.__init__.__doc__
del population.__init__
population.__init__ = new_population


def new_dumper(self, chrom=[], subPop=[], indRange=[], *args, **kwargs):
  # param chrom
  if type(chrom) == types.IntType:
    ch = [chrom]
  else:
    ch = chrom
  # parameter subPop
  if type(subPop) == types.IntType:
    sp = [subPop]
  else:
    sp = subPop
  # parameter indRange
  ir = indRange
  if len(indRange) > 0 and type(indRange[0]) in [types.TupleType, types.ListType]:
    ir = []
    for i in indRange:
      ir.extend(i)
  _swig_setattr(self, dumper, 'this', 
    cppModule.new_dumper(chrom=ch, subPop=sp, indRange=ir, *args, **kwargs))
  _swig_setattr(self, dumper, 'thisown', 1)
 
new_dumper.__doc__ = dumper.__init__.__doc__
del dumper.__init__
dumper.__init__ = new_dumper


def new_kamMutator(self, rate=[], *args, **kwargs):
  # parameter rate
  if type(rate) in [types.IntType, types.FloatType]:
    r = [rate]
  else:
    r = rate
  _swig_setattr(self, kamMutator, 'this', 
    cppModule.new_kamMutator(rate=r, *args, **kwargs))
  _swig_setattr(self, kamMutator, 'thisown', 1)
 
new_kamMutator.__doc__ = kamMutator.__init__.__doc__
del kamMutator.__init__
kamMutator.__init__ = new_kamMutator



def new_smmMutator(self, rate=[], *args, **kwargs):
  # parameter rate
  if type(rate) in [types.IntType, types.FloatType]:
    r = [rate]
  else:
    r = rate
  _swig_setattr(self, smmMutator, 'this', 
    cppModule.new_smmMutator(rate=r, *args, **kwargs))
  _swig_setattr(self, smmMutator, 'thisown', 1)
 
new_smmMutator.__doc__ = smmMutator.__init__.__doc__
del smmMutator.__init__
smmMutator.__init__ = new_smmMutator



def new_gsmMutator(self, rate=[], *args, **kwargs):
  # parameter rate
  if type(rate) in [types.IntType, types.FloatType]:
    r = [rate]
  else:
    r = rate
  _swig_setattr(self, gsmMutator, 'this', 
    cppModule.new_gsmMutator(rate=r, *args, **kwargs))
  _swig_setattr(self, gsmMutator, 'thisown', 1)
 
new_gsmMutator.__doc__ = gsmMutator.__init__.__doc__
del gsmMutator.__init__
gsmMutator.__init__ = new_gsmMutator



def new_pyMutator(self, rate=[], *args, **kwargs):
  # parameter rate
  if type(rate) in [types.IntType, types.FloatType]:
    r = [rate]
  else:
    r = rate
  _swig_setattr(self, pyMutator, 'this', 
    cppModule.new_pyMutator(rate=r, *args, **kwargs))
  _swig_setattr(self, pyMutator, 'thisown', 1)
 
new_pyMutator.__doc__ = pyMutator.__init__.__doc__
del pyMutator.__init__
pyMutator.__init__ = new_pyMutator




def new_migrator(self, rate, fromSubPop=[], toSubPop=[], *args, **kwargs):
  # parameter rate
  r = rate
  if type(rate) in  [types.IntType, types.LongType]:
    r = [[rate]]
  # parameter fromSubPop
  if type(fromSubPop) in [types.IntType, types.LongType]:
    fs = [fromSubPop]
  else:
    fs = fromSubPop
  # parameter toSubPop
  if type(toSubPop) in  [types.IntType, types.LongType]:
    ts = [toSubPop]
  else:
    ts = toSubPop
  _swig_setattr(self, migrator, 'this', 
    cppModule.new_migrator(rate=r, fromSubPop=fs, toSubPop=ts, *args, **kwargs))
  _swig_setattr(self, migrator, 'thisown', 1)
 
new_migrator.__doc__ = migrator.__init__.__doc__
del migrator.__init__
migrator.__init__ = new_migrator



def new_recombinator(self, intensity=-1, rate=[], afterLoci=[], 
  maleIntensity=-1, maleRate=[], maleAfterLoci=[], *args, **kwargs):
  # parameter rate
  if type(rate) in [types.IntType, types.FloatType]:
    if len(afterLoci) > 0:
      r = [rate]*len(afterLoci)
    else:
      r = [rate]
  else:
    r = rate
  # parameter maleRate
  if type(maleRate) in [types.IntType, types.FloatType]:
    if len(maleAfterLoci) > 0:
      mr = [maleRate]*len(maleAfterLoci)
    elif len(afterLoci) > 0:
      mr = [maleRate]*len(afterLoci)
    else:
      mr = [maleRate]
  else:
    mr = maleRate

  _swig_setattr(self, recombinator, 'this', 
    cppModule.new_recombinator(intensity=intensity, 
    rate=r, afterLoci=afterLoci, 
    maleIntensity=maleIntensity, 
    maleRate=mr, maleAfterLoci=maleAfterLoci, 
    *args, **kwargs))
  _swig_setattr(self, recombinator, 'thisown', 1)
 
new_recombinator.__doc__ = recombinator.__init__.__doc__
del recombinator.__init__
recombinator.__init__ = new_recombinator



def new_initByFreq(self, alleleFreq=[], indRange=[], *args, **kwargs):
  # parameter alleleFreq
  if len(alleleFreq) > 0 and type(alleleFreq[0]) in [types.IntType, types.LongType, types.FloatType]:
    af = [alleleFreq]
  else:
    af = alleleFreq
  # parameter indRange
  if len(indRange) > 0 and type(indRange[0]) in  [types.IntType, types.LongType]:
    ir = [indRange]
  else:
    ir = indRange
  _swig_setattr(self, initByFreq, 'this', 
    cppModule.new_initByFreq(alleleFreq=af, indRange=ir, *args, **kwargs))
  _swig_setattr(self, initByFreq, 'thisown', 1)
 
new_initByFreq.__doc__ = initByFreq.__init__.__doc__
del initByFreq.__init__
initByFreq.__init__ = new_initByFreq


def new_initByValue(self, value=[], indRange=[], *args, **kwargs):
  # parameter value
  if len(value) > 0 and type(value[0]) in [types.IntType, types.LongType]:
    val = [value]
  else:
    val = value
  # parameter indRange
  if len(indRange) > 0 and type(indRange[0]) in  [types.IntType, types.LongType]:
    ir = [indRange]
  else:
    ir = indRange
  _swig_setattr(self, initByValue, 'this', 
    cppModule.new_initByValue(value=val, indRange=ir, *args, **kwargs))
  _swig_setattr(self, initByValue, 'thisown', 1)
 
new_initByValue.__doc__ = initByValue.__init__.__doc__
del initByValue.__init__
initByValue.__init__ = new_initByValue


def new_pyInit(self, indRange=[], *args, **kwargs):
  # parameter indRange
  if len(indRange) > 0 and type(indRange[0]) in  [types.IntType, types.LongType]:
    ir = [indRange]
  else:
    ir = indRange
  _swig_setattr(self, pyInit, 'this', 
    cppModule.new_pyInit(indRange=ir, *args, **kwargs))
  _swig_setattr(self, pyInit, 'thisown', 1)
 
new_pyInit.__doc__ = pyInit.__init__.__doc__
del pyInit.__init__
pyInit.__init__ = new_pyInit




def new_stat(self, haploFreq=[], LD=[], relGroups=[], relMethod=[], *args, **kwargs):
  # parameter haploFreq
  if len(haploFreq) > 0 and type(haploFreq[0]) in [types.IntType, types.LongType]:
    hf = [haploFreq]
  else:
    hf = haploFreq
  # parameter LD
  if len(LD) > 0 and type(LD[0]) in  [types.IntType, types.LongType]:
    ld = [LD]
  else:
    ld = LD
  # parameter relGroups
  if relGroups == []:
    rg = [[]]
    useSubPop = True
  elif len(relGroups) > 0 and type(relGroups[0]) in  [types.IntType, types.LongType]:
    rg = [relGroups]
    useSubPop = True
  else:
    rg = relGroups
    useSubPop = False
  # parameter relMethod
  if type(relMethod) in [types.IntType, types.LongType]:
    rm = [relGroups]
  else:
    rm = relGroups

  _swig_setattr(self, stat, 'this', 
    cppModule.new_stat(haploFreq=hf, LD=ld, relGroups=rg, relBySubPop=useSubPop,
      relMethod = rm, *args, **kwargs))
  _swig_setattr(self, stat, 'thisown', 1)
 
new_stat.__doc__ = stat.__init__.__doc__
del stat.__init__
stat.__init__ = new_stat



def new_randomSample(self, size=[], *args, **kwargs):
  if type(size) in [types.IntType, types.LongType]:
    sz=[size]
  else:
    sz = size
  _swig_setattr(self, randomSample, 'this', 
    cppModule.new_randomSample(size=sz, *args, **kwargs))
  _swig_setattr(self, randomSample, 'thisown', 1)
 
new_randomSample.__doc__ = randomSample.__init__.__doc__
del randomSample.__init__
randomSample.__init__ = new_randomSample


def new_caseControlSample(self, cases=[], controls=[], *args, **kwargs):
  if type(cases) in [types.IntType, types.LongType]:
    ca = [cases]
    spSample = False
  else:
    ca = cases
    spSample = True
  if type(controls) in [types.IntType, types.LongType]:
    ct = [controls]
    spSample = False
  else:
    ct = controls
    spSample = True
  _swig_setattr(self, caseControlSample, 'this', 
    cppModule.new_caseControlSample(cases=ca, controls=ct, 
      spSample=spSample, *args, **kwargs))
  _swig_setattr(self, caseControlSample, 'thisown', 1)
 
new_caseControlSample.__doc__ = caseControlSample.__init__.__doc__
del caseControlSample.__init__
caseControlSample.__init__ = new_caseControlSample



def new_affectedSibpairSample(self,size=[], *args, **kwargs):
  if type(size) in [types.IntType, types.LongType]:
    sz=[size]
  else:
    sz = size
  _swig_setattr(self, affectedSibpairSample, 'this', 
    cppModule.new_affectedSibpairSample(size=sz, *args, **kwargs))
  _swig_setattr(self, affectedSibpairSample, 'thisown', 1)
 
new_affectedSibpairSample.__doc__ = affectedSibpairSample.__init__.__doc__
del affectedSibpairSample.__init__
affectedSibpairSample.__init__ = new_affectedSibpairSample

%}