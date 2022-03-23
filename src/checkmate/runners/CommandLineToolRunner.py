import subprocess
import time
from abc import ABC, abstractmethod

from src.checkmate.runners.AbstractCommandLineToolRunner import AbstractCommandLineToolRunner
from src.checkmate.util.FuzzingJob import FuzzingJob
from src.checkmate.util.UtilClasses import FinishedFuzzingJob

"""
This class supports the basics of running a command line tool,
which allows setting input and output via a command line option.
"""
class CommandLineToolRunner(AbstractCommandLineToolRunner, ABC):

    @abstractmethod
    def get_tool_path(self) -> str:
        pass

    @abstractmethod
    def get_input_option(self) -> str:
        """Returns option that should prepend the input program."""
        pass

    @abstractmethod
    def get_output_option(self) -> str:
        """Returns option that should prepend the output."""
        pass

    @abstractmethod
    def get_task_option(self, task: str) -> str:
        """Given a task, sets the appropriate option."""
        pass

    def transform(self, result_path: str):
        """Applies a transformation to the results before returning."""
        pass

    def run_job(self, job: FuzzingJob) -> FinishedFuzzingJob:
        config_as_str = self.dict_to_config_str(job.configuration)
        cmd = [self.get_tool_path()].extend(config_as_str)
        output_file = f'{self.dict_hash()}_{job.apk}.result'
        cmd.extend([self.get_input_option(), job.apk, self.get_output_option(), output_file])
        start_time: float = time.time()
        subprocess.run(cmd)
        total_time: float = time.time() - start_time
        self.transform(output_file)
        return FinishedFuzzingJob(
            job=job,
            execution_time=total_time,
            results_location=output_file
        )



