#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Daemon que lê um arquivo de configuração .INI e faz diversas checagens:
 - Checa o status do backup periódico do banco de dados;
 - Checa o status do backup dos logs binários do servidor MySQL master;
 - Checa o status da réplica do banco de dados.
Os retornos referente ao probe são servidos via HTTP"""

from optparse import OptionParser
from configobj import ConfigObj, ConfigObjError, Section
from extra.utils import Singleton
from extra.settings import constants as c
from socket import error as socket_error
import os
import logging
import BaseHTTPServer
import thread
import time
import sys
import MySQLdb
import simplejson as json

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
		def __init__(self, code, msg, parser=None):
			Exception.__init__(self, msg)
			self.code = code
			self.msg = msg + '\n'
			self.parser = parser

	class MyHandler(BaseHTTPServer.BaseHTTPRequestHandler):
		def __init__(self, monitoration_function, *args):
			self.monitoration_function = monitoration_function
			BaseHTTPServer.BaseHTTPRequestHandler.__init__(self, *args)

		def do_GET(s):
			"""Respond to a GET request."""
			s.send_response(200)
			s.send_header("Content-type", "text/html")
			s.end_headers()
			s.wfile.write(json.dumps(s.monitoration_function(),encoding='utf-8'))
			

	__metaclass__ = Singleton
	__return_code = c.NO_ERRORS
	__monitoration_array = {}

	__TIME_TO_SLEEP = {
                u'minutely': 60,
                u'hourly': 3600,
                u'daily': 86400,
                }

	def __init__(self):
		usage = "Usage: %prog [options] | INI-CONFIGURATION-FILE"
		description = "Replication and Backup Probes."
		parser = OptionParser(usage=usage,description=description)
		(options, args) = parser.parse_args()
		try:
			try:
				config_ini = args[0]
			except IndexError:
				#Treat no config file passed as argument
				raise self.FatalError(c.COMMAND_USE_ERROR,"Invalid number of arguments",parser)
			try:
			        configspec = ConfigObj(config_ini, encoding='UTF8', file_error=True)
			except (IOError), ioe:
				try:
					#Treat non-existent file
					raise self.FatalError(c.CANT_READ_CONFIGURATION,'Error: %s: ' % ioe.args[-1] + '"' + ioe.filename + '".')
				except (TypeError):
					#Treat permission denied on reading file
					raise self.FatalError(c.CANT_READ_CONFIGURATION,'Error: %s' % ioe.args[-1])
			except (ConfigObjError), cfge:
				#Treat invalid syntax on reading file
				raise self.FatalError(c.PARSING_CONFIGURATION_ERROR,'Error: %s' % cfge.msg.replace('\n',' '))
			for section in configspec.keys():
				if isinstance(configspec[section],Section):
					for subsection in c.SUBSECTIONS:
						try:
							thread.start_new_thread(self.__check,(section,subsection,configspec[section][subsection['name']]))
						except (KeyError), ke:
							#TODO Logging non-existent subsections
							pass
			try:
				self.__start_webserver(int(configspec['probe-port']),self.get_monitoration_array)
			except (ValueError), ve:
				#TODO Treat invalid port values
				pass
			except (KeyError), ke:
                                #TODO Treat no port specified
                                pass
			except (socket_error), se:
				#TODO Treat socket error
                                pass
		except (self.FatalError), fe:
			self.__set_return_code(fe.code)
			if not fe.parser:
				print fe.msg.encode('utf-8')
			else:
				fe.parser.error(fe.msg)

	def __start_webserver(self, port, monitoration_function):
		def modify_handler(monitoration_function):
			return lambda *args: self.MyHandler(monitoration_function, *args)
		handler = modify_handler(monitoration_function)
		httpd = BaseHTTPServer.HTTPServer(('', port), handler)
		try:
			httpd.serve_forever()
		except KeyboardInterrupt:
			pass
	
	def get_monitoration_array(self):
		return self.__monitoration_array

	def __set_return_code(self,code):
		self.__return_code = code

	def get_return_code(self):
		return self.__return_code
	
	def __update_status(self,section,subsection,status):
#		try:
#			self.__monitoration_array[section][subsection] = status
#		except (KeyError), ke:
#			self.__monitoration_array[section] = {subsection: status}
		self.__monitoration_array[section + '-' + subsection] = int(status)

	def __check(self, section, subsection, info):
		METHODS = {
		u'growing-dir': self.__check_growing_dir,
		u'mysql-replication': self.__check_mysql_replication,
		}
		
		try:
			real_check = METHODS[subsection['type']]
		except (KeyError), ke:
			#TODO Treat invalid and not configured types
			pass
		real_check(section,subsection['name'],info)
#		self.__update_status(section,subsection,True)	

	def __get_time_to_sleep(self,interval):
		try:
			return self.__TIME_TO_SLEEP[interval]
		except:
			#Treat invalid interval
			pass

	def __check_growing_dir(self,section,subsection,info):
		#print 'growing_dir: %s - %s - TOTAL %i' % (section,str(info),self.__get_dir_size(info['dir']))

		last_size = self.__get_dir_size(info['dir'])
#		delay = TIME_TO_SLEEP[info[u'check-interval']]
		delay = self.__get_time_to_sleep(info[u'check-interval'])
#		print u'Esperar %s para seção %s, subseção %s' % (delay,section,subsection)
		while True:
			time.sleep(delay)
			new_size = self.__get_dir_size(info['dir'])
			if (new_size - last_size) > int(info[u'threshold']):
				self.__update_status(section,subsection,True)
			else:
				self.__update_status(section,subsection,False)
			last_size = new_size
			
		

	def __check_mysql_replication(self,section,subsection,info):

		query_slavestatus = ( "SHOW SLAVE STATUS" )

		delay = self.__get_time_to_sleep(info[u'check-interval'])
		def inner_check():
			db = MySQLdb.connect(host=info[u'host'],
                                user=info[u'user'],
                                passwd=info[u'password'],
                                port=int(info[u'port']))

                        query_slavestatus = ( "SHOW SLAVE STATUS" )
                        cur = db.cursor()
                        cur.execute(query_slavestatus)
                        row = cur.fetchone()
                        slave_status = {}
                        for i in range(len(cur.description)):
                                slave_status[cur.description[i][0]] = row[i]
                        if (slave_status[u'Slave_IO_Running'] == 'Yes') and (slave_status[u'Slave_SQL_Running'] == 'Yes') and (slave_status[u'Slave_SQL_Running'] == 'Yes') and (not slave_status[u'Last_Error']):
                                self.__update_status(section,subsection,True)
                        else:
                                self.__update_status(section,subsection,False)
                        db.close()
		inner_check()
		while True:
                        time.sleep(delay)
			inner_check()

	def __get_dir_size(self,start_path):
		total_size = 0
		for dirpath, dirnames, filenames in os.walk(start_path):
			for f in filenames:
				fp = os.path.join(dirpath, f)
				total_size += os.path.getsize(fp)
		return total_size

if __name__ == "__main__":
	m = Main()
	sys.exit(m.get_return_code())
