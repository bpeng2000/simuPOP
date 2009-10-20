%module Mating_pyChooser_cpp_impl
%{
#include "Mating_pyChooser_cpp.h"
%}

/*
 To pass Python lists to C++ functions, and to return C++ vectors to Python,
 you will need to tell SWIG how to convert between them. The following
 code includes SWIG's STL (standard template libraries) header files, and
 instantialize the types of vectors Mating_pyChooser_cpp.h uses.
*/

// std_vector.i for std::vector
%include "std_vector.i"
%template() std::vector<double>;

// stl.i for std::pair
%include "stl.i"
%template() std::pair<unsigned long, unsigned long>;

%include "Mating_pyChooser_cpp.h"