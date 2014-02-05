#!/usr/bin/env python

#
# $File: plotter.py $
# $LastChangedDate$
# $Rev$
#
# This file is part of simuPOP, a forward-time population genetics
# simulation environment. Please visit http://simupop.sourceforge.net
# for details.
#
# Copyright (C) 2004 - 2010 Bo Peng (bpeng@mdanderson.org)
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#

'''
This module defines several utility functions and Python operators that make
use of the Python rpy module (http://rpy.sourceforge.net) to plot expressions
and information fields of evolving populations using a popular statistical
analysis language R (http://www.r-project.org) or matplotlib. Note that 
rpy2, the successor of rpy, is currently not supported. You can specify the
plotting library using simuOpt.setOptions(plotter='matplotlib').

Each operator calls a sequence of R or matplotlib functions to draw and save
figures. A special parameter passing mechanism is used so that you can specify
arbitrary parameters to these functions. For example, you can use parameter
``par_mfrow=[2,2]`` to pass ``mfrow=[2,2]`` to function ``par``, and use
``lty_rep=[1,2]`` to pass ``lty=1`` and ``lty=2`` to specify different line
types for different replicates if ``rpy`` is used. The help message of each class
will describe which and in what sequence these R or matplotlib functions are
called to help you figure out which parameters are allowed.
'''

__all__ = [
    'newDevice', 
    'saveFigure',
    'DerivedArgs',
    'VarPlotter',
    'ScatterPlotter',
    'InfoPlotter',
    'HistPlotter',
    'QQPlotter',
    'BoxPlotter',
    # export essential piece of rpy so that other modules could use them
    'r',
    'with_mode',
    'NO_CONVERSION'
]
    
from math import ceil, sqrt
import os

from simuOpt import simuOptions

if simuOptions['Plotter'] is None:
    try:
        import rpy_options
        rpy_options.set_options(VERBOSE = False)
        from rpy import r, with_mode, NO_CONVERSION
        use_rpy = True
    except ImportError, e:
        try:
            import matplotlib.pylab as plt
            use_rpy = False
        except:
            print('Neither rpy nor matplotlib is available.')
            raise e
elif simuOptions['Plotter'] == 'rpy':
    import rpy_options
    rpy_options.set_options(VERBOSE = False)
    from rpy import r, with_mode, NO_CONVERSION
    use_rpy = True
else:
    import matplotlib.pylab as plt
    use_rpy = False


# if under windows, fix a bug with rpy which uses blocking i/o so
# R figure will not be refreshed in time. See
#     https://Stat.ethz.ch/pipermail/r-devel/2006-January/036049.html
# for details.
if use_rpy and os.name == 'nt':
    r.options(windowsBuffered=False)
    # In addition to options(windowsBuffered=False), I find that I also need to
    # call windows.options(buffered=False) to make functions such as hist work.
    #
    # This function is only available for R 2.9.0 (rev 48333)
    if int(r.R_Version()['svn rev']) >= 48333:
        r.windows_options(buffered=False)


from simuPOP import PyOperator, ALL_AVAIL

def newDevice():
    '''Create a new graphics window and return its device number in R. This
    function essentially calls ``getOption('device')()`` in R.
    '''
    if use_rpy:
        # open a new window
        try:
            # 46754 is the revision number for R 2.8.0
            if int(r.R_Version()['svn rev']) < 46754:
                # For R < 2.8.0, getOption('device') returns a string (such as 'X11')
                r(r.getOption('device') + '()')
            else:
                # For R >= 2.8.0, getOption('device') returns a function
                r('getOption("device")()')
        except:
            raise RuntimeError("Failed to get R version to start a graphical device");
        # get device number
        device = r.dev_cur()
        if device == 0:
            raise RuntimeError('Can not open new device')
        return device
    else:
        return plt.figure()

def saveFigure(file=None, **kwargs):
    '''
    Save current figure into ``file``. File format and graphics device are
    determined by file extension. Supported file formats include ``pdf``,
    ``png``, ``bmp``, ``jpg (jpeg)``, ``tif (tiff)``, and ``eps``, which
    correspond to R devices ``pdf``, ``png``, ``bmp``, ``jpeg``, ``tiff``
    and ``postscript``. A postscript device will be used if there is no file
    extension or the file extension is not recognizable. Additional keyword
    parameters will be passed to the underlying ``dev.print`` function.
    '''
    if file is None:
        return
    if use_rpy:
        filename, ext = os.path.splitext(file)
        dirname = os.path.dirname(file)
        if dirname != '' and not os.path.isdir(dirname):
            # this might fail and raise an error
            os.makedirs(dirname)
        # default extension and format
        if ext == '':
            ext = '.eps'
        #
        params = {}
        # these two parameters have to be specified for raster formats
        try:
            # I need to use this more lengthy form because some
            # functions are not available in, for example, R 2.6.2
            if ext.lower() == '.pdf':
                device = r.pdf
            elif ext.lower() == '.png':
                device = r.png
                params = {'width': 800, 'height': 600}
            elif ext.lower() == '.bmp':
                device = r.bmp
                params = {'width': 800, 'height': 600}
            elif ext.lower() in ['.jpg', '.jpeg']:
                device = r.jpeg
                params = {'width': 800, 'height': 600}
            elif ext.lower() in ['.tif', '.tiff']:
                device = r.tiff
                params = {'width': 800, 'height': 600}
            elif ext.lower() == '.eps':
                device = r.postscript
        except Exception, e:
            print e
            print 'Can not determine which device to use to save file %s. A postscript driver is used.' % name
            device = r.postscript
        params.update(kwargs)
        r.dev_print(file=file, device=device, **params)
    else:
        plt.savefig(file)


class DerivedArgs:
    '''This class implements the derived keyword argument handling mechanism that
    is used by all classes defined in this module. It is provided for users who
    would like to use this mechanism for their own rpy or matplotlib-related
    operators.
    
    An derived keyword argument is an argument that is prefixed with a function
    name and/or suffixed by an iterator name. The former specifies to which
    underlying R function this parameter will be passed to; the latter allows
    the users to specify a list of values that will be passed, for example, to
    lines representing different replicates. For example, parameter
    ``par_mar=[1]*4`` will pass ``mar=[1]*4`` to R function ``par``, and
    ``lty_rep=[1, 2, 3]`` will pass ``lty=1``, ``lty=2`` and ``lty=3`` to
    different replicates.

    Values provided to derived arguments are usually passed unchanged, but with
    one exception: string value with a leading ``!`` mark will be evaluated
    against the current population before it is returned. For example,
    ``main='!"Allele frequency at generation %d" % gen'`` will return 
    ``main="Allele frequency at generation 100"`` at generation 100.
    '''
    def __init__(self, defaultFuncs=[], allFuncs=[], suffixes=[], defaultParams={}, **kwargs):
        '''
        defaultFunc
            Default functions. Parameters without a prefix will be passed to
            these functions.

        allFuncs
            Allowed functions. This should be all the R functions called in
            your class.

        suffixes
            A list of allowed suffixes.

        defaultParams
            Default parameters in a dictionary. E.g. ``{'plot_type': 'l'}``
            will pass ``type='l'`` to the ``plot`` function unless users
            provides another value.

        kwargs
            User specified parameters. These parameters will overwide
            default values in ``defaultParams``.
        '''
        self.defaultFuncs = defaultFuncs
        self.allFuncs = allFuncs
        self.suffixes = suffixes
        self.params = kwargs
        self.addDefault(**defaultParams)

    def addDefault(self, **kwargs):
        '''Add keyword parameters kwargs if they have not been defined.
        '''
        # due to various forms, it is surprisingly difficult to figure out
        # which parameter has been given.
        def baseForm(name):
            for suffix in self.suffixes:
                if name.endswith('_' + suffix):
                    return name[:-len('_' + suffix)]
            return name
        #
        def funcForm(name):
            base = baseForm(key)
            if True in [base.startswith(x + '_') for x in self.allFuncs]:
                return [base]
            else:
                return ['%s_%s' % (x, base) for x in self.defaultFuncs]
        #
        existingParams = []
        for key in self.params.keys():
            existingParams.extend(funcForm(key))
        #
        for key,value in kwargs.iteritems():
            funcs = funcForm(key)
            exist = False
            for func in funcs:
                if func in existingParams:
                    exist = True
            if not exist:
                self.params[key] = value

    def getArgs(self, func, pop, **kwargs):
        '''Get all single format parameters from keyword parameters. Additional
        keyword arguments can be used to specify suffix and its index. (e.g.
        rep=1 will return the second element of par_rep). Unrecognized keyword
        arguments are handled as default value that will be used if a parameter
        is not defined. E.g. ``getArgs('line', pop, rep=1, pch=4)`` will get
        parameters for replicate 1 and add ``pch=4`` if ``pch`` is not defined.
        '''
        if func not in self.allFuncs:
            raise ValueError('%s is not among the allowed functions' % func)
        ret = {}
        for key,value in self.params.iteritems():
            # this is a prefixed parameter
            par = None
            if True in [key.startswith(x + '_') for x in self.allFuncs]:
                if key.startswith(func + '_'):
                    # function specific, accept
                    par = key[len(func + '_'):]
            # not prefixed, accept if func is one of the default funcs
            elif func in self.defaultFuncs:
                par = key
            if par is None:
                continue
            # is this a suffixed parameter?
            if True in [par.endswith('_' + x) for x in self.suffixes]:
                for suffix,idx in kwargs.iteritems():
                    if not suffix in self.suffixes:
                        continue
                    if par.endswith('_' + suffix):
                        if type(value) in [type(()), type([])]:
                            ret[par[:-len('_' + suffix)]] = value[idx % len(value)]
                        else:
                            ret[par[:-len('_' + suffix)]] = value
                        break
            else:
                ret[par] = value
        # unrecognized keyword arguments?
        for key,value in kwargs.iteritems():
            if not key in self.suffixes and not ret.has_key(key):
                ret[key] = value
        # evalulate the values if needed
        for key in ret.keys():
            if type(ret[key]) == type('') and ret[key].startswith('!') and pop is not None:
                ret[key] = pop.evaluate(ret[key][1:])
        return ret

    def getLegendArgs(self, func, pop, args, keys, values, **kwargs):
        '''
        Get argument values for legend drawing purposes. For example, 

            getLegendArgs('lines', pop, ['lty', 'pch'], 'rep', [0,1,2])
        
        will get parameter for ``lty`` and ``pch`` for all ``rep``. If there
        are more keys (e.g. ``['rep', 'dim']``), values should be a list of
        of lists (e.g., ``[(0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2)]``).
        Default values could be passed as additional keyword arguments.
        '''
        # get param using getArgs
        ret = {}
        for arg in args:
            ret[arg] = []
        for val in values:
            # compose a dictionary with these values
            index = {}
            if type(keys) == type(''):
                index[keys] = val
            else:
                for k,v in zip(keys, val):
                    index[k] = v
            index.update(kwargs)
            vals = self.getArgs(func, pop, **index)
            for arg in args:
                if vals.has_key(arg):
                    ret[arg].append(vals[arg])
        #
        for arg in args:
            if len(ret[arg]) == 0:
                ret.pop(arg)
        return ret


class VarPlotter(PyOperator):
    '''
    This class defines a Python operator that uses R to plot the current and
    historical values of a Python expression (``expr``), which are evaluated
    (against each population's local namespace) and saved during evolution. The
    return value of the expression can be a number or a sequence, but should
    have the same type and length across all replicates and generations.
    Histories of each value (or each item in the returned sequence) of each
    replicate form a line, with generation numbers as its x-axis. Number of
    lines will be the number of replicates multiplied by dimension of the
    expression. Although complete histories are usually saved, you can use
    parameter ``win`` to save histories only within the last ``win``
    generations.
    
    A figure will be draw at the end of the last replicate (except for the
    first generation where no line could be drawn) unless the current
    generation is less than ``update`` generations away from the last
    generation at which a figure has been drawn. Lines for multiple replicates
    or dimensions could be plotted in the same figure (by default), or be
    seperated to subplots by replicates (``byRep``), by each dimention of the
    results (``byDim``), or by both. These figure could be saved to files in
    various formats if parameter ``saveAs`` is specified. File format is
    determined by file extension. After the evolution, the graphic device could
    be left open (``leaveOpen``).

    If the rpy module is used (default if rpy if available), arbitrary keyword
    parameters could be specified and be passed to the underlying R drawing functions
    ``plot`` and ``lines``. These parameters could be used to specify line type (``lty``),
    color (``col``), title (``main``), limit of x and y axes (``xlim`` and
    ``ylim``) and many other options (see R manual for details). As a special
    case, multiple values can be passed to each replicate and/or dimension if
    the name of a parameter ends with ``_rep``, ``_dim``, or ``_repdim``
    For example, ``lty_rep=range(1, 5)`` will pass parameters ``lty=1``, ...
    ``lty=4`` to four replicates. You can also pass parameters to specific
    R functions such as ``par``, ``plot``, ``lines``, ``legend``, ``dev_print``
    by prefixing parameter names with a function name. For example, 
    ``dev_print_width=300`` will pass ``width=300`` to function ``dev.print()``
    when you save your figures using this function. In addition, if the value
    of a parameter is a string starting with ``!``, the evaluated result of
    the remaining string will be used as parameter value. Further customization
    of your figures could be achieved by writing your own hook functions that
    will be called before and after a figure is drawn, and after each ``plot``
    call.

    This opertor calls R functions ``par``, ``plot``, ``lines``, ``legend``,
    and ``dev.print``. Functions ``plot`` and ``lines`` are the default
    destination for keyword arguments and the ones that accept list parameters
    to customize lines by replicate and/or dimension.
    '''
    def __init__(self, expr, win=0, update=1, byRep=False, byDim=False,
        saveAs="", leaveOpen=False, legend=[], preHook=None, postHook=None,
        plotHook=None, begin=0, end=-1, step=1, at=[],
        reps=ALL_AVAIL, **kwargs):
        '''
        expr
            expression that will be evaluated at each replicate's local
            namespace when the operator is applied. Its value can be a number
            or a list (or tuple) but the type and length of the return value
            should be consistent for all replicates and at all generations.

        win
            Window of generations. If given, only values from generation -win
            to -1 will be plotted.

        update
            Update the figure after specified generations. For example, you can
            evalulate an expression and save its values at every 10 generations
            (parameter ``step=10``) but only draw a figure after every 50
            generations (parameter ``update=50``.

        byRep
            Separate values at different replicates to different subplots.
            
        byDim
            Separate items from sequence results of ``expr`` to different
            subplots. If both ``byRep`` and ``byDim`` are ``True``, the
            subplots will be arranged by variable and then replicates.

        saveAs
            Save figures in files saveAs_gen.ext (e.g. ``figure_10.eps`` if
            ``saveAs='figure.eps'``). If ext is given, a corresponding device
            will be used. Otherwise, a default postscript driver will be used.
            Currently supported formats include ``.pdf``, ``.png``, ``.bmp``,
            ``.jpg``, and ``.tif``. The default filename could be overridden
            by derived argument ``dev_print_file``.

        leaveOpen
            Whether or not leave the plot open when plotting is done. Default
            to ``False`` functions. If this option is set to ``True``, you will
            have to close the graphic device explicitly using function
            ``r.dev_off()``. Note that leaving the device open allows
            further manipuation of the figures outside of this operator.

        legend
            labels of the lines. This operator will look for keyword parameters
            such as ``col``, ``lty``, ``lwd``, and ``pch`` and call the
            ``legend`` function to draw a legend. If figure has multiple lines
            for both replicates and dimensions, legends should be given to each
            dimension, and then each replicate.

        preHook
            A function that, if given, will be called before the figure is
            draw. The ``r`` object for ``rpy`` or ``Axes`` object for ``matplotlib``
            will be passed to this function.

        postHook
            A function that, if given, will be called after the figure is
            drawn.  The ``r`` object for ``rpy`` or ``Axes`` object for ``matplotlib``
            will be passed to this function.

        plotHook
            A function that, if given, will be called after each ``plot``
            function. The ``r`` object from the ``rpy`` module or ``Figure``
            object from the ``matplotlib`` module , generation
            list, data being plotted, replicate number (if applicable) and
            dimension index (if applicable) will be passed as keyword arguments
            ``r``, ``gen``, ``data``, ``rep`` (optional) and ``dim``
            (optional).

        kwargs
            Additional keyword arguments that will be interpreted and sent to
            underlying R or matplotlib functions. These arguments could have prefixes
            (destination function names) ``plot_``, ``lines_``, ``par_``,
            ``legend_`` and ``dev_print_``, and suffixes (list parameters)
            ``_rep``, ``_dim``, and ``_repdim`` for the ``rpy`` option. Arguments
            without prefixes are sent to functions ``plot`` and ``lines``. String
            values with a leading ``!`` will be replaced by its evaluated result
            against the current population.
        '''
        # parameters
        self.expr = expr
        self.win = win
        self.update = update
        self.byRep = byRep
        self.byDim = byDim
        self.saveAs = saveAs
        self.leaveOpen = leaveOpen
        self.legend = legend
        self.preHook = preHook
        self.postHook = postHook
        self.plotHook = plotHook
        if use_rpy:
            self.args = DerivedArgs(
                defaultFuncs = ['plot', 'lines'],
                allFuncs = ['par', 'plot', 'lines', 'dev_print', 'legend'],
                suffixes = ['rep', 'dim', 'repdim'],
                defaultParams = {
                    'plot_type': 'l',
                    'plot_xlab': 'Generation',
                    'plot_ylab': '',
                    'lines_lty': 1,
                    'legend_bty': 'n',
                    'legend_x': 'topright',
                },
                **kwargs
            )
        else:
            self.args = DerivedArgs(
                defaultFuncs = ['figure', 'plot'],
                allFuncs = ['figure', 'plot', 'set_title', 'set_xlabel',
                    'set_ylabel', 'set_ylim', 'legend'],
                suffixes = ['rep', 'dim', 'repdim'],
                defaultParams = {
                    'plot_linestyle': '-',
                    'set_xlabel_xlabel': 'Generation',
                    'set_ylabel_ylabel': '',
                    'set_title_label': '',
                },
                **kwargs
            )
        # internal flags
        self.nRep = 0
        self.reps = []   # allows specification of selected replicates
        self.nDim = 0
        self.lastPlot = 0
        self.min = None
        self.max = None
        # data
        self.gen = []
        self.data = []
        # when apply is called, self._rpy_plot is called.
        PyOperator.__init__(self, func=self._rpy_plot if use_rpy else self._mat_plot,
            begin=begin, end=end, step=step, at=at, reps=reps,
            subPops=ALL_AVAIL, infoFields=[])

    def __del__(self):
        # Close the device if needed.
        if use_rpy:
            if not self.leaveOpen and hasattr(self, 'device'):
                r.dev_off(self.device)
        else:
            if not self.leaveOpen:
                plt.close()

    def _pushData(self, gen, rep, data):
        '''Push history data to self.data for later retrieval. Set self.min and
        self.max along the way.
        '''
        # allocate a list for each replicate.
        while rep + 1 > len(self.data):
            self.data.append([])
        # append gen.
        if len(self.gen) == 0 or self.gen[-1] != gen:
            self.gen.append(gen)
        # check if data type and length are consistent, set self.nDim
        if type(data) in [type(()), type([])]:
            if self.nDim == 0:
                self.nDim = len(data)
            if self.nDim != len(data):
                raise RuntimeError('Data dimension is inconsistent.')
            if self.min is None or self.min > min(data):
                self.min = min(data)
            if self.max is None or self.max < max(data):
                self.max = max(data)
        elif self.nDim > 1:
            raise RuntimeError('Data dimension is inconsistent.')
        else:
            self.nDim = 1
            if self.min is None or self.min > data:
                self.min = data
            if self.max is None or self.max < data:
                self.max = data
        # append data
        self.data[rep].append(data)
        # check number of saved generations (self.win)
        if self.win > 0 and len(self.gen) > 1 and rep + 1 == len(self.data) \
            and self.gen[0] + self.win < gen:
            self.gen.pop(0)
            for d in self.data:
                if len(d) > 0:
                    d.pop(0)
        # set self.nRep
        if self.nRep == 0 and len(self.gen) > 1:
            self.reps = [x for x in range(len(self.data)) if len(self.data[x]) > 0]
            self.nRep = len(self.reps)

    def _getData(self, rep, dim = 0):
        "Get the dim'th element of the data of replicate rep"
        if type(self.data[rep][0]) in [type(()), type([])]:
            return [x[dim] for x in self.data[rep]]
        else:
            return self.data[rep]

    def _rpy_plot(self, pop):
        "Evaluate expression in pop and save result. Plot all data if needed"
        gen = pop.dvars().gen
        rep = pop.dvars().rep
        # push data 
        self._pushData(gen, rep, pop.evaluate(self.expr))
        # Draw a plot only when
        # 1. There are at least two obervations.
        # 2. rep is the last recorded replicate.
        # 3. we are self.update away from last plot.
        if len(self.gen) <= 1 or rep + 1 != len(self.data) or \
            (self.update >= 1 and gen < self.lastPlot + self.update):
            # do not plot
            return True
        else:
            self.lastPlot = gen
        # create a new graphical device if needed
        if not hasattr(self, 'device'):
            self.device = newDevice()
        else: # if there are multiple devices, set it back
            r.dev_set(self.device)
        # call the preHook function if given
        if self.preHook is not None:
            self.preHook(r)
        # figure out the dimension of data
        if self.nRep == 1:
            self.byRep = False
        if self.nDim == 1:
            self.byDim = False
        # needs subplots?
        nPlots = 1
        if self.byDim:
            nPlots *= self.nDim
        if self.byRep:
            nPlots *= self.nRep
        # try to use colors
        if self.nDim > 1 and not self.byDim:
            self.args.addDefault(col_dim=r.rainbow(self.nDim))
        if self.nRep > 1 and not self.byRep:
            self.args.addDefault(col_rep=r.rainbow(self.nRep))
        # suggest how to arrange subplots
        if nPlots > 1:
            nrow = int(ceil(sqrt(nPlots)))
            ncol = int(ceil(nPlots/float(nrow)))
            if nrow > ncol:
                nrow, ncol = ncol, nrow
            self.args.addDefault(par_mfrow=[nrow, ncol])
        # users might set additional parameters and override calculated mfrow.
        r.par(**self.args.getArgs('par', pop))
        # now plot.
        if self.byRep:
            # handle each replicate separately
            for rep_idx,rep in enumerate(self.reps):
                if self.byDim:
                    # separate plot for each dim
                    for dim in range(self.nDim):
                        data = self._getData(rep, dim)
                        r.plot(self.gen, data,
                            **self.args.getArgs('plot', pop, rep=rep_idx, dim=dim,
                                repdim=self.nDim*rep_idx + dim, ylim=[self.min, self.max]))
                        if self.plotHook is not None:
                            self.plotHook(r=r, gen=self.gen, data=data, rep=rep, dim=dim)
                else:
                    # all var in one subplot
                    data = self._getData(rep, 0)
                    r.plot(self.gen, data,
                        **self.args.getArgs('plot', pop, rep=rep_idx, dim=0,
                            repdim=self.nDim * rep_idx, ylim=[self.min, self.max]))
                    if self.plotHook is not None:
                        self.plotHook(r=r, gen=self.gen, data=data, rep=rep)
                    for dim in range(1, self.nDim):
                        r.lines(self.gen, self._getData(rep, dim),
                            **self.args.getArgs('lines', pop, rep=rep_idx, dim=dim,
                                repdim=self.nDim * rep_idx + dim))
                    if len(self.legend) > 0:
                        args = self.args.getLegendArgs('lines', pop, ['lty', 'col', 'lwd'],
                            'rep', range(self.nRep))
                        args.update(self.args.getArgs('legend', pop))
                        r.legend(legend=self.legend, **args)
        else:
            # all replicate in one figure
            if self.byDim:
                for dim in range(self.nDim):
                    data = self._getData(self.reps[0], dim)
                    r.plot(self.gen, data,
                        **self.args.getArgs('plot', pop, rep=self.reps[0], dim=dim, repdim=dim,
                            ylim=[self.min, self.max]))
                    if self.plotHook is not None:
                        self.plotHook(r=r, gen=self.gen, data=data, dim=dim)
                    for rep_idx,rep in enumerate(self.reps[1:]):
                        r.lines(self.gen, self._getData(rep, dim),
                            **self.args.getArgs('lines', pop, rep=rep_idx+1, dim=dim,
                                repdim=self.nDim * (rep_idx + 1) + dim))
                    if len(self.legend) > 0:
                        args = self.args.getLegendArgs('lines', pop, ['lty', 'col', 'lwd'],
                            'rep', range(self.nRep))
                        args.update(self.args.getArgs('legend', pop))
                        r.legend(legend=self.legend, **args)
            else:
                data = self._getData(0, 0)
                r.plot(self.gen, data,
                    **self.args.getArgs('plot', pop, rep=0, dim=0, repdim=0,
                        ylim=[self.min, self.max]))
                if self.plotHook is not None:
                    self.plotHook(r=r, gen=self.gen, data=data)
                for rep_idx,rep in enumerate(self.reps):
                    for dim in range(self.nDim):
                        r.lines(self.gen, self._getData(rep, dim),
                            **self.args.getArgs('lines', pop, rep=rep_idx, dim=dim,
                                repdim=self.nDim * rep_idx + dim))
                if len(self.legend) > 0:
                    args = self.args.getLegendArgs('lines', pop, ['lty', 'col', 'lwd'],
                        ['rep', 'dim'], [(x,y) for x in range(self.nRep) for y in range(self.nDim)])
                    args.update(self.args.getArgs('legend', pop))
                    r.legend(legend=self.legend, **args)
        # call the postHook function if given
        if self.postHook is not None:
            self.postHook(r)
        if self.saveAs != '':
            file, ext = os.path.splitext(self.saveAs)
            filename = '%s_%d%s' % (file, gen, ext)
            saveFigure(**self.args.getArgs('dev_print', pop, file=filename))
        return True

    def _mat_plot(self, pop):
        "Evaluate expression in pop and save result. Plot all data if needed"
        gen = pop.dvars().gen
        rep = pop.dvars().rep
        # push data 
        self._pushData(gen, rep, pop.evaluate(self.expr))
        # Draw a plot only when
        # 1. There are at least two obervations.
        # 2. rep is the last recorded replicate.
        # 3. we are self.update away from last plot.
        if len(self.gen) <= 1 or rep + 1 != len(self.data) or \
            (self.update >= 1 and gen < self.lastPlot + self.update):
            # do not plot
            return True
        else:
            self.lastPlot = gen
        # create a new graphical device if needed
        if not hasattr(self, 'device'):
            self.device = plt.figure(**self.args.getArgs('figure', pop))
        # call the preHook function if given
        if self.preHook is not None:
            self.preHook(self.device)
        # figure out the dimension of data
        if self.nRep == 1:
            self.byRep = False
        if self.nDim == 1:
            self.byDim = False
        # needs subplots?
        nPlots = 1
        if self.byDim:
            nPlots *= self.nDim
        if self.byRep:
            nPlots *= self.nRep
        # try to use colors
        if self.nDim > 1 and not self.byDim:
            cm = plt.get_cmap('gist_rainbow')
            self.args.addDefault(plot_c_dim=[cm(i*1.0/self.nDim) for i in range(self.nDim)])
        if self.nRep > 1 and not self.byRep:
            cm = plt.get_cmap('gist_rainbow')
            self.args.addDefault(plot_c_rep=[cm(i*1.0/self.nRep) for i in range(self.nRep)])
        # suggest how to arrange subplots
        if nPlots > 1:
            nrow = int(ceil(sqrt(nPlots)))
            ncol = int(ceil(nPlots/float(nrow)))
            if nrow > ncol:
                nrow, ncol = ncol, nrow
        #    self.args.addDefault(par_mfrow=[nrow, ncol])
        # users might set additional parameters and override calculated mfrow.
        #r.par(**self.args.getArgs('par', pop))
        # now plot.
        if self.byRep:
            # handle each replicate separately
            for rep_idx,rep in enumerate(self.reps):
                if self.byDim:
                    # separate plot for each dim
                    for dim in range(self.nDim):
                        data = self._getData(rep, dim)
                        ax = self.device.add_subplot(nrow, ncol, dim)
                        ax.set_xlabel(**self.args.getArgs('set_xlabel', pop, rep=rep_idx, dim=dim,
                                repdim=self.nDim*rep_idx + dim))
                        ax.set_ylabel(**self.args.getArgs('set_ylabel', pop, rep=rep_idx, dim=dim,
                                repdim=self.nDim*rep_idx + dim))
                        ax.set_title(**self.args.getArgs('set_title', pop, rep=rep_idx, dim=dim,
                                repdim=self.nDim*rep_idx + dim))
                        ax.plot(self.gen, data,
                            **self.args.getArgs('plot', pop, rep=rep_idx, dim=dim,
                                repdim=self.nDim*rep_idx + dim))
                        ax.set_ylim(self.min, self.max)
                        if self.plotHook is not None:
                            self.plotHook(ax, gen=self.gen, data=data, rep=rep, dim=dim)
                else:
                    # all var in one subplot
                    data = self._getData(rep, 0)
                    ax = self.device.add_subplot(nrow, ncol, rep_idx + 1)
                    ax.set_xlabel(**self.args.getArgs('set_xlabel', pop, rep=rep_idx))
                    ax.set_ylabel(**self.args.getArgs('set_ylabel', pop, rep=rep_idx))
                    ax.set_title(**self.args.getArgs('set_title', pop, rep=rep_idx))
                    handles = [
                        ax.plot(self.gen, data,
                            **self.args.getArgs('plot', pop, rep=rep_idx, dim=0,
                                repdim=self.nDim * rep_idx))[0]]
                    ax.set_ylim(self.min, self.max)
                    if self.plotHook is not None:
                        self.plotHook(ax, gen=self.gen, data=data, rep=rep)
                    for dim in range(1, self.nDim):
                        handles.append(ax.plot(self.gen, self._getData(rep, dim),
                            **self.args.getArgs('plot', pop, rep=rep_idx, dim=dim,
                                repdim=self.nDim * rep_idx + dim))[0])
                    if len(self.legend) > 0:
                        ax.legend(handles, self.legend, **self.args.getArgs('legend', pop))
        else:
            # all replicate in one figure
            if self.byDim:
                for dim in range(self.nDim):
                    data = self._getData(self.reps[0], dim)
                    ax = self.device.add_subplot(nrow, ncol, dim)
                    ax.set_xlabel(**self.args.getArgs('set_xlabel', pop, rep=self.reps[0],
                            dim=dim, repdim=dim))
                    ax.set_ylabel(**self.args.getArgs('set_ylabel', pop, rep=self.reps[0],
                            dim=dim, repdim=dim))
                    ax.set_title(**self.args.getArgs('set_title', pop, rep=self.reps[0],
                            dim=dim, repdim=dim))
                    handles = [
                        ax.plot(self.gen, data,
                            **self.args.getArgs('plot', pop, rep=self.reps[0],
                            dim=dim, repdim=dim))[0]]
                    ax.set_ylim(self.min, self.max)
                    if self.plotHook is not None:
                        self.plotHook(ax, gen=self.gen, data=data, dim=dim)
                    for rep_idx,rep in enumerate(self.reps[1:]):
                        handles.append(
                            ax.plot(self.gen, self._getData(rep, dim),
                                **self.args.getArgs('plot', pop, rep=rep_idx+1, dim=dim,
                                repdim=self.nDim * (rep_idx + 1) + dim))[0])
                    if len(self.legend) > 0:
                        ax.legend(handles, self.legend, **self.args.getArgs('legend', pop))
            else:
                data = self._getData(0, 0)
                ax = self.device.add_subplot(111)
                ax.set_xlabel(**self.args.getArgs('set_xlabel', pop))
                ax.set_ylabel(**self.args.getArgs('set_ylabel', pop))
                ax.set_title(**self.args.getArgs('set_title', pop))
                handles = [ax.plot(self.gen, data,
                    **self.args.getArgs('plot', pop, rep=0, dim=0, repdim=0))[0]]
                ax.set_ylim(self.min, self.max)
                if self.plotHook is not None:
                    self.plotHook(ax, gen=self.gen, data=data)
                for rep_idx,rep in enumerate(self.reps):
                    for dim in range(self.nDim):
                        handles.append(
                            ax.plot(self.gen, self._getData(rep, dim),
                            **self.args.getArgs('plot', pop, rep=rep_idx, dim=dim,
                                repdim=self.nDim * rep_idx + dim))[0])
                if len(self.legend) > 0:
                    ax.legend(handles, self.legend, **self.args.getArgs('legend', pop))
        # call the postHook function if given
        if self.postHook is not None:
            self.postHook(self.device)
        if self.saveAs != '':
            file, ext = os.path.splitext(self.saveAs)
            filename = '%s_%d%s' % (file, gen, ext)
            self.device.savefig(filename)
        return True


class ScatterPlotter(PyOperator):
    '''
    This class defines a Python operator that uses R to plot individuals in a
    Population, using values at two information fields as their x- and y-axis.

    Arbitrary keyword parameters could be specified and be passed to the
    underlying R drawing functions ``plot`` and ``points``. These parameters
    could be used to specify point type (``pch``), color (``col``),
    title (``main``), limit of x and y axes (``xlim`` and ``ylim``) and many
    other options (see R manual for details). You can also pass parameters
    to specific R functions such as ``par``, ``plot``, ``points``, ``legend``,
    ``pdf`` by prefixing parameter names with a function name. For example,
    ``par_mar=[1]*4`` will pass ``par=[1]*4`` to function ``par()`` which is
    called before a figure is drawn. (Note that the function to save a figure
    is ``dev.print`` so parameters such as ``dev_print_width`` should be
    used.) Further customization of your figures could be achieved by writing
    your own hook functions that will be called before and after a figure is
    drawn.

    The power of this operator lies in its ability to differentiate individuals
    from different (virtual) subpopulations. If you specify IDs of (virtual)
    subpopulations (VSPs) in parameter ``subPops``, only individuals from these
    VSPs will be displayed. Points from these subpopulations will be drawn
    with different shapes and colors. You can also customize these points
    using list parameters with suffix ``_sp``. For example, if you have defined
    two VSPs by sex and set ``subPops=[(0, 0), (0, 1)]``,
    ``col_sp=['blue', 'red']`` will color male individuals with blue and female
    individuals with red. In addition, if the value of a parameter is a string
    starting with ``!``, the evaluated result of the remaining string will be
    used as parameter value.

    This opertor calls R functions ``par``, ``plot``, ``points``, ``legend``,
    and ``dev.print``. Functions ``plot`` and ``points`` are the default
    destination for keyword arguments and the ones that accept list parameters
    to customize lines by (virtual) subpopulation.
    '''
    def __init__(self, infoFields=[], saveAs="", leaveOpen=False, legend=[], 
        preHook=None, postHook=None, begin=0, end=-1, step=1,
        at=[], reps=ALL_AVAIL, subPops=[], **kwargs):
        '''
        infoFields
            Two information fields whose values will be the x- and y-axis of
            each point (individual) in the plot.

        subPops
            A list of subpopulations and virtual subpopulations. Only
            individuals from these subpopulations will be plotted. Default
            to subpopulation indexes.

        saveAs
            Save figures in files saveAs_gen_rep.ext (e.g. ``figure_10_0.eps``
            if ``saveAs='figure.eps'``). If ext is given, a corresponding
            device will be used. Otherwise, a default postscript driver will be
            used. Currently supported formats include ``.pdf``, ``.png``,
            ``.bmp``, ``.jpg``, and ``.tif``. The default filename could be
            overriden by derived argument ``dev_print_file``.

        leaveOpen
            Whether or not leave the plot open when plotting is done. Default
            to ``False`` functions. If this option is set to ``True``, you will
            have to close the graphic device explicitly using function
            ``r.dev_off()``. Note that leaving the device open allows
            further manipuation of the figures outside of this operator.

        legend
            labels of the points. It must match the specified subpopulations.

        preHook
            A function that, if given, will be called before the figure is
            draw. The ``r`` object from the ``plotter`` module or the ``Figure``
            object from matplotlib will be passed to this function.

        postHook
            A function that, if given, will be called after the figure is
            drawn. The ``r`` object from the ``plotter`` module or the ``Figure``
            object from matplotlib will be passed to this function.

        kwargs
            Additional keyword arguments that will be interpreted and sent to
            underlying R functions. These arguments could have prefixes
            (destination function names) ``plot_``, ``points_``, ``par_``,
            ``legend_`` and ``dev_print_``, and suffixes (list parameters)
            ``_sp``. Arguments without prefixes are sent to functions
            ``plot`` and ``points``. String values with a leading ``!`` will be
            replaced by its evaluated result against the current population.
        '''
        # parameters
        self.infoFields = infoFields
        if len(self.infoFields) != 2:
            raise RuntimeError('Two information fields should be given')
        self.saveAs = saveAs
        self.leaveOpen = leaveOpen
        self.legend = legend
        self.preHook = preHook
        self.postHook = postHook
        self.subPops = subPops
        if use_rpy:
            self.args = DerivedArgs(
                defaultFuncs = ['plot', 'points'],
                allFuncs = ['par', 'plot', 'points', 'dev_print', 'legend'],
                suffixes = ['sp'],
                defaultParams = {
                    'legend_bty': 'n',
                    'plot_xlab': self.infoFields[0],
                    'plot_ylab': self.infoFields[1],
                    'legend_x': 'topright',
                },
                **kwargs)
        else:
            self.args = DerivedArgs(
                defaultFuncs = ['figure', 'plot'],
                allFuncs = ['figure', 'plot', 'scatter', 'set_title', 'set_xlabel',
                    'set_ylabel', 'set_ylim', 'legend'],
                suffixes = ['sp'],
                defaultParams = {
                    'plot_linestyle': '-',
                    'set_xlabel_xlabel': self.infoFields[0],
                    'set_ylabel_ylabel': self.infoFields[1],
                    'set_title_label': '',
                },
                **kwargs
            )

        if len(self.subPops) > 1:
            if use_rpy:
                self.args.addDefault(
                    pch_sp = range(1, len(self.subPops) + 1),
                    col_sp = r.rainbow(len(self.subPops)))
            else:
                cm = plt.get_cmap('gist_rainbow')
                self.args.addDefault(
                    scatter_c_sp=[cm(i*1.0/len(self.subPops)) for i in range(len(self.subPops))])
        # when apply is called, self._rpy_plot is called.
        PyOperator.__init__(self, func=self._rpy_plot if use_rpy else self._mat_plot,
            begin=begin, end=end, step=step, at=at, reps=reps)


    def __del__(self):
        # Close the device if needed.
        if not self.leaveOpen and hasattr(self, 'device'):
            r.dev_off(self.device)

    def _rpy_plot(self, pop):
        "Evaluate expression in pop and save result. Plot all data if needed"
        gen = pop.dvars().gen
        rep = pop.dvars().rep
        # create a new graphical device if needed
        if not hasattr(self, 'device'):
            self.device = newDevice()
        else: # if there are multiple devices, set it back
            r.dev_set(self.device)
        # call the preHook function if given
        if self.preHook is not None:
            self.preHook(r)
        # call par in case some parameter is provided
        parParam = self.args.getArgs('par', pop)
        if len(parParam) > 0:
            r.par(**parParam)
        #
        x = pop.indInfo(self.infoFields[0])
        y = pop.indInfo(self.infoFields[1])
        xlim = [min(x), max(x)]
        ylim = [min(y), max(y)]
        # if there is no subpopulation, easy
        if len(self.subPops) == 0:
            r.plot(x, y, 
                **self.args.getArgs('plot', pop, type='p', xlim=xlim, ylim=ylim))
        else:
            parPlot = self.args.getArgs('plot', pop, type='n', xlim=xlim, ylim=ylim)
            parPlot['type'] = 'n'
            r.plot(x[0], y[0], **parPlot)
            for idx,sp in enumerate(self.subPops):
                x = pop.indInfo(self.infoFields[0], sp)
                y = pop.indInfo(self.infoFields[1], sp)
                r.points(x, y, **self.args.getArgs('points', pop, sp=idx))
            # legend
            if len(self.legend) > 0:
                args = self.args.getLegendArgs('points', pop, ['col', 'pch', 'lwd', 'cex'],
                    'sp', range(len(self.subPops)))
                args.update(self.args.getArgs('legend', pop))
                r.legend(legend=self.legend, **args)
        # call the postHook function if given
        if self.postHook is not None:
            self.postHook(r)
        if self.saveAs != '':
            file, ext = os.path.splitext(self.saveAs)
            filename = '%s_%d_%d%s' % (file, gen, rep, ext)
            saveFigure(**self.args.getArgs('dev_print', pop, file=filename))
        return True

    def _mat_plot(self, pop):
        "Evaluate expression in pop and save result. Plot all data if needed"
        gen = pop.dvars().gen
        rep = pop.dvars().rep
        # create a new graphical device if needed
        if not hasattr(self, 'device'):
            self.device = plt.figure(**self.args.getArgs('figure', pop))
        # call the preHook function if given
        if self.preHook is not None:
            self.preHook(self.device)
        # call par in case some parameter is provided
        #parParam = self.args.getArgs('par', pop)
        #if len(parParam) > 0:
        #    r.par(**parParam)
        #
        x = pop.indInfo(self.infoFields[0])
        y = pop.indInfo(self.infoFields[1])
        xlim = [min(x), max(x)]
        ylim = [min(y), max(y)]
        # if there is no subpopulation, easy
        if len(self.subPops) == 0:
            ax = self.device.add_subplot(111)
            ax.plot(x, y, 
                **self.args.getArgs('plot', pop))
            ax.set_xlim(xlim[0], xlim[1])
            ax.set_ylim(ylim[0], ylim[1])
        else:
            #parPlot = self.args.getArgs('plot', pop, type='n', xlim=xlim, ylim=ylim)
            #parPlot['type'] = 'n'
            ax = self.device.add_subplot(111)
            ax.plot(x[0], y[0])
            ax.set_xlim(xlim[0], xlim[1])
            ax.set_ylim(ylim[0], ylim[1])
            handles = []
            for idx,sp in enumerate(self.subPops):
                x = pop.indInfo(self.infoFields[0], sp)
                y = pop.indInfo(self.infoFields[1], sp)
                handles.append(ax.scatter(x, y, **self.args.getArgs('scatter', pop, sp=idx)))
            # legend
            if len(self.legend) > 0:
                ax.legend(handles, self.legend,  **self.args.getArgs('legend', pop))
        # call the postHook function if given
        if self.postHook is not None:
            self.postHook(self.device)
        if self.saveAs != '':
            file, ext = os.path.splitext(self.saveAs)
            filename = '%s_%d_%d%s' % (file, gen, rep, ext)
            self.device.savefig(filename)
        return True

class InfoPlotter(PyOperator):
    '''
    This operator uses a R function such as ``hist`` and ``qqplot`` to plot
    properties of one or more information fields of individuals in one or more
    (virtual) subpopulations. Separate subplots are used for different
    information fields and subpopulations.

    This operator essentially gets values of information fields and sends them
    to a R function such as ``hist``. The resulting figures could be customized
    by additional keyword parameters and various hook functions. For example,
    a ``qqline`` function could be called in a ``plotHook`` function to add a
    QQ line to a ``qqnorm`` plot. The ``plotHook`` can be used to draw the
    whole (sub)plot if no R function is specified for parameter ``func``.
    
    Besides regular keyword parameters, keyword parameters ending in ``_sp``,
    ``_fld`` or ``_spfld`` are expected to have multiple values which will be
    used for differnt subpopulations, information fields, and their
    combinations. You can also specify which function the keyword should be
    sent by prefixing a function name to the parameter name. For example,
    ``pch_fld=[1, 2]`` will use different symbols for different information
    fields, and ``par_mar=[1]*4`` will send parameter ``mar=[1]*4`` to function
    ``par``. In addition, if the value of a parameter is a string starting with
    ``!``, the evaluated result of the remaining string will be used as
    parameter value.
    
    This opertor calls R functions ``par``, ``dev.print``, and a user-specified
    function. Additional keyword arguments without function prefix will be sent
    to this function.
    '''
    def __init__(self, func=None, infoFields=[], saveAs="", leaveOpen=False,
        preHook=None, postHook=None, plotHook = None, begin=0,
        end=-1, step=1, at=[], reps=ALL_AVAIL, subPops=[], **kwargs):
        '''
        func
            Name of the R or matplotlib function that will be called to draw figures
            from values of given information fields. No R function will be called
            if it is not specified. In this case, a ``plotHook`` can be used
            to plot passed values.

        infoFields
            Information fields whose values will be sent to the specified
            plotting function.

        subPops
            A list of subpopulations and virtual subpopulations. Each
            subpopulation will be plotted in a separate subplot.

        saveAs
            Save figures in files saveAs_gen_rep.ext (e.g. ``figure_10_0.eps``
            if ``saveAs='figure.eps'``). If ext is given, a corresponding
            device will be used. Otherwise, a default postscript driver will be
            used. Currently supported formats include ``.pdf``, ``.png``,
            ``.bmp``, ``.jpg``, and ``.tif``. The default filename could be
            overriden by derived argument ``dev_print_file``.

        leaveOpen
            Whether or not leave the plot open when plotting is done. Default
            to ``False`` functions. If this option is set to ``True``, you will
            have to close the graphic device explicitly using function
            ``r.dev_off()``. Note that leaving the device open allows
            further manipuation of the figures outside of this operator.

        preHook
            A function that, if given, will be called before the figure is
            draw. The ``r`` object for ``rpy`` will be passed to this function.

        postHook
            A function that, if given, will be called after the figure is
            drawn.  The ``r`` object for ``rpy`` will be passed to this function.

        plotHook
            A function that, if given, will be called after each ``plot``
            function. The ``r`` object from the ``rpy`` module  , data being
            plotted, name of the information field and index of subpopulation
            (in parameter ``subPops``, if applicable) will be passed with
            keywords ``r``, ``data``, ``field`` and ``subPop`` (optional)
            respectively.

        kwargs
            Additional keyword arguments that will be interpreted and sent to
            underlying R functions. These arguments could have prefixes
            (destination function names) ``par_``, ``dev_print_`` and the
            function you specify (parameter ``func``), and suffixes (list
            parameters) ``_sp``, ``_fld``, and ``_spfld``. Arguments without
            prefixes are sent to the user specified function. String values
            with a leading ``!`` will be replaced by its evaluated result
            against the current population.
        '''
        # parameters
        if type(infoFields) == type(''):
            self.infoFields = [infoFields]
        else:
            self.infoFields = infoFields
        self.func = func
        if len(self.infoFields) == 0:
            raise RuntimeError('At least one information field should be given')
        self.saveAs = saveAs
        self.leaveOpen = leaveOpen
        self.preHook = preHook
        self.postHook = postHook
        self.plotHook = plotHook
        self.subPops = subPops
        if use_rpy:
            if self.func is not None:
                self.rfunc = r(self.func)
            self.args = DerivedArgs(
                defaultFuncs = [] if self.func is None else [self.func],
                allFuncs = ['par', 'dev_print', 'legend'] + ([] if self.func is None else [self.func]),
                suffixes = ['sp', 'fld', 'spfld'],
                defaultParams = {'legend_x': 'topright'},
                **kwargs)
        else:
            raise RuntimeError('InfoPlotter does not yet support matplotlib plotter')
        # when apply is called, self._rpy_plot is called.
        PyOperator.__init__(self, func=self._rpy_plot,
            begin=begin, end=end, step=step, at=at, reps=reps)


    def __del__(self):
        # Close the device if needed.
        if use_rpy:
            if not self.leaveOpen and hasattr(self, 'device'):
                r.dev_off(self.device)
        else:
            if not self.leaveOpen:
                plt.close()

    def _rpy_plot(self, pop):
        "Evaluate expression in pop and save result. Plot all data if needed"
        gen = pop.dvars().gen
        rep = pop.dvars().rep
        # create a new graphical device if needed
        if not hasattr(self, 'device'):
            self.device = newDevice()
        else: # if there are multiple devices, set it back
            r.dev_set(self.device)
        # call the preHook function if given
        if self.preHook is not None:
            self.preHook(r)
        # subplots?
        nPlots = len(self.infoFields)
        if len(self.subPops) > 1:
            nPlots *= len(self.subPops)
        # call par in case some parameter is provided
        if nPlots > 1:
            nrow = int(ceil(sqrt(nPlots)))
            ncol = int(ceil(nPlots/float(nrow)))
            if nrow > ncol:
                nrow, ncol = ncol, nrow
            self.args.addDefault(par_mfrow=[nrow, ncol])
        #
        r.par(**self.args.getArgs('par', pop))
        #
        for fldIdx,fld in enumerate(self.infoFields):
            # if there is no subpopulation, easy
            if len(self.subPops) == 0:
                val = pop.indInfo(fld)
                if self.func is not None:
                    self.rfunc(val, **self.args.getArgs(self.func, pop, fld=fldIdx, sp=0,
                        spfld=fldIdx, main='%s at gen %d' % (fld, gen), xlab=fld, ylab=self.func))
                if self.plotHook is not None:
                    self.plotHook(r=r, data=val, field=fld)
            else:
                for spIdx,sp in enumerate(self.subPops):
                    val = pop.indInfo(fld, sp)
                    if self.func is not None:
                        self.rfunc(val, **self.args.getArgs(self.func, pop,
                            fld=fldIdx, sp=spIdx, spfld=len(self.infoFields)*spIdx + fldIdx,
                            main='%s in %s at gen %d' % (fld, pop.subPopName(sp), gen),
                            xlab=fld, ylab=self.func))
                    if self.plotHook is not None:
                        self.plotHook(r=r, data=val, field=fld, subPop=sp)
        # call the postHook function if given
        if self.postHook is not None:
            self.postHook(r)
        if self.saveAs != '':
            file, ext = os.path.splitext(self.saveAs)
            filename = '%s_%d_%d%s' % (file, gen, rep, ext)
            saveFigure(**self.args.getArgs('dev_print', pop, file=filename))
        return True

class HistPlotter(InfoPlotter):
    '''An ``InfoPlotter`` that uses function ``hist``.'''
    def __init__(self, *args, **kwargs):
        '''Returns an ``InfoPlotter`` that uses R function ``hist`` to draw
        histogram of individual information fields of specified (virtual)
        subpopulations. Please see ``InfoPlotter`` for details.
        '''
        InfoPlotter.__init__(self, 'hist', *args, **kwargs)


class QQPlotter(InfoPlotter):
    '''An ``InfoPlotter`` that uses function ``qqnorm``.'''
    def __init__(self, *args, **kwargs):
        '''Returns an ``InfoPlotter`` that uses R function ``qqnorm`` to draw
        qq plot of individual information fields of specified (virtual)
        subpopulations. Please see ``InfoPlotter`` for details.
        '''
        InfoPlotter.__init__(self, 'qqnorm', *args, **kwargs)


class BoxPlotter(PyOperator):
    '''
    This operator draws boxplots of one or more information fields of
    individuals in one or more (virtual) subpopulations of a population.
    Although a ``InfoPlotter`` with ``func=boxplot`` could be used to plot
    boxplots for each information field and/or subpopulation, this class allows
    multiple whiskers to share one plot. How the whiskers are oraganized is
    controlled by parameters ``byField`` and ``bySubPop``.
    
    This operator essentially gets values of information fields and sends them
    to boxplots. Individual ownerships (subpopulation or field) are also passed
    so that multiple whiskers could be drawn in the same plot. The resulting
    figures could be customized by additional keyword parameters and various
    hook functions.
    
    Besides regular keyword parameters, keyword parameters ending in ``_sp``,
    ``_fld`` or ``_spfld`` are expected to have multiple values which will be
    used for differnt subpopulations, information fields, and their
    combinations. You can also specify which function the keyword should be
    sent by prefixing a function name to the parameter name. For example,
    ``pch_fld=[1, 2]`` will use different symbols for different information
    fields, and ``par_mar=[1]*4`` will send parameter ``mar=[1]*4`` to function
    ``par``. In addition, if the value of a parameter is a string starting with
    ``!``, the evaluated result of the remaining string will be used as
    parameter value.
 
    This opertor calls R functions ``par``, ``boxplot`` and ``dev.print``.
    Keyword parameters without function prefix will be passed to ``boxplot``.
    '''
    def __init__(self, infoFields=[], byField=False, bySubPop=False, saveAs="",
        leaveOpen=False, preHook=None, postHook=None, plotHook = None,
        begin=0, end=-1, step=1, at=[], reps=ALL_AVAIL, subPops=[], **kwargs):
        '''
        infoFields
            Information fields whose values will be sent to R function
            ``boxplot``.

        subPops
            A list of subpopulations and virtual subpopulations. Separate
            whiskers will be drawn for individuals in these subpopulations.

        byField
            If multiple information fields are specified, separate the whiskers
            different subplots if this parameter is ``True``.
        
        bySubPop
            If multiple (virtual) subpopulations are specified, separate the
            whiskers to different subplots if this parameter is ``True``.

        saveAs
            Save figures in files saveAs_gen_rep.ext (e.g. ``figure_10_0.eps``
            if ``saveAs='figure.eps'``). If ext is given, a corresponding
            device will be used. Otherwise, a default postscript driver will be
            used. Currently supported formats include ``.pdf``, ``.png``,
            ``.bmp``, ``.jpg``, and ``.tif``. The default filename could be
            overriden by derived argument ``dev_print_file``.

        leaveOpen
            Whether or not leave the plot open when plotting is done. Default
            to ``False`` functions. If this option is set to ``True``, you will
            have to close the graphic device explicitly using function
            ``r.dev_off()``. Note that leaving the device open allows
            further manipuation of the figures outside of this operator.

        preHook
            A function that, if given, will be called before the figure is
            draw. The ``r`` object for ``rpy`` will be passed to this function.

        postHook
            A function that, if given, will be called after the figure is
            drawn.  The ``r`` object for ``rpy`` will be passed to this function.

        plotHook
            A function that, if given, will be called after each ``plot``
            function. The ``r`` object from the ``rpy`` module, current field
            and subpopulation will be passed with keywords ``r``, ``field`` and
            ``subPop`` if applicable.

        kwargs
            Additional keyword arguments that will be interpreted and sent to
            underlying R functions. These arguments could have prefixes
            (destination function names) ``plot_``, ``boxplot_``, ``par_``,
            and ``dev_print_``, and suffixes (list parameters) ``_sp``,
            ``_fld`` and ``_spfld``. Arguments without prefixes are sent to
            function ``boxplot``. String values with a leading ``!`` will be
            replaced by its evaluated result against the current population.
        '''
        # parameters
        if type(infoFields) == type(''):
            self.infoFields = [infoFields]
        else:
            self.infoFields = infoFields
        if len(self.infoFields) == 0:
            raise RuntimeError('At least one information field should be given')
        if not use_rpy:
            raise RuntimeError('BoxPlotter function does not support matplotlib plotter')
        self.saveAs = saveAs
        self.leaveOpen = leaveOpen
        self.preHook = preHook
        self.postHook = postHook
        self.plotHook = plotHook
        self.subPops = subPops
        self.byField = byField
        if len(self.infoFields) == 1:
            self.byField = False
        self.bySubPop = bySubPop
        if len(self.subPops) <= 1:
            self.bySubPop = False
        self.args = DerivedArgs(
            defaultFuncs = ['boxplot'],
            allFuncs = ['par', 'boxplot', 'dev_print', 'legend'],
            suffixes = ['sp', 'fld', 'spfld'],
            defaultParams = {'legend_x': 'topright'},
            **kwargs)
        # when apply is called, self.plot is called, additional keyword
        # parameters are passed by kwargs.
        PyOperator.__init__(self, func=self._rpy_plot, begin=begin, end=end,
            step=step, at=at, reps=reps)

    def __del__(self):
        # Close the device if needed.
        if not self.leaveOpen and hasattr(self, 'device'):
            r.dev_off(self.device)

    def _rpy_plot(self, pop):
        "Evaluate expression in pop and save result. Plot all data if needed"
        gen = pop.dvars().gen
        rep = pop.dvars().rep
        # create a new graphical device if needed
        if not hasattr(self, 'device'):
            self.device = newDevice()
        else: # if there are multiple devices, set it back
            r.dev_set(self.device)
        # call the preHook function if given
        if self.preHook is not None:
            self.preHook(r)
        # subplots?
        nPlots = 1
        if len(self.infoFields) > 1 and self.byField:
            nPlots *= len(self.infoFields)
        if len(self.subPops) > 1 and self.bySubPop:
            nPlots *= len(self.subPops)
        # call par in case some parameter is provided
        if nPlots > 1:
            nrow = int(ceil(sqrt(nPlots)))
            ncol = int(ceil(nPlots/float(nrow)))
            if nrow > ncol:
                nrow, ncol = ncol, nrow
            self.args.addDefault(par_mfrow=[nrow, ncol])
        #
        r.par(**self.args.getArgs('par', pop))
        #
        if self.byField:
            for fldIdx,fld in enumerate(self.infoFields):
                if self.bySubPop:
                    # multiple Field and subpop, each has its own subplot
                    for spIdx,sp in enumerate(self.subPops):
                        val = pop.indInfo(fld, sp)
                        r.boxplot(val, **self.args.getArgs('boxplot', pop,
                            fld=fld, sp=sp, spfld=len(self.infoFields)*spIdx + fldIdx,
                            main='%s in %s at gen %d' % (fld, pop.subPopName(sp), gen)))
                        if self.plotHook is not None:
                            self.plotHook(r=r, field=fld, subPop=spIdx)
                else:
                    # combine data
                    data = []
                    owner = []
                    if len(self.subPops) == 0:
                        data = pop.indInfo(fld)
                        owner = [fld]*len(data)
                    else:
                        for spIdx,sp in enumerate(self.subPops):
                            spData = pop.indInfo(fld, sp)
                            data.extend(spData)
                            owner.extend([pop.subPopName(sp)]*len(spData))
                    #
                    r.boxplot(r('data ~ owner'), data=r.data_frame(data=data, owner=owner),
                        **self.args.getArgs('boxplot', pop, fld=fldIdx,
                        main='Field %s at gen %d' % (fld, gen)))
                    if self.plotHook is not None:
                        self.plotHook(r=r, field=fld)
        elif not self.byField and self.bySubPop:
            for spIdx,sp in enumerate(self.subPops):
                # combine data
                data = []
                owner = []
                for fldIdx,fld in enumerate(self.infoFields):
                    fldData = pop.indInfo(fld, sp)
                    data.extend(fldData)
                    owner.extend([fld]*len(fldData))
                #
                r.boxplot(r('data ~ owner'), data=r.data_frame(data=data, owner=owner),
                    **self.args.getArgs('boxplot', pop, sp=spIdx,
                        main='Subpop %s at gen %d' % (pop.subPopName(sp), gen)))
                if self.plotHook is not None:
                    self.plotHook(r=r, subPop=sp)
        else:
            # everything in one plot.
            data = []
            owner = []
            for fldIdx,fld in enumerate(self.infoFields):
                if len(self.subPops) == 0:
                    data.extend(pop.indInfo(fld))
                    owner.extend([fld]*pop.popSize())
                    continue
                # multiple subpopulations
                for spIdx,sp in enumerate(self.subPops):
                    spData = pop.indInfo(fld, sp)
                    data.extend(spData)
                    if len(self.infoFields) == 1:
                        owner.extend([pop.subPopName(sp)]*len(spData))
                    else:
                        owner.extend(['%s, %s' % (fld, pop.subPopName(sp))]*len(spData))
            #
            r.boxplot(r("data ~ owner"), data=r.data_frame(data=data, owner=owner),
                **self.args.getArgs('boxplot', pop))
            if self.plotHook is not None:
                self.plotHook(r=r)
        # call the postHook function if given
        if self.postHook is not None:
            self.postHook(r)
        if self.saveAs != '':
            file, ext = os.path.splitext(self.saveAs)
            filename = '%s_%d_%d%s' % (file, gen, rep, ext)
            saveFigure(**self.args.getArgs('dev_print', pop, file=filename))
        return True

