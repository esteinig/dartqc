import re

from dartqc.FilterResult import FilterResult
from dartqc.Dataset import Dataset
from dartqc.PipelineOptions import Filter


class SNPBlacklistFilter(Filter):
    def get_order(self) -> int:
        return 1

    def get_cmd_type(self):
        return Filter.LIST_OF_LISTS

    def get_name(self) -> str:
        return "SNP Blacklist"

    def get_cmd_names(self) -> [str]:
        return ["--snp_blacklist"]

    def get_cmd_help(self) -> str:
        return "Remove SNPs - Pattern: [allele_id, allele_id, ...]"

    def get_description(self) -> str:
        return "Remove list of SNPs"

    def filter(self, dataset: Dataset, blacklist: [str], unknown_args: [], **kwargs) -> FilterResult:
        silenced = FilterResult()

        for snp_def in dataset.snps:
            if snp_def.allele_id in blacklist and snp_def.allele_id not in dataset.filtered.snps:
                silenced.silenced_snp(snp_def.allele_id)

        return silenced

SNPBlacklistFilter()
