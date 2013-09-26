#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Daemon que monitora os b"""

from optparse import OptionParser

__author__ = "Edgard Mota de Oliveira"
__copyright__ = "Copyright 2013, BoaCompra UOL"
__credits__ = ["Edgard Mota de Oliveira", "Marcelo Henrique Gonçalves (tqi_mhgoncalves@uolinc.com)"]
__license__ = "Proprietária"
__version__ = "0.0.1"
__maintainer__ = "Edgard Mota de Oliveira"
__email__ = "emota@uolinc.com"
__status__ = "Desenvolvimento"

def main():
	usage = "Usage: %prog [options] | DIRECTORY LAST-SIZE"
	description = "Verify if DIRECTORY has grown based on its LAST-SIZE"
	parser = OptionParser(usage=usage,description=description)
	(options, args) = parser.parse_args()
	if len(args) != 2:
		parser.error("Número de argumentos incorreto")
	else:
		pass	


if __name__ == "__main__":
	main()
