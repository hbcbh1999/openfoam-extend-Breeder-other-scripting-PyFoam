#  ICE Revision: $Id: PotentialRunner.py 9555 2008-10-21 08:22:51Z bgschaid $ 
"""
Application class that implements pyFoamSteadyRunner
"""

from os import path,environ
from optparse import OptionGroup

from PyFoamApplication import PyFoamApplication

from PyFoam.Execution.BasicRunner import BasicRunner
from PyFoam.RunDictionary.SolutionDirectory import SolutionDirectory

from PyFoam.Error import warning,error

from PyFoam.FoamInformation import oldAppConvention as oldApp

from CommonParallel import CommonParallel
from CommonStandardOutput import CommonStandardOutput

class PotentialRunner(PyFoamApplication,
                      CommonStandardOutput,
                      CommonParallel):
    def __init__(self,args=None):
        description="""
Runs the potentialFoam solver on a case to get a decent initial condition.

Copies the current fields for U and p to backup-files.
        """

        PyFoamApplication.__init__(self,
                                   args=args,
                                   description=description,
                                   usage="%prog [options] <caseDirectory>",
                                   interspersed=True,
                                   nr=1)

    def addOptions(self):
        pot=OptionGroup(self.parser,
                        "Solver settings",
                        "Basic settings for the potentialFoam-solver")
        
        pot.add_option("--non-orthogonal-correctors",
                       type="int",
                       dest="noCorr",
                       default=None,
                       help="The number of non-orthogonal corrections")
        pot.add_option("--tolerance",
                       type="float",
                       dest="tolerance",
                       default=None,
                       help="Overwrite the tolerance of the linear solver")
        pot.add_option("--relTol",
                       type="float",
                       dest="relTol",
                       default=None,
                       help="Overwrite the relative tolerance of the linear solver")
        pot.add_option("--no-write-p",
                       action="store_false",
                       dest="writep",
                       default=True,
                       help="Don't write pressure p")
        pot.add_option("--pRefCell",
                       type="int",
                       dest="pRefCell",
                       default=None,
                       help="Sets the number of the reference cell for closed cases")
        pot.add_option("--pRefValue",
                               type="int",
                               dest="pRefValue",
                               default=None,
                               help="Sets the pressure reference value for closed cases")
        self.parser.add_option_group(pot)
        
        CommonParallel.addOptions(self)
        CommonStandardOutput.addOptions(self)
        
    def run(self):
        cName=self.parser.getArgs()[0]
        sol=SolutionDirectory(cName,archive=None)
        initial=sol[0]
        if "U" not in initial or "p" not in initial:
            error("Either 'p' or 'U' missing from the initial directory",initial.baseName())
        if self.opts.writep:
            initial["p.prepotential"]=initial["p"]
        initial["U.prepotential"]=initial["U"]
        
        lam=self.getParallel()

        if self.opts.writep:
            writep=["-writep"]
        else:
            writep=[]

        argv=["potentialFoam"]
        if oldApp():
            argv+=[".",cName]
        else:
            argv+=["-case",cName]
        
        self.setLogname(default="Potential",useApplication=False)
            
        run=BasicRunner(argv=argv+writep,
                        server=False,
                        logname=self.opts.logname,
                        silent=self.opts.progress,
                        lam=lam)

        print "Setting system-directory for potentialFoam"
        trig=PotentialTrigger(sol,
                              self.opts.noCorr,
                              self.opts.tolerance,
                              self.opts.relTol,
                              pRefCell=self.opts.pRefCell,
                              pRefValue=self.opts.pRefValue)
        run.addEndTrigger(trig.resetIt)

        run.start()

import re
from PyFoam.RunDictionary.ParsedParameterFile import ParsedParameterFile

class PotentialTrigger:
    def __init__(self,sol,correctors,tolerance,relTol,pRefValue=None,pRefCell=None):
        self.solution=ParsedParameterFile(path.join(sol.systemDir(),"fvSolution"),backup=True)
        self.schemes=ParsedParameterFile(path.join(sol.systemDir(),"fvSchemes"),backup=True)
        self.control=ParsedParameterFile(path.join(sol.systemDir(),"controlDict"),backup=True)
        pot=SolutionDirectory(path.join(environ["FOAM_TUTORIALS"],"potentialFoam","cylinder"),archive=None,paraviewLink=False)
        
        self.fresh=True
        
        try:
            if "SIMPLE" not in self.solution:
                self.solution["SIMPLE"]=ParsedParameterFile(path.join(pot.systemDir(),"fvSolution"),backup=False)["SIMPLE"]

            if "nNonOrthogonalCorrectors" not in self.solution["SIMPLE"] and correctors==None:
                correctors=3
                warning("Setting number of correctors to default value",correctors)
            if correctors!=None:
                self.solution["SIMPLE"]["nNonOrthogonalCorrectors"]=correctors

            if pRefCell!=None:
                self.solution["SIMPLE"]["pRefCell"]=pRefCell
            if pRefValue!=None:
                self.solution["SIMPLE"]["pRefValue"]=pRefValue
                
            if tolerance!=None:
                self.solution["solvers"]["p"][1]["tolerance"]=tolerance
            if relTol!=None:
                self.solution["solvers"]["p"][1]["relTol"]=relTol
                
            self.schemes.content=ParsedParameterFile(path.join(pot.systemDir(),"fvSchemes"),backup=False).content
            self.control.content=ParsedParameterFile(path.join(pot.systemDir(),"controlDict"),backup=False).content
            
            self.solution.writeFile()
            self.schemes.writeFile()
            self.control.writeFile()
        except Exception,e:
            warning("Restoring defaults")
            self.solution.restore()
            self.schemes.restore()
            self.control.restore()
            raise e
        
    def resetIt(self):
        if self.fresh:
            warning("Trigger called: Resetting fvSchemes and fvSolution")
            self.solution.restore()
            self.schemes.restore()
            self.control.restore()
            self.fresh=False