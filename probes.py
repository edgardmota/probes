#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Daemon que lê um arquivo de configuração .INI e faz diversas checagens:
 - Checa o status do backup periódico do banco de dados;
 - Checa o status do backup dos logs binários do servidor MySQL master;
 - Checa o status da réplica do banco de dados.
Os retornos referente ao probe são servidos via HTTP"""

from optparse import OptionParser
from configobj import ConfigObj, ConfigObjError
from extra.utils import Singleton
import BaseHTTPServer
import thread
import time
import sys

__author__ = "Edgard Mota de Oliveira"
__copyright__ = "Copyright 2013, BoaCompra UOL"
__credits__ = ["Edgard Mota de Oliveira", "Marcelo Henrique Gonçalves (tqi_mhgoncalves@uolinc.com)"]
__license__ = "Proprietária"
__version__ = "0.0.1"
__maintainer__ = "Edgard Mota de Oliveira"
__email__ = "emota@uolinc.com"
__status__ = "Desenvolvimento"

class Main:

	class FatalError(Exception):
		pass

	__metaclass__ = Singleton
	__root_reserved_words = [u'probe-port', u'log-file']
	def __init__(self):
		usage = "Usage: %prog [options] | INI-CONFIGURATION-FILE"
		description = "Probe de backups e réplicas."
		parser = OptionParser(usage=usage,description=description)
		(options, args) = parser.parse_args()
		try:
			config_ini = args[0]
		except IndexError:
		        parser.error("Número de argumentos incorreto")
		else:
			try:
			        configspec = ConfigObj(config_ini, encoding='UTF8', file_error=True)
			except (IOError), ioe:
				try:
					print 'Error: %s: ' % ioe.args[-1] + '"' + ioe.filename + '".'
				except (TypeError):
					print 'Error: %s' % ioe.args[-1]
			except (ConfigObjError), cfge:
				print 'Error: %s' % cfge.msg.replace('\n',' ')
			else:
				print configspec

if __name__ == "__main__":
	sys.exit(Main())
