import subprocess

from . import constants
from .files import FastqCollection


class IrmaExecutionError(RuntimeError):
    """An IRMA command could not be started or completed successfully."""


class IrmaBulk:
    SINGLE_READS = constants.SINGLE_READS
    PAIRED_READS = constants.PAIRED_READS

    def __init__(
        self,
        module,
        file_list,
        reads_type,
        irma_cmd=constants.IRMA_CMD,
        first_pattern=constants.FORWARD_VALUE,
        second_pattern=constants.REVERSE_VALUE,
    ):
        self.irma_cmd = irma_cmd
        self.module = module
        self._cmd_list = []

        if reads_type == self.SINGLE_READS:
            paired = False
        elif reads_type == self.PAIRED_READS:
            paired = True
        else:
            raise ValueError(
                f"Reads type must be {self.SINGLE_READS!r} or {self.PAIRED_READS!r}"
            )

        fastq_collection = FastqCollection.from_list(
            files=file_list,
            paired=paired,
            first_pattern=first_pattern,
            second_pattern=second_pattern,
        )
        self._extend_cmd_list(fastq_collection, module)

    def _extend_cmd_list(self, fastq_collection, module=None):
        for fastq_set in fastq_collection.iter_files():
            command = self._build_cmd(
                files=fastq_set.files,
                output=fastq_set.common_name,
                module=module,
            )
            self._cmd_list.append(command)

    def _build_cmd(self, files, module=None, output=None):
        module = module or self.module
        if not isinstance(module, str) or not module.strip():
            raise ValueError("An IRMA module is required")
        if output is not None:
            if not isinstance(output, str) or not output.strip():
                raise ValueError("IRMA output name cannot be empty")
            if output in (".", "..") or "/" in output or "\\" in output or "\0" in output:
                raise ValueError(f"Invalid IRMA output name: {output!r}")

        command = [self.irma_cmd, module]
        command.extend(file.full_name for file in files)
        if output is not None:
            command.append(output)
        return command

    def add_execution(
        self,
        file_list,
        paired: bool,
        module=None,
        first_pattern=constants.FORWARD_VALUE,
        second_pattern=constants.REVERSE_VALUE,
    ):
        fastq_collection = FastqCollection.from_list(
            files=file_list,
            paired=paired,
            first_pattern=first_pattern,
            second_pattern=second_pattern,
        )
        existing_outputs = {command[-1] for command in self._cmd_list}
        new_commands = []
        for fastq_set in fastq_collection.iter_files():
            if fastq_set.common_name in existing_outputs:
                raise ValueError(
                    f"Duplicate IRMA output name {fastq_set.common_name!r}; "
                    "refusing to risk output collision"
                )
            existing_outputs.add(fastq_set.common_name)
            new_commands.append(
                self._build_cmd(
                    files=fastq_set.files,
                    output=fastq_set.common_name,
                    module=module,
                )
            )
        self._cmd_list.extend(new_commands)

    def run(self):
        for command in self._cmd_list:
            sample = command[-1]
            try:
                subprocess.run(command, check=True)
            except subprocess.CalledProcessError as error:
                raise IrmaExecutionError(
                    f"IRMA failed for sample {sample!r} with exit code "
                    f"{error.returncode}"
                ) from error
            except FileNotFoundError as error:
                raise IrmaExecutionError(
                    f"IRMA executable not found: {self.irma_cmd!r}"
                ) from error
            except PermissionError as error:
                raise IrmaExecutionError(
                    f"Permission denied while starting IRMA executable "
                    f"{self.irma_cmd!r}"
                ) from error
            except OSError as error:
                raise IrmaExecutionError(
                    f"Could not run IRMA for sample {sample!r}: {error}"
                ) from error
        return 0
