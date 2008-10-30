#  ICE Revision: $Id: PlotWatcher.py 9424 2008-09-22 08:00:35Z bgschaid $ 
"""
Class that implements pyFoamPlotWatcher
"""

from PyFoam.Execution.GnuplotRunner import GnuplotWatcher

from PyFoamApplication import PyFoamApplication

from CommonPlotLines import CommonPlotLines
from CommonPlotOptions import CommonPlotOptions

from os import path
from optparse import OptionGroup

class PlotWatcher(PyFoamApplication,
                  CommonPlotOptions,
                  CommonPlotLines):
    def __init__(self,args=None):
        description="""
        Gets the name of a logfile which is assumed to be the output of a
        OpenFOAM-solver. Parses the logfile for information about the
        convergence of the solver and generates gnuplot-graphs. Watches the
        file until interrupted.
        """

        CommonPlotOptions.__init__(self,persist=False)
        CommonPlotLines.__init__(self)
        PyFoamApplication.__init__(self,
                                   args=args,
                                   description=description,
                                   usage="%prog [options] <logfile>",
                                   changeVersion=False,
                                   interspersed=True,
                                   nr=1)

    def addOptions(self):
        CommonPlotOptions.addOptions(self)

        output=OptionGroup(self.parser,
                           "Output",
                           "What should be output to the terminal")
        self.parser.add_option_group(output)
        
        output.add_option("--tail",
                          type="long",
                          dest="tail",
                          default=5000L,
                          help="The length at the end of the file that should be output (in bytes. Default: %default)")
        output.add_option("--silent",
                          action="store_true",
                          dest="silent",
                          default=False,
                          help="Logfile is not copied to the terminal")
        output.add_option("--progress",
                          action="store_true",
                          default=False,
                          dest="progress",
                          help="Only prints the progress of the simulation, but swallows all the other output")

        limit=OptionGroup(self.parser,
                          "Limits",
                          "Where the plots should start and end")
        self.parser.add_option_group(limit)
        
        limit.add_option("--start",
                         action="store",
                         type="float",
                         default=None,
                         dest="start",
                         help="Start time starting from which the data should be plotted. If undefined the initial time is used")

        limit.add_option("--end",
                         action="store",
                         type="float",
                         default=None,
                         dest="end",
                         help="End time until which the data should be plotted. If undefined it is plotted till the end")

        CommonPlotLines.addOptions(self)
                
    def run(self):
        self.processPlotOptions()
        self.processPlotLineOptions(autoPath=path.dirname(self.parser.getArgs()[0]))

        run=GnuplotWatcher(self.parser.getArgs()[0],
                           smallestFreq=self.opts.frequency,
                           persist=self.opts.persist,
                           tailLength=self.opts.tail,
                           silent=self.opts.silent,
                           plotLinear=self.opts.linear,
                           plotCont=self.opts.cont,
                           plotBound=self.opts.bound,
                           plotIterations=self.opts.iterations,
                           plotCourant=self.opts.courant,
                           plotExecution=self.opts.execution,
                           plotDeltaT=self.opts.deltaT,
                           customRegexp=self.plotLines(),
                           writeFiles=self.opts.writeFiles,
                           raiseit=self.opts.raiseit,
                           progress=self.opts.progress,
                           start=self.opts.start,
                           end=self.opts.end)

        run.start()