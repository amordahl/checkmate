from src.checkmate.runners.CommandLineToolRunner import CommandLineToolRunner


class DOOPRunner(CommandLineToolRunner):
    def get_input_option(self) -> str:
        return "-i"

    def get_output_option(self) -> str:
        pass

    def get_task_option(self, task: str) -> str:
        if task == 'cg':
            pass
        else:
            raise NotImplementedError(f'DOOP does not support task {task}.')

    def get_base_command(self) -> str:
        return "doop"