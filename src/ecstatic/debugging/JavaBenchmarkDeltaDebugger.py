#  ECSTATIC: Extensible, Customizable STatic Analysis Tester Informed by Configuration
#
#  Copyright (c) 2022.
#
#  This program is free software: you can redistribute it and/or modify
#      it under the terms of the GNU General Public License as published by
#      the Free Software Foundation, either version 3 of the License, or
#      (at your option) any later version.
#
#      This program is distributed in the hope that it will be useful,
#      but WITHOUT ANY WARRANTY; without even the implied warranty of
#      MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#      GNU General Public License for more details.
#
#      You should have received a copy of the GNU General Public License
#      along with this program.  If not, see <https://www.gnu.org/licenses/>.

import logging
import os.path
import dill as pickle
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from functools import partial
from multiprocessing import Pool
from pathlib import Path
from typing import Iterable, Optional, List, Any

from src.ecstatic.readers import ReaderFactory
from src.ecstatic.runners import RunnerFactory
from src.ecstatic.runners.AbstractCommandLineToolRunner import AbstractCommandLineToolRunner
from src.ecstatic.util.BenchmarkReader import validate
from src.ecstatic.util.PotentialViolation import PotentialViolation
from src.ecstatic.util.UtilClasses import FinishedFuzzingJob
from src.ecstatic.util.Violation import Violation
from src.ecstatic.violation_checkers import ViolationCheckerFactory
from src.ecstatic.violation_checkers.AbstractViolationChecker import get_file_name

logger = logging.getLogger(__name__)


@dataclass
class DeltaDebuggingResult:
    result: bool
    output: str


class JavaBenchmarkDeltaDebugger:

    def __init__(self, artifacts_folder: str, tool: str, task: str, groundtruths: str = None,
                 whole_program: bool = False):
        self.artifacts_folder = artifacts_folder
        self.tool = tool
        self.task = task
        self.groundtruths = groundtruths
        self.whole_program = whole_program

    def delta_debug(self, potential_violation: PotentialViolation, campaign_directory: str, timeout: Optional[int]) \
            -> Optional[DeltaDebuggingResult]:
        """

        Parameters
        ----------
        violation

        Returns
        -------
        True if the delta debugging failed. False otherwise.
        @param potential_violation:
        @param timeout:
        @param campaign_directory:
        """
        if "eclipse" in os.path.basename(potential_violation.job1.job.target.name):
            return None
        # First, create artifacts. We need to pickle the violation, as well as creating the script.
        delta_debugging_base_directory = os.path.abspath(os.path.join(campaign_directory, 'deltadebugging',
                                                                      os.path.dirname(get_file_name(potential_violation)),
                                                                      os.path.basename(potential_violation.job1.job.target.name)))
        print(f"Making delta debugging directory {delta_debugging_base_directory}")
        for ix, edge in potential_violation.expected_diffs:
            delta_debugging_directory = os.path.join(delta_debugging_base_directory, ix)
            if os.path.exists(os.path.join(delta_debugging_directory, "log.txt")):
                logger.critical(
                    f'Delta debugging result {os.path.join(delta_debugging_directory, "log.txt")} already exists. Not removing. Skipping this violation.')
                return None
            if os.path.exists(delta_debugging_directory):
                logger.info("Ignoring existing result")
                shutil.rmtree(delta_debugging_directory, ignore_errors=True)
            Path(delta_debugging_directory).mkdir(exist_ok=True, parents=True)

            # Copy benchmarks folder so that we have our own code location.
            shutil.copytree(src="benchmarks", dst=os.path.join(delta_debugging_directory, "benchmarks"))
            potential_violation.job1.job.target = validate(potential_violation.job1.job.target, delta_debugging_directory)
            logging.info(f'Moved benchmark, so target is now {potential_violation.job1.job.target}')
            potential_violation.job2.job.target = potential_violation.job1.job.target
            try:
                if len(potential_violation.job1.job.target.sources) == 0:
                    logging.critical(f"Cannot delta debug benchmark record {potential_violation.job1.job.target} without sources.")
                    return None
            except TypeError:
                logging.exception(potential_violation.job1.job.target)

            # Then, create the script.
            script_location = self.create_script(potential_violation, edge, delta_debugging_directory, timeout)
            build_script = potential_violation.job1.job.target.build_script
            os.chmod(build_script, 700)
            os.chmod(script_location, 700)

            # Then, run the delta debugger
            cmd: List[str] = "java -jar /SADeltaDebugger/ViolationDeltaDebugger/target/ViolationDeltaDebugger-1.0" \
                             "-SNAPSHOT-jar-with-dependencies.jar".split(' ')
            sources = [['--sources', s] for s in potential_violation.job1.job.target.sources]
            [cmd.extend(s) for s in sources]
            cmd.extend(["--target", potential_violation.job1.job.target.name])
            cmd.extend(["--bs", os.path.abspath(build_script)])
            cmd.extend(["--vs", os.path.abspath(script_location)])
            cmd.extend(["--logs", os.path.join(delta_debugging_directory, "log.txt")])
            cmd.extend(['--hdd'])
            cmd.extend(['--class-reduction'])
            cmd.extend(['--timeout', '120'])

            print(f"Running delta debugger with cmd {' '.join(cmd)}")
            subprocess.run(cmd, stdout=sys.stdout, stderr=sys.stderr, text=True)
            print("Delta debugging completed.")
        # delta_debugging_directory = os.path.join(results_directory)
        # tarname = os.path.join(delta_debugging_directory, get_file_name(violation)) + '.tar.gz'
        # Path(os.path.dirname(tarname)).mkdir(exist_ok=True, parents=True)
        # with tarfile.open(tarname, 'w:gz') as f:
        #     f.add(violation.job1.job.target.name, os.path.basename(violation.job1.job.target.name))
        #     [f.add(s) for s in violation.job1.job.target.sources]
        #     with open(os.path.join(delta_debugging_directory, get_file_name(violation)), 'w') as f1:
        #         json.dump(violation.as_dict(), f1)
        #     f.add(os.path.join(delta_debugging_directory, get_file_name(violation)),
        #           os.path.basename(os.path.join(delta_debugging_directory, get_file_name(violation))))
        #     f.add(os.path.join(d.name, "log.txt"), "log.txt")
        #     os.remove(os.path.join(delta_debugging_directory, get_file_name(violation)))
        #
        # print(f"Delta debugging result written to {tarname}")

    def create_script(self, violation: Violation, edge: Any, directory: str, timeout: Optional[int]) -> str:
        """
        Given a violation, creates a script that will execute it and return True if the violation is
        preserved.

        Parameters
        ----------
        timeout: The timeout of the delta debugger.
        directory: Where to put delta debugging results.
        violation: The violation to try to recreate.

        Returns
        -------
        the location of the script.
        """
        violation_tmp = tempfile.NamedTemporaryFile(delete=False, dir=directory)
        pickle.dump(violation, open(violation_tmp.name, 'wb'))
        violation_tmp.close()

        edge_tmp = tempfile.NamedTemporaryFile(delete=False, dir=directory)
        pickle.dump(edge, open(edge_tmp.name, 'wb'))
        edge_tmp.close()

        with tempfile.NamedTemporaryFile(mode='w', dir=directory, delete=False) as f:
            f.write("#!/bin/bash\n")
            cmd = f"deltadebugger --violation {violation_tmp.name} " \
                  f"--edge {edge_tmp.name}" \
                  f"--target {violation.job1.job.target.name} " \
                  f"--tool {self.tool} " \
                  f"--task {self.task} "
            if timeout is not None:
                cmd += f"--timeout {timeout} "
            if self.groundtruths is not None:
                cmd = f"{cmd} --groundtruths {self.groundtruths} "
            if self.whole_program:
                cmd = f"{cmd} --whole-program"
            f.write(cmd + "\n")
            result = f.name
            logger.info(f"Wrote cmd {cmd} to delta debugging script.")
        return result


import argparse
import logging


def main():
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    parser = argparse.ArgumentParser()
    parser.add_argument("--violation", help="The location of the pickled violation.", required=True)
    parser.add_argument("--edge", help="The edge to preserve.")
    parser.add_argument("--target", help="The location of the target program.", required=True)
    parser.add_argument("--tool", help="The tool to use.", required=True)
    parser.add_argument("--task", help="The task.", required=True)
    parser.add_argument("--groundtruths", help="Groundtruths (may be None if we are not using ground truths.")
    parser.add_argument("--timeout", help="Timeout in minutes.", type=int, default=None)
    parser.add_argument("--whole-program", help="Whole program", action='store_true')
    args = parser.parse_args()

    with open(args.violation, 'rb') as f:
        violation: Violation = pickle.load(f)

    with open(args.edge, 'rb') as f:
        edge = pickle.load(f)

    logger.info(f'Read violation from {args.violation}')
    violation.job1.job.target.name = os.path.abspath(args.target)
    violation.job2.job.target.name = os.path.abspath(args.target)

    # Create tool runner.
    tmpdir = tempfile.TemporaryDirectory()
    runner: AbstractCommandLineToolRunner = RunnerFactory.get_runner_for_tool(args.tool)
    if args.whole_program:
        runner.whole_program = True
    if args.timeout is not None:
        runner.timeout = args.timeout
    reader = ReaderFactory.get_reader_for_task_and_tool(args.task, args.tool)
    checker = ViolationCheckerFactory.get_violation_checker_for_task(args.task, args.tool,
                                                                     2, args.groundtruths, reader)
    partial_function = partial(runner.run_job, output_folder=tmpdir.name)
    with Pool(2) as p:
        finishedJobs: Iterable[FinishedFuzzingJob] = p.map(partial_function, [violation.job1.job, violation.job2.job])
    violations: Iterable[PotentialViolation] = \
        checker.check_violations([f for f in finishedJobs if f is not None and f.results_location is not None],
                                 tmpdir.name)
    for v in violations:
        # Since we already know the target and the configs are the same, we only have to check the partial order.
        if edge in v.expected_diffs:
            logging.info(f"Edge {edge} was recreated! Exiting with 0.")
            # 0 means succeed.
            exit(0)
    # 1 means the violation was not recreated.
    logging.info("Edge was not recreated. Exiting with 1.")
    exit(1)
