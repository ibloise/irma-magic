import os
import secrets

from . import constants


def write_new_file(path, writer, *, binary=False, newline=None):
    """Write and atomically publish a new file without replacing a path."""
    destination = os.path.abspath(os.fsdecode(os.fspath(path)))
    directory = os.path.dirname(destination)
    for _ in range(100):
        temporary = os.path.join(directory, ".irmagic-" + secrets.token_hex(8))
        try:
            descriptor = os.open(
                temporary, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o666
            )
            break
        except FileExistsError:
            continue
    else:
        raise FileExistsError(
            f"Could not reserve a temporary file for {destination!r}"
        )

    try:
        if binary:
            handle = os.fdopen(descriptor, "wb")
        else:
            handle = os.fdopen(descriptor, "w", encoding="utf-8", newline=newline)
        with handle:
            writer(handle)
        os.link(temporary, destination)
    except BaseException:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise
    else:
        os.unlink(temporary)


class File:
    def __init__(self, filename):
        self.name = filename

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, filename):
        filename = os.fspath(filename)
        self._name = os.path.basename(filename)
        self.ext = os.path.splitext(self._name)[1]
        self.path = os.path.dirname(filename)
        self.compressed = self._is_compressed(filename)
        self.full_name = os.path.join(self.path, self._name)

    def _is_compressed(self, filename):
        return False

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name


class FastqFile(File):
    FASTQ_EXT = constants.FASTQ_EXT
    FQ_EXT = constants.FQ_EXT
    GZ_EXT = constants.GZ_EXT
    VALID_SUFFIXES = (
        FASTQ_EXT + GZ_EXT,
        FQ_EXT + GZ_EXT,
        FASTQ_EXT,
        FQ_EXT,
    )

    @File.name.setter
    def name(self, filename):
        filename = os.fspath(filename)
        self._name = os.path.basename(filename)
        self.path = os.path.dirname(filename)
        self.full_name = os.path.join(self.path, self._name)
        self.ext = next(
            (suffix for suffix in self.VALID_SUFFIXES if self._name.endswith(suffix)),
            None,
        )
        if self.ext is None:
            admitted = ", ".join(self.VALID_SUFFIXES)
            raise ValueError(
                f"FASTQ file {filename!r} must end with one of: {admitted}"
            )
        self.compressed = self.ext.endswith(".gz")
        self.stem = self._name[:-len(self.ext)]

class FastqSet:
    def __init__(self, file_tuple, paired, patterns, common_name=None):
        self.files = file_tuple
        self.paired = paired
        self.patterns = patterns
        check_file = file_tuple[0]
        self.compress = check_file.compressed
        if common_name is None:
            if paired:
                if check_file.stem.count(patterns[0]) != 1:
                    raise ValueError(
                        f"Expected exactly one read marker {patterns[0]!r} "
                        f"in {check_file.name!r}"
                    )
                common_name = check_file.stem.replace(patterns[0], "", 1)
            else:
                common_name = check_file.stem
        if not common_name:
            raise ValueError(f"FASTQ filename {check_file.name!r} has an empty sample ID")
        self.common_name = common_name

    def __repr__(self):
        return f"{self.common_name}:{self.files}; {self.paired}"


class FastqCollection:
    def __init__(self):
        self._collection = []

    @classmethod
    def from_list(cls, **kwargs):
        collection = cls()
        collection.append_files(**kwargs)
        return collection

    def append_files(
        self,
        files,
        paired: bool,
        first_pattern: str = constants.FORWARD_VALUE,
        second_pattern: str = constants.REVERSE_VALUE,
    ):
        if paired and (not first_pattern or not second_pattern or first_pattern == second_pattern):
            raise ValueError("Paired-read patterns must be nonempty and distinct")

        fastq_files = [self._transform_file(filename) for filename in files]
        if not fastq_files:
            raise ValueError("At least one FASTQ input is required")
        if paired:
            files_and_names = self._pair_files(
                fastq_files, first_pattern, second_pattern
            )
        else:
            files_and_names = [
                ((fastq_file,), fastq_file.stem) for fastq_file in fastq_files
            ]

        existing_names = {fastq_set.common_name for fastq_set in self._collection}
        new_sets = []
        for file_tuple, common_name in files_and_names:
            fastq_set = FastqSet(
                file_tuple,
                paired,
                (first_pattern, second_pattern),
                common_name=common_name,
            )
            if fastq_set.common_name in existing_names:
                raise ValueError(
                    f"Duplicate IRMA output name {fastq_set.common_name!r}; "
                    "refusing to risk output collision"
                )
            existing_names.add(fastq_set.common_name)
            new_sets.append(fastq_set)
        self._collection.extend(new_sets)

    def _transform_file(self, filename):
        return FastqFile(filename)

    def _pair_files(self, files_list, first_pattern, second_pattern):
        by_sample = {}
        for fastq_file in files_list:
            stem = fastq_file.stem
            first_count = stem.count(first_pattern)
            second_count = stem.count(second_pattern)
            if first_count and second_count:
                raise ValueError(
                    f"Ambiguous read markers in FASTQ filename {fastq_file.full_name!r}"
                )
            if first_count > 1 or second_count > 1:
                raise ValueError(
                    f"Ambiguous repeated read marker in FASTQ filename "
                    f"{fastq_file.full_name!r}"
                )
            if first_count == 1:
                role, marker = 1, first_pattern
            elif second_count == 1:
                role, marker = 2, second_pattern
            else:
                raise ValueError(
                    f"FASTQ filename {fastq_file.full_name!r} contains neither "
                    f"read marker {first_pattern!r} nor {second_pattern!r}"
                )

            sample_id = stem.replace(marker, "", 1)
            if not sample_id:
                raise ValueError(
                    f"FASTQ filename {fastq_file.full_name!r} has an empty sample ID"
                )
            source_directory = os.path.abspath(fastq_file.path or os.curdir)
            sample_key = (source_directory, sample_id)
            reads = by_sample.setdefault(sample_key, {1: [], 2: []})
            reads[role].append(fastq_file)

        pairs = []
        for (_, sample_id), reads in sorted(by_sample.items()):
            if len(reads[1]) != 1 or len(reads[2]) != 1:
                absent = []
                if not reads[1]:
                    absent.append(first_pattern)
                if not reads[2]:
                    absent.append(second_pattern)
                duplicates = []
                if len(reads[1]) > 1:
                    duplicates.append(first_pattern)
                if len(reads[2]) > 1:
                    duplicates.append(second_pattern)
                details = []
                if absent:
                    details.append(f"missing {', '.join(absent)}")
                if duplicates:
                    details.append(f"duplicate {', '.join(duplicates)}")
                raise ValueError(
                    f"Invalid paired FASTQ inputs for sample {sample_id!r}: "
                    f"{'; '.join(details)}"
                )
            pairs.append(((reads[1][0], reads[2][0]), sample_id))
        return pairs

    def iter_files(self):
        return iter(self._collection)

    def __repr__(self):
        return f"{self._collection}"
