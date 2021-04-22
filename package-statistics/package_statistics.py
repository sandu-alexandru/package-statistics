#!/usr/bin/env python3
"""
This module shows the user the top n packages with most file associations.

Usage:
./package_statistics.py [architecture]

Sample output:

Package statistics for Contents file for i386 architecture:

1. fonts/fonts-cns11643-pixmaps	110999
2. x11/papirus-icon-theme	69475
3. fonts/texlive-fonts-extra	65577
4. games/flightgear-data-base	62458
5. devel/piglit	49913
6. doc/trilinos-doc	49591
7. x11/obsidian-icon-theme	48829
8. games/widelands-data	34984
9. doc/libreoffice-dev-doc	33666
10. misc/moka-icon-theme	33326
"""
import os
import re
import sys
import gzip
import heapq
import shutil
import logging
import datetime
import urllib.request

DATE_FORMAT = '%H-%M-%S_%d-%m-%Y'
DEFAULT_PACKAGES_ADDRESS = "http://ftp.uk.debian.org/debian/dists/stable/main/"
DEFAULT_ARCH = "amd64"


class PackageContentsHandler:
    """
    Package content handler, meant to be used when performing various
    operations on a contents indices file, based on architecture.
    """
    def __init__(self, architecture, package_address):
        self.architecture = architecture
        self.package_address = package_address
        self.package_contents_file = f"Contents-{self.architecture}"

        timestamp = datetime.datetime.now().strftime(DATE_FORMAT)
        self.package_contents_directory = (
            f"{self.package_contents_file}_{timestamp}")

        self.package_contents_filepath = (
            f"{self.package_contents_directory}/{self.package_contents_file}")

        self.package_associations = {}

    def retrieve_package_contents_file(self) -> None:
        """
        Retrieves the content indices file.

        Downloads the gz file under a runtime-created directory
        and extracts the contents under a specified filepath.
        """
        logging.info("Preparing the Contents indices directory: %s",
                     self.package_contents_directory)
        os.makedirs(self.package_contents_directory, exist_ok=True)

        logging.info("Attempting to retrieve Contents indices file\n"
                     "\tFile: %s.gz\n\tAddress: %s",
                     self.package_contents_file,
                     self.package_address)
        urllib.request.urlretrieve(
            f'{self.package_address}{self.package_contents_file}.gz',
            f"{self.package_contents_filepath}.gz")

        logging.info("Extracting gz archive")
        with gzip.open(f'{self.package_contents_filepath}.gz', 'rb') as f_in:
            with open(self.package_contents_filepath, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)

    def generate_package_association_stats(self) -> None:
        """
        Generates the package association dictionary based on file contents.

        Retrieves the file if it isn't already prepared,
        and while reading through the lines,
        attempt to get the package(s), and based on their occurences,
        update the package associations dictionary.
        """
        if not os.path.exists(self.package_contents_filepath):
            self.retrieve_package_contents_file()

        logging.info("Generating package association statistics")
        with open(self.package_contents_filepath, "r",
                  encoding="utf-8", buffering=2048) as package_contents_file:
            for line in package_contents_file.readlines():
                self.__process_package_association_line(line)
        logging.info("Package association dictionary generated")

    def __process_package_association_line(self, package_association_line):
        """
        Processes a package association line from Contents index,
        updating the package associations stats dictionary
        based on the findings, either adding a new package or
        incrementing the associations of an already existing one
        within the stats.

        Args:
            package_association_line: line from the Contents index file,
                                    specifying a file-package association.
        """
        try:
            possible_package = re.split(r'\s+', package_association_line)[1]
        except IndexError:
            logging.error("\nError ecountered"
                          " on package association line:\n%s\n",
                          package_association_line)
        else:
            # Splitting for comma since some files
            # are associated with multiple packages
            possible_packages = possible_package.split(",")
            for package in possible_packages:
                if package not in self.package_associations:
                    self.package_associations[package] = 1
                else:
                    self.package_associations[package] += 1

    def show_top_packages_with_most_associations(self, how_many: int = 10):
        """
        Prints the top packages with most associations.

        Generates both console output as well as a report file,
        containing the top packages that were found with most file associations

        Args:
            how_many: Up to which number the top should be
        """
        sorted_packages = heapq.nlargest(how_many,
                                         self.package_associations,
                                         key=self.package_associations.get)

        output = (f"\nPackage statistics for Contents file "
                  f"for {self.architecture} architecture:\n")
        for i in range(how_many):
            output += (
                f"{i + 1}. "  # Top number
                f"{sorted_packages[i]}\t"   # Package name
                f"{self.package_associations[sorted_packages[i]]}\n")  # Value

        print(output)
        with open(f"{self.package_contents_directory}/"
                  f"top_{how_many}_packages.txt", "w",
                  encoding="utf-8") as output_file:
            output_file.write(output)


if __name__ == '__main__':
    logging.getLogger().setLevel(logging.INFO)
    #
    # Using a PackageContentsHandler object,
    # we can generate the statistics and print the output
    # for the top packages with most associations
    #
    architecture_arg = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_ARCH

    contents_handler = PackageContentsHandler(architecture_arg,
                                              DEFAULT_PACKAGES_ADDRESS)
    contents_handler.generate_package_association_stats()
    contents_handler.show_top_packages_with_most_associations()
