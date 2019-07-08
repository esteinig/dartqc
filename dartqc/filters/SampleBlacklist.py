import re

from dartqc.FilterResult import FilterResult
from dartqc.Dataset import Dataset
from dartqc.PipelineOptions import Filter


class SampleBlacklistFilter(Filter):
    def get_order(self) -> int:
        return 0

    def get_cmd_type(self):
        return Filter.LIST_OF_LISTS

    def get_name(self) -> str:
        return "Sample Blacklist"

    def get_cmd_names(self) -> [str]:
        return ["--sample_blacklist"]

    def get_cmd_help(self) -> str:
        return "Remove samples - Pattern: [sample_id, sample_id, ...]"

    def get_description(self) -> str:
        return "Remove list of samples"

    def filter(self, dataset: Dataset, blacklist: [str], unknown_args: [], **kwargs) -> FilterResult:
        silenced = FilterResult()

        for sample_def in dataset.samples:
            if sample_def.id in blacklist and sample_def.id not in dataset.filtered.samples:
                silenced.silenced_sample(re.sub(r"['\"]", "", sample_def.id))

        return silenced

SampleBlacklistFilter()
