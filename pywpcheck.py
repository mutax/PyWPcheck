#! /usr/bin/env python
# -*- coding: utf8 -*-
#
#    PyWPcheck - Wordpress Update Checker in python
#    Copyright (C) 2013  Florian Streibelt pywpcheck@f-streibelt.de
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, version 2 only.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program; if not, write to the Free Software
#    Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301
#    USA

"""PyWPcheck by Florian Streibelt <pywpcheck@f-streibelt.de>"""


import ConfigParser,argparse,logging,sys

config = ConfigParser.ConfigParser()
logger = logging.getLogger('') # must be the root logger initially

def main():
	global config
	global logger

	parser = argparse.ArgumentParser()
	parser.add_argument('-c','--config', default="pywpcheck.cfg",help="configuration file to read.")
	parser.add_argument('-d','--debug', help="debuglevel for python logging, overriding configuration")

	args = parser.parse_args()
	try:
		config.readfp(open(args.config))
	except Exception,e:
		print e
		print "Could not read configuration. Need help? Use -h"
		sys.exit(1)

	try:
		logfile = config.get("log:file","logfile")
		try:
			# allow disabling of logfile creation on startup
			enabled = config.get("log:file","enabled").strip().upper()
			if enabled != 'YES' and enabled != 'TRUE':
				logfile=None
		except:
			pass
	except ConfigParser.NoSectionError:
		logfile = None


	logger.setLevel(logging.DEBUG)

	formatter = logging.Formatter('%(asctime)s, %(levelname)s, %(name)s, %(module)s, %(funcName)s: %(message)s')

	if logfile:
		# setup file logging

		if args.debug:
			loglevel_file=args.debug
		else:
			loglevel_file=config.get("log:file","level")


		loglevel_file_num = getattr(logging, loglevel_file.upper(), None)

		if not isinstance(loglevel_file_num, int):
			raise ValueError('Invalid log file loglevel: %s' % loglevel_file)


		file_log_handler = logging.FileHandler(filename=logfile)
		file_log_handler.setFormatter(formatter)
		file_log_handler.setLevel(loglevel_file_num)
		logger.addHandler(file_log_handler)


	loglevel_cons=None
	loglevel_cons_num=logging.NOTSET
	consolelogging=True

	if args.debug:
		loglevel_cons=args.debug
	else:
		try:
			loglevel_cons=config.get("log:console","level")

			try:
				# allow disabling of logging to stdout
				enabled = config.get("log:console","enabled").strip().upper()
				if enabled != 'YES' and enabled != 'TRUE':
					loglevel_cons=None
					consolelogging=False
			except:
				pass

		except ConfigParser.NoSectionError:
			pass

	if loglevel_cons:
		loglevel_cons_num = getattr(logging, loglevel_cons.upper(), None)

		if not isinstance(loglevel_cons_num, int):
			raise ValueError('Invalid console loglevel: %s' % loglevel_cons)


	if consolelogging:
		stderr_log_handler = logging.StreamHandler()
		stderr_log_handler.setFormatter(formatter)
		stderr_log_handler.setLevel(loglevel_cons_num)
		logger.addHandler(stderr_log_handler)

	if len(logger.handlers)==0:
		# as adviced when we don't want the
		# No hndler found error...
		logger.addHandler(logging.NullHandler())

	logger.debug("configured.")
	logger = logging.getLogger("PyWPcheck")
	logger.debug("switched logger.")

	if args.debug:
		logger.info('Loglevel was set to %s using the commandline' % args.debug)

	from pywplib.check import pywpcheck
	pywpcheck(config)

if __name__ == '__main__':
	try:
		main()
	except KeyboardInterrupt:
		pass

