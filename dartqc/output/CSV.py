import csv
import os

import logging

import numpy

from dartqc.Dataset import Dataset
from dartqc.PipelineOptions import Output

log = logging.getLogger(__file__)


class CSVOutput(Output):
    def get_name(self) -> str:
        return "csv"

    def get_description(self) -> str:
        return "Output the genotype in CSV format (1 SNP per row, 1 sample per column)"

    def write(self, filter_name: str, folder: str, encoding: str, dataset: Dataset, unknown_args: [], **kwargs) -> None:
        file_path = os.path.join(folder, filter_name + "_" + self.get_name() + ".csv")

        log.info("Outputting CSV")

        filtered_calls, filtered_snps, filtered_samples = dataset.get_filtered_calls()

        # Get calls as matrix - swap SNP/sample axes & trim back to only first allele's call (much quicker processing)
        numpy_matrix = numpy.asarray([filtered_calls[snp.allele_id] for snp in filtered_snps])
        numpy_matrix = numpy.dstack(numpy_matrix)  # [SNPs][samples][calls] -> [samples][calls][SNPs]
        numpy_matrix = numpy.dstack(numpy_matrix)  # [SNPs][calls][samples] -> [calls][SNPs][samples]
        # numpy_matrix = numpy_matrix  # Only get first allele calls (if "-" -> missing)

        del filtered_calls

        # IMPORTANT #
        # Data is internally stored in the 11 encoding - this means:
        #   10 => HOMOZYGOUS, because the first allele is present and the second is not.  Therefore there are 2 of the first allele!
        #   01 => Also HOMOZYGOUS, for the other allele
        #   11 => HETEROZYGOUS, because BOTH alleles are present!

        # Convert from (0,1) type tuples to requested encoding
        for snp_idx, snp_def in enumerate(filtered_snps):
            if encoding == "ACTG":
                # Find the two possible letters for this SNP
                if snp_def.snp is None:
                    log.error("ACTG encoding not possible -> Missing SNP def for SNP {}, the allele ID should have the SNP definition in it such as 1234|F|0--32:C>A".format(snp_def.allele_id))
                    return

                # IMPORTANT #
                # ACTG encoding needs to give the actual 2 allele calls
                # Eg. for a A>T SNP 11 = AT, NOT AA!
                # Eg. for a A>T SNP 01 = TT, because only the second allele is present

                snp_vals = snp_def.snp.split(":")[1].split(">")

                # Replace all 0's & 1's with ACTG's - missing stays same
                numpy.put(numpy_matrix[0][snp_idx], numpy.where(numpy_matrix[0][snp_idx] == "0"), snp_vals[1])
                numpy.put(numpy_matrix[0][snp_idx], numpy.where(numpy_matrix[0][snp_idx] == "1"), snp_vals[0])
                numpy.put(numpy_matrix[1][snp_idx], numpy.where(numpy_matrix[1][snp_idx] == "0"), snp_vals[0])
                numpy.put(numpy_matrix[1][snp_idx], numpy.where(numpy_matrix[1][snp_idx] == "1"), snp_vals[1])

            elif encoding == "012":
                # Find indexes for 0's and 1's in first allele.
                major = numpy.where(numpy_matrix[0][snp_idx] == "1")
                minor = numpy.where(numpy_matrix[1][snp_idx] == "1")

                # Identify het's as where the second allele has a 1 in the same location as the first allele
                het = numpy.intersect1d(numpy.where(numpy_matrix[1][snp_idx] == "1"), major)

                # Remove het's from major and minor homo's
                major = numpy.setdiff1d(major, het, True)
                minor = numpy.setdiff1d(minor, het, True)

                # Replace the first allele values (-,0,1) with new encoding (-,0,1,2)
                numpy.put(numpy_matrix[0][snp_idx], het, "0")
                numpy.put(numpy_matrix[0][snp_idx], minor, "1")
                numpy.put(numpy_matrix[0][snp_idx], major, "2")

            elif encoding == "AB":
                snp_vals = ["A", "B"]

                # IMPORTANT #
                # AB encoding needs to give the actual 2 allele calls
                # Eg. 11 = AB, NOT AA!
                # Eg. 01 = BB, because only the second allele is present
                # Eg. 10 = AA, because only the first allele is present

                # Replace all 0's & 1's with A's and B's - missing stays same
                numpy.put(numpy_matrix[0][snp_idx], numpy.where(numpy_matrix[0][snp_idx] == "0"), snp_vals[1])
                numpy.put(numpy_matrix[0][snp_idx], numpy.where(numpy_matrix[0][snp_idx] == "1"), snp_vals[0])
                numpy.put(numpy_matrix[1][snp_idx], numpy.where(numpy_matrix[1][snp_idx] == "0"), snp_vals[0])
                numpy.put(numpy_matrix[1][snp_idx], numpy.where(numpy_matrix[1][snp_idx] == "1"), snp_vals[1])

            elif encoding == "IUPAC":
                # Find the two possible letters for this SNP
                if snp_def.snp is None:
                    log.error("IUPAC encoding not possible -> Missing SNP def for SNP {}, the allele ID should have the SNP definition in it such as 1234|F|0--32:C>A".format(snp_def.allele_id))
                    return

                snp_vals = snp_def.snp.split(":")[1].split(">")

                both_snps = snp_vals[0] + snp_vals[1]

                het_val = "R" if both_snps == "AG" or both_snps == "GA" \
                    else "Y" if both_snps == "CT" or both_snps == "TC" \
                    else "S" if both_snps == "GC" or both_snps == "CG" \
                    else "W" if both_snps == "AT" or both_snps == "TA" \
                    else "K" if both_snps == "GT" or both_snps == "TG" \
                    else "M" if both_snps == "AC" or both_snps == "CA" \
                    else "???"

                # Find indexes for 0's and 1's in first allele.
                major = numpy.where(numpy_matrix[0][snp_idx] == "1")
                minor = numpy.where(numpy_matrix[1][snp_idx] == "1")

                # Identify het's as where the second allele has a 1 in the same location as the first allele
                het = numpy.intersect1d(numpy.where(numpy_matrix[1][snp_idx] == "1"), major)

                # Remove het's from major and minor homo's
                major = numpy.setdiff1d(major, het, True)
                minor = numpy.setdiff1d(minor, het, True)

                # Replace the first allele values (-,0,1) with new encoding (-,0,1,2)
                numpy.put(numpy_matrix[0][snp_idx], het, het_val)
                numpy.put(numpy_matrix[0][snp_idx], minor, snp_vals[1])
                numpy.put(numpy_matrix[0][snp_idx], major, snp_vals[0])

        if encoding == "012" or encoding == "IUPAC":
            # All data is only in the first allele - so grab it now and drop the second row
            numpy_matrix = numpy_matrix[0]
        else:
            # Concatenate the 2 call values together into a single string
            numpy_matrix = numpy.core.defchararray.add(numpy_matrix[0], numpy_matrix[1])

        with open(file_path, "w") as file_out:
            headers = [""] + [sample_def.id for sample_def in filtered_samples]

            writer = csv.writer(file_out, lineterminator='\n')
            writer.writerow(headers)

            for idx, snp_def in enumerate(filtered_snps):
                writer.writerow([snp_def.allele_id] + numpy_matrix[idx].tolist())


                # filtered_calls = dataset.get_filtered_calls()
                #
                # # Get calls as matrix - swap SNP/sample axes & trim back to only first allele's call (much quicker processing)
                # numpy_matrix = numpy.asarray([filtered_calls[snp.allele_id] for snp in dataset.snps])
                # numpy_matrix = numpy.dstack(numpy_matrix)  # [SNPs][samples][calls] -> [samples][calls][SNPs]
                # numpy_matrix = numpy.dstack(numpy_matrix)  # [SNPs][calls][samples] -> [calls][SNPs][samples]
                # numpy_matrix = numpy_matrix  # Only get first allele calls (if "-" -> missing)
                #
                # with open(file_path, "w") as file_out:
                #     headers = [""] + [sample_def.id for sample_def in dataset.samples]
                #
                #     writer = csv.writer(file_out, lineterminator='\n')
                #     writer.writerow(headers)
                #
                #     # file_out.write(",".join(headers) + "\n")
                #     #
                #     for snp_idx, snp_def in enumerate(dataset.snps):
                #         snp_vals = snp_def.snp.split(":")[1].split(">")
                #
                #         split_calls = numpy.dstack(snp_calls)[0]
                #         numpy.put(split_calls[0], numpy.where(split_calls[0] == "0"), snp_vals[1])
                #         numpy.put(split_calls[0], numpy.where(split_calls[0] == "1"), snp_vals[0])
                #         numpy.put(split_calls[1], numpy.where(split_calls[1] == "0"), snp_vals[0])
                #         numpy.put(split_calls[1], numpy.where(split_calls[1] == "1"), snp_vals[1])
                #
                #         row = [allele_id] + numpy.concatenate([split_calls]).tolist()
                #
                #         writer.writerow([allele_id] + row)
                #
                #
                #     file_out.flush()


CSVOutput()
