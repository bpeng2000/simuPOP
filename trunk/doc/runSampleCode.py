#!/usr/bin/env python
#
# $File: runSampleCode.py $
# $LastChangedDate: 2009-09-05 13:56:43 -0500 (Sat, 05 Sep 2009) $
# $Rev: 2894 $
#
# This file is part of simuPOP, a forward-time population genetics
# simulation environment. Please visit http://simupop.sourceforge.net
# for details.
#
# Copyright (C) 2004 - 2009 Bo Peng (bpeng@mdanderson.org)
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

#
# This script get a filename from sys.argv[1], open and run it as if in an
# interactive session. The output is separated according to special comments
# in the output file. Allowed intructions are
#
# * logging output between these two lines to a filename
#   #file filename
#   #end
#
# * execute, but do not write the output between these two lines
#   #beginignore
#   #end
# 
# * expect error so do not stop when an error happens
#   #expecterror

import code, sys, os, re, tempfile

#  run a script interatively
class runScriptInteractively(code.InteractiveConsole):
    def __init__(self, locals=None, filename="<console>", file = None):
        self.file = file or open(filename)
        code.InteractiveConsole.__init__(self, locals, filename)

    def raw_input(self, prompt):
        l = self.file.readline()
        if l == '':
            raise EOFError
        sys.stdout.write(prompt + l)
        return l.strip("\n")

# do not stop on help() function since stdin is then no longer
# a terminal.
class wrapper:
  def __init__(self, file):
    self.file = file
  def isatty(self):
    return 0
  def __getattr__(self, key):
    return getattr(self.file, key)

def runScript(inputFile, outputFile):
    '''Run a script and return its output as a list of strings'''
    # out to a file
    #
    oldIn = sys.stdin
    oldOut = sys.stdout
    oldErr = sys.stderr
    #
    # set stdin, stderr, stdout
    outFile = open(outputFile, 'w')
    sys.stdin = wrapper(sys.stdin)
    sys.stderr = outFile
    sys.stdout = outFile
    #
    b = runScriptInteractively(locals=locals(), filename = inputFile)
    b.interact(None)
    #
    # reset io streams
    sys.stdin = oldIn
    sys.stdout = oldOut
    sys.stderr = oldErr
    #
    outFile.close()

def writeFile(content, srcFile, logFile=False):
    dir = os.path.split(srcFile)[0]
    if dir != '' and not os.path.isdir(dir):
        os.mkdir(dir)
    #
    src = open(srcFile, 'w')
    ignore = False
    expect_error = False
    start = not logFile
    for line in content:
        if logFile and line.startswith('>>>'):
            start = True
        if not start:
            continue
        if line.startswith('#beginignore') or line.startswith('>>> #beginignore'):
            ignore = True
        elif line.startswith('#endignore') or line.startswith('>>> #endignore'):
            ignore = False
        elif line.startswith('#expecterror') or line.startswith('>>> #expecterror'):
            expect_error = True
        elif line == '>>> ':
            continue
        elif not ignore:
            print >> src, line,
    # if there is error
    if not expect_error and True in ['Error' in x for x in content]:
        print
        print 'An Error occured in log file %s ' % srcFile
        print "If this is expected, please add '#expecterror' in your source code."
        print
        print ''.join(content)
        print
        sys.exit(1)
    src.close()


def runSampleCode(srcFile):
    begin_re = re.compile('^#file\s*(.*)')
    end_re = re.compile('^#end\s*$')
    #
    src = open(srcFile, 'r')
    tmpSrc = tmpSrcName = None
    filename = None
    for lineno, line in enumerate(src.readlines()):
        if begin_re.match(line):
            filename = begin_re.match(line).groups()[0].strip()
            tmp, tmpSrcName = tempfile.mkstemp()
            tmpSrc = open(tmpSrcName, 'w')
        elif end_re.match(line):
            if tmpSrc is None:
                print 'ERROR (line %d): %s' % (lineno, line)
                sys.exit(1)
            #
            print 'Processing %s...' % filename,
            sys.stdout.flush()
            tmpSrc.close()
            tmpSrc = None
            tmp, tmpLogName = tempfile.mkstemp()
            runScript(tmpSrcName, tmpLogName)
            #
            writeFile(open(tmpSrcName).readlines(), filename)
            logFile = filename.replace('.py', '.log')
            writeFile(open(tmpLogName).readlines(), logFile, True)
            print ' done.'
        else:
            if tmpSrc is not None:
                print >> tmpSrc, line,
            elif line.strip() != '' and not line.startswith('#'):
                print 'Unprocessed:', line
    src.close()

if __name__ == '__main__':
    if len(sys.argv) < 2 or sys.argv[1] == '-h' or not os.path.isfile(sys.argv[1]):
        print 'Usage: runSampleCode scriptToRun'
        print '    -h: view this help information'
        sys.exit(0)
    #
    runSampleCode(sys.argv[1])

