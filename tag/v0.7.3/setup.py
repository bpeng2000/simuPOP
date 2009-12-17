"""
simuPOP installer 

In case that you have modified the C++ code, or you are
checking out simuPOP from svn repository, you need to 
install swig >= 1.3.27 to generate the wrap files.

"""

from distutils.core import setup, Extension
from distutils.ccompiler import new_compiler

import os, shutil, sys, glob, re
#
# XML_SUPPORT will be disabled for mac machines due to a bug
# in mac/gcc. You will not be able to save population in xml 
# format under a mac. Binary and txt formats are still supported
# and should suffice most applications.
#
# If you do need XML_SUPPORT under mac, you can 
# set XML_SUPPORT = True and try to compile.
#
if os.name == 'posix' and os.uname()[0] == 'Darwin':
    XML_SUPPORT = False
else:
    XML_SUPPORT = True

# under windows, the difference between mingw/cygwin static/shared
# and different versions of zlib really make a mess. Under linux,
# mandrivia uses /usr/include/linux for zlib.h etc but I can not 
# find a safe way to add this path in. Therefore, I am embedding
# a zlib under this system. You can change EMBED_ZLIB = False 
# to use system zlib.
EMBED_ZLIB = True

# for every official release, there will be a file recording release info
# Othersise, SIMUPOP_VER and SIMUPOP_REV will be provided as environmental
# variables.
if os.environ.has_key('SIMUPOP_VER') and os.environ.has_key('SIMUPOP_REV'):
        SIMUPOP_VER = os.environ['SIMUPOP_VER']
        SIMUPOP_REV = os.environ['SIMUPOP_REV']
else:
        execfile('simuPOP.release')
std_macro = [('SIMUPOP_VER', SIMUPOP_VER), 
                         ('SIMUPOP_REV', SIMUPOP_REV) ]
        
# Source files
HEADER_FILES = [
    'src/simupop_cfg.h',
    'src/utility.h',
    'src/individual.h',
    'src/population.h',
    'src/simulator.h',
    'src/mating.h',
    'src/operator.h',
    'src/initializer.h',
    'src/migrator.h',
    'src/outputer.h',
    'src/selector.h',
    'src/stator.h',
    'src/terminator.h',
    'src/mutator.h',
    'src/recombinator.h',
    'src/tagger.h',
]

SOURCE_FILES = [
    'src/utility.cpp',
    'src/individual.cpp',
    'src/population.cpp',
    'src/simulator.cpp',
    'src/mating.cpp',
    'src/operator.cpp',
    'src/initializer.cpp',
    'src/migrator.cpp',
    'src/outputer.cpp',
    'src/selector.cpp',
    'src/stator.cpp',
    'src/terminator.cpp',
    'src/mutator.cpp',
    'src/recombinator.cpp',
    'src/tagger.cpp',
]

# create source file for each module
MODU_SOURCE_FILES = {'std':[], 'op':[], 'la':[], 'laop':[], 'ba':[], 'baop':[]}
for modu in ['std', 'op', 'la', 'laop', 'ba', 'baop']:
    for src in SOURCE_FILES:
        mod_src = src[:-4] + '_' + modu + '.cpp'
        shutil.copy(src, mod_src)
        MODU_SOURCE_FILES[modu].append( mod_src )
    MODU_SOURCE_FILES[modu].append( 'src/simuPOP_' + modu + '_wrap.cpp' )
    
if sys.argv[1] not in ['sdist']:
    # checking os type and copy configuration files
    if os.name == 'nt':    # Windows
        shutil.copy('config_win32.h', 'config.h')
    elif os.name == 'posix':
        sysName = os.uname()[0]
        if sysName == 'Linux':     # Linux
            shutil.copy('config_linux.h', 'config.h')
        elif sysName == 'SunOS': # Solaris
            shutil.copy('config_solaris.h', 'config.h')
        elif sysName == 'Darwin':    # MacOS
            shutil.copy('config_mac.h', 'config.h')
    else:
        try:
            open('config.h')
            close('config.h')
            print "Warning: Unknown system type. Using existing config.h"
        except IOError:
            print "Error: Unknown system type. Use configure to generate config.h."
            sys.exit()

WRAP_INFO = [
    ['src/simuPOP_std_wrap.cpp', 'src/simuPOP_std.i', ''],
    ['src/simuPOP_op_wrap.cpp', 'src/simuPOP_op.i', '-DOPTIMIZED'],
    ['src/simuPOP_la_wrap.cpp', 'src/simuPOP_la.i', '-DLONGALLELE'],
    ['src/simuPOP_laop_wrap.cpp', 'src/simuPOP_laop.i', '-DLONGALLELE -DOPTIMIZED'],
    ['src/simuPOP_ba_wrap.cpp', 'src/simuPOP_ba.i', '-DBINARYALLELE'],
    ['src/simuPOP_baop_wrap.cpp', 'src/simuPOP_baop.i', '-DBINARYALLELE -DOPTIMIZED'],
]    


def swig_version():
    ''' get the version of swig '''
    fout = os.popen('swig -version')
    #
    try:
        version = re.match('SWIG Version\s*(\d+).(\d+).(\d+).*', fout.readlines()[1]).groups()
    except:
        print 'Can not obtain swig version, please install swig'
        sys.exit(1)
    return map(int, version)
        

# if any of the wrap files does not exist
# or if the wrap files are older than any of the source files.
if (False in [os.path.isfile(WRAP_INFO[x][0]) for x in range(len(WRAP_INFO))]) or \
    (max( [os.path.getmtime(x) for x in HEADER_FILES] ) > \
     min( [os.path.getmtime(WRAP_INFO[x][0]) for x in range(len(WRAP_INFO))])):
    (v1, v2, v3) = swig_version()
    if (v1, v2, v3) >= (1, 3, 28):
        # for swig >= 1.3.28
        SWIG = 'swig -O -templatereduce -shadow -python -c++ -keyword -nodefaultctor -w-503,-312,-511,-362,-383,-384,-389,-315,-525'
    elif (v1, v2, v3) >= (1, 3, 25):
        # for swig from 1.3.25 to 1.3.27
        SWIG = 'swig -shadow -c++ -python -keyword -w-312,-401,-503,-511,-362,-383,-384,-389,-315,-525'
    else:
        print 'Swig >= 1.3.25 is required, please upgrade it.'
        sys.exit(1)
    # generate header file 
    print "Generating external runtime header file..."
    os.system( 'swig -python -external-runtime swigpyrun.h' )
    # try the first option set with the first library
    for lib in range(len(WRAP_INFO)):
        print "Generating wrap file " + WRAP_INFO[lib][0]
        if os.system('%s %s -o %s %s' % (SWIG, WRAP_INFO[lib][2], WRAP_INFO[lib][0], WRAP_INFO[lib][1])) != 0:
            print "Calling swig failed. Please check your swig version."
            sys.exit(1)
    print
    print "All wrap files are generated successfully."
    print


DESCRIPTION = """
simuPOP is a forward-time population genetics simulation environment.
The core of simuPOP is a scripting language (Python) that provides 
a large number of objects and functions to manipulate populations, 
and a mechanism to evolve populations forward in time. Using this 
R/Splus-like environment, users can create, manipulate and evolve 
populations interactively, or write a script and run it as a batch 
file. Owing to its flexible and extensible design, simuPOP can simulate
large and complex evolutionary processes with ease. At a more 
user-friendly level, simuPOP provides an increasing number of built-in
scripts that perform simulations ranging from implementation of basic 
population genetics models to generating datasets under complex 
evolutionary scenarios. simuPOP is currently bundled with a Python
binding of coaSim.
"""

def buildStaticLibrary(sourceFiles, libName, libDir, compiler):
    '''Build libraries to be linked to simuPOP modules'''
    # get a c compiler
    print 'Creating library', libName
    comp = new_compiler(compiler=compiler, verbose=True)
    objFiles = comp.compile(sourceFiles, include_dirs=['.'])
    comp.create_static_lib(objFiles, libName, libDir)
            
GSL_FILES = [ 
    'gsl/sys/infnan.c',
    'gsl/sys/coerce.c',
    'gsl/sys/fdiv.c',
    'gsl/sys/pow_int.c',
    'gsl/sys/fcmp.c',
    'gsl/specfunc/psi.c',
    'gsl/specfunc/trig.c',
    'gsl/specfunc/exp.c',
    'gsl/specfunc/log.c',
    'gsl/specfunc/erfc.c',
    'gsl/specfunc/zeta.c',
    'gsl/specfunc/elementary.c',
    'gsl/specfunc/gamma.c',
    'gsl/rng/borosh13.c',
    'gsl/rng/fishman2x.c',
    'gsl/rng/mt.c',
    'gsl/rng/rand.c',
    'gsl/rng/ranmar.c',
    'gsl/rng/types.c',
    'gsl/rng/cmrg.c',
    'gsl/rng/gfsr4.c',
    'gsl/rng/r250.c',
    'gsl/rng/random.c',
    'gsl/rng/rng.c',
    'gsl/rng/uni32.c',
    'gsl/rng/coveyou.c',
    'gsl/rng/knuthran2.c',
    'gsl/rng/ran0.c',
    'gsl/rng/randu.c',
    'gsl/rng/slatec.c',
    'gsl/rng/uni.c',
    'gsl/rng/default.c',
    'gsl/rng/knuthran.c',
    'gsl/rng/ran1.c',
    'gsl/rng/ranf.c',
    'gsl/rng/taus113.c',
    'gsl/rng/vax.c',
    'gsl/rng/file.c',
    'gsl/rng/lecuyer21.c',
    'gsl/rng/ran2.c',
    'gsl/rng/ranlux.c',
    'gsl/rng/taus.c',
    'gsl/rng/waterman14.c',
    'gsl/rng/fishman18.c',
    'gsl/rng/minstd.c',
    'gsl/rng/ran3.c',
    'gsl/rng/ranlxd.c',
    'gsl/rng/transputer.c',
    'gsl/rng/zuf.c',
    'gsl/rng/fishman20.c',
    'gsl/rng/mrg.c',
    'gsl/rng/rand48.c',
    'gsl/rng/ranlxs.c',
    'gsl/rng/tt.c',
    'gsl/randist/nbinomial.c',
    'gsl/randist/beta.c',
    'gsl/randist/exponential.c',
    'gsl/randist/geometric.c',
    'gsl/randist/binomial.c',
    'gsl/randist/poisson.c',
    'gsl/randist/rdgamma.c',
    'gsl/randist/multinomial.c',
    'gsl/randist/chisq.c',
    'gsl/randist/gauss.c',
    'gsl/error.c' 
]


SERIAL_FILES = [
    'src/serialization/basic_archive.cpp',
    'src/serialization/basic_iarchive.cpp',
    'src/serialization/basic_oarchive.cpp',
    'src/serialization/basic_serializer_map.cpp',
    'src/serialization/basic_text_iprimitive.cpp',
    'src/serialization/basic_text_oprimitive.cpp',
    'src/serialization/binary_iarchive.cpp',
    'src/serialization/binary_oarchive.cpp',
    'src/serialization/extended_type_info.cpp',
    'src/serialization/extended_type_info_no_rtti.cpp',
    'src/serialization/extended_type_info_typeid.cpp',
    'src/serialization/text_iarchive.cpp',
    'src/serialization/text_oarchive.cpp',
    'src/serialization/void_cast.cpp',
    'src/serialization/polymorphic_iarchive.cpp',
    'src/serialization/polymorphic_oarchive.cpp',
    'src/serialization/stl_port.cpp',
    'src/serialization/basic_pointer_iserializer.cpp',
    'src/serialization/basic_iserializer.cpp',
    'src/serialization/basic_oserializer.cpp',
    'src/serialization/basic_pointer_oserializer.cpp',
    'src/serialization/basic_archive_impl.cpp'
]

IOSTREAMS_FILES = [
    'src/iostreams/mapped_file.cpp',
    'src/iostreams/file_descriptor.cpp',
    'src/iostreams/zlib.cpp'
]

# after hacking around cygwin/mingw zlib1.dll mgwz.dll,
# I decide to embed zlib. This is not a good choice but
# I am tired of the extra complexities.
ZLIB_FILES = [
    'zlib/adler32.c',
    'zlib/compress.c',
    'zlib/crc32.c',
    'zlib/deflate.c',
    'zlib/gzio.c',
    'zlib/inffast.c',
    'zlib/inflate.c',
    'zlib/infback.c',
    'zlib/inftrees.c',
    'zlib/trees.c',
    'zlib/uncompr.c',
    'zlib/zutil.c',
]

if XML_SUPPORT: 
    SERIAL_FILES.extend( [
        'src/serialization/basic_xml_archive.cpp',
        'src/serialization/xml_grammar.cpp',
        'src/serialization/xml_iarchive.cpp',
        'src/serialization/xml_oarchive.cpp'
        ]
    )

SOURCE = GSL_FILES + SERIAL_FILES + IOSTREAMS_FILES
LIBRARIES = ['z', 'stdc++']
EXTRA_COMPILER_ARGS = ['-O3']
INCLUDES = ['.']

if EMBED_ZLIB:
    SOURCE += ZLIB_FILES
    LIBRARIES.remove('z')
    INCLUDES.append('zlib')

# find all test files
DATA_FILES =    [
    ('share/simuPOP', ['README', 'INSTALL', 'ChangeLog', 'AUTHORS', 
        'COPYING', 'TODO', 'simuPOP.release']), 
    ('share/simuPOP/doc', ['doc/userGuide.pdf', 'doc/userGuide.py', 'doc/refManual.pdf']), 
    ('share/simuPOP/test', glob.glob('test/test_*.py')),
    ('share/simuPOP/misc', ['misc/README', 'misc/python-mode.el', 'misc/emacs-python.el']),
    ('share/simuPOP/scripts', glob.glob('scripts/*.py'))
]

if not XML_SUPPORT: # using serialization library with xml support
    std_macro.append( ('__NO_XML_SUPPORT__', None) )
    
setup(
    name = "simuPOP",
    version = SIMUPOP_VER,
    author = "Bo Peng",
    author_email = "bpeng@rice.edu",
    description = "Forward-time population genetics simulation environment",
    long_description = DESCRIPTION, 
    url = "http://simupop.sourceforge.net",
    package_dir = {'': 'src' }, 
    py_modules = ['simuPOP', 'simuOpt', 'simuPOP_std', 'simuPOP_op', 'simuPOP_la', 'simuPOP_laop', 
        'simuPOP_ba', 'simuPOP_baop', 'simuUtil', 'simuSciPy', 'simuMatPlt', 'simuRPy', 'simuViewPop' ],
    ext_modules = [
        Extension('_simuPOP_std',
            extra_compile_args = EXTRA_COMPILER_ARGS,
            include_dirs = INCLUDES,
            library_dirs = ['build'],
            libraries = LIBRARIES,
            define_macros = [ ('SIMUPOP_MODULE', 'simuPOP_std')] + std_macro,
            sources = MODU_SOURCE_FILES['std'] + SOURCE
        ),
        Extension('_simuPOP_op',
            extra_compile_args = EXTRA_COMPILER_ARGS,
            include_dirs = INCLUDES,
            library_dirs = ['build'],
            libraries = LIBRARIES,
            define_macros = [ ('SIMUPOP_MODULE', 'simuPOP_op'), ('OPTIMIZED', None)] + std_macro,
            sources = MODU_SOURCE_FILES['op'] + SOURCE
        ),
        Extension('_simuPOP_la',
            extra_compile_args = EXTRA_COMPILER_ARGS,
            include_dirs = INCLUDES,
            library_dirs = ['build'],
            libraries = LIBRARIES,
            define_macros = [ ('SIMUPOP_MODULE', 'simuPOP_la'), ('LONGALLELE', None) ] + std_macro,
            sources = MODU_SOURCE_FILES['la'] + SOURCE
        ),
        Extension('_simuPOP_laop',
            extra_compile_args = EXTRA_COMPILER_ARGS,
            include_dirs = INCLUDES,
            library_dirs = ['build'],
            libraries = LIBRARIES,
            define_macros = [ ('SIMUPOP_MODULE', 'simuPOP_laop'), ('LONGALLELE', None), 
                                                ('OPTIMIZED', None) ] + std_macro,
            sources = MODU_SOURCE_FILES['laop'] + SOURCE
        ),
        Extension('_simuPOP_ba',
            extra_compile_args = EXTRA_COMPILER_ARGS,
            include_dirs = INCLUDES,
            library_dirs = ['build'],
            libraries = LIBRARIES,
            define_macros = [ ('SIMUPOP_MODULE', 'simuPOP_ba'), ('BINARYALLELE', None) ] + std_macro,
            sources = MODU_SOURCE_FILES['ba'] + SOURCE
        ),
        Extension('_simuPOP_baop',
            extra_compile_args = EXTRA_COMPILER_ARGS,
            include_dirs = INCLUDES,
            library_dirs = ['build'],
            libraries = LIBRARIES,
            define_macros = [ ('SIMUPOP_MODULE', 'simuPOP_baop'), ('BINARYALLELE', None), 
                                                ('OPTIMIZED', None) ] + std_macro,
            sources = MODU_SOURCE_FILES['baop'] + SOURCE
        ),
    ],
    data_files = DATA_FILES
)

# keep the source code of snapshot version since snapshot may be 
# changed frequently.
if not SIMUPOP_VER == 'snapshot':
    for modu in ['std', 'op', 'la', 'laop', 'ba', 'baop']:
        for src in MODU_SOURCE_FILES[modu][:-1] :
            os.remove(src)