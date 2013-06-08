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

import logging
logger = logging.getLogger(__name__)


class WPDBConf:

	def __init__(self,settings):

		self.name        = settings['name']
		self.database    = settings['database']
		self.tableprefix = settings['tableprefix']
		self.dbhost      = settings['dbhost']
		self.username    = settings['username']
		self.password    = settings['password']

	def __str__(self):
		return "Wordpress site %(name)s (%(user)s@%(dbhost)s/%(database)s)" % \
		        { 'name': self.name,
				  'user': self.username,
				  'dbhost': self.dbhost,
				  'database': self.database,
				}


def getWPSitesFromConfig(config):

	sites = filter ( lambda x:x.startswith('site:'),config.sections() )

	return sites



def mysqlconnect(site):

	import MySQLdb as mdb

	dbhost = site.dbhost
	dbuser = site.username
	dbpass = site.password
	dbname = site.database

	logger.info('opening new connection to mysql://%s@%s/%s' % (dbuser,dbhost,dbname))
	try:
		db_connection = mdb.connect(dbhost, dbuser, dbpass, dbname)
	except Exception,e:
		logger.exception(e)
		raise e

	return db_connection


def wpsql_get_option(con,key,prefix="wp_"):

	cur = con.cursor()

	table = "%s%s" % (prefix,'options')

	cur.execute(
			"SELECT option_value  FROM %(table)s WHERE option_name='%(key)s'" % \
				{
					'key': key,
					'table': table,
				}
	)
	rc=cur.rowcount

	if not rc==1:
		logger.debug("option %s not found" % key)
		return None

	return cur.fetchone()[0]


def parse_core_to_dict(phpdata):
	""" Try to parse the serialized php objects of the core updater"""
	from phpserialize import loads,phpobject
	import time

	# They store serialized php objects in the database
	# where usually options are saved - we have to 
	# deserialize them and extract the information as dict.
	# The problem here is, that all three update mechanisms
	# use slightly different formats.

	try:

		p=loads(phpdata,object_hook=phpobject)
		d1=p._asdict()

		# this field is only present in the core blob:
		if 'version_checked' in d1:
			current_version=d1['version_checked']
		else:
			current_version=None

		if 'updates' in d1:
			updates=d1['updates']
		else:
			updates={}

		rdict={}
		for k,u in updates.iteritems():
			# for the core here is another serialized 
			# object in our dict:
			rdict[k]=u._asdict()

		age = time.time() - d1['last_checked']
		return age,current_version,rdict

	except Exception,e:
		logger.error("Error parsing serialized php data: core")
		logger.exception(e)
		logger.error("'"+phpdata+"'")

	return -1,None,None



def parse_plugins_to_dict(phpdata):
	""" Try to parse the serialized php objects of the plugins updater"""
	from phpserialize import loads,phpobject
	import time

	try:

		# deserialize the outer php class to a dict
		p=loads(phpdata,object_hook=phpobject)
		d1=p._asdict()

		if 'checked' in d1:
			checked  = d1['checked']
		else:
			checked  = {}

		# yes,here they call the field response
		if 'response' in d1:
			response = d1['response']
		else:
			response = {}

		rdict={}
		for k,r in response.iteritems():
			rdict[k]=r._asdict()

		age = time.time() - d1['last_checked']
		return age,checked,rdict

	except Exception,e:
		logger.error("Error parsing serialized php data: plugins")
		logger.exception(e)
		logger.error("'"+phpdata+"'")

	return -1,None,None




def parse_themes_to_dict(phpdata):
	""" Try to parse the serialized php objects of the plugins updater"""
	from phpserialize import loads,phpobject
	import time

	# yes, they really have different formats in each of the settings...
	# while in core and plugins the response entry are objects, here they are
	# already dicts... *sigh*

	# At this point it was already too late to stop this little project...
	# after wasting 8 hours into this... 

	try:

		d1=loads(phpdata,object_hook=phpobject)._asdict()
		checked  = {}
		response = {}

		if 'checked' in d1:
			checked  = d1['checked']
		if 'response' in d1:
			response = d1['response']

		if 'last_checked' in d1:
			last_checked = d1['last_checked']
			age = time.time() - last_checked
		else:
			age = -1

		return age,checked,response

	except Exception,e:
		logger.error("Error parsing serialized php data")
		logger.exception(e)
		logger.error("'"+phpdata+"'")

	return -1,None,None



def underline(text,underline='-'):
	""" make a nice headline"""
	print text
	print underline*len(text)
	print


def pywpcheck(config):
	""" The main working area - be warned, at some point I gave up"""
	wpsites = set()
	wpsections = getWPSitesFromConfig(config)

	logger.debug("loading default myysql config")
	d = dict(config.items('mysql:defaults'))

	for wpsection in wpsections:
		logger.debug("loading config for WP Site: %s" % wpsection)
		d['name'] = wpsection.replace('site:','')
		c = dict(config.items(wpsection))
		# overwrite defaults, if present
		settings = dict(d.items()+c.items())
		wpconfig = WPDBConf(settings)
		logger.info("found Site: %s" % wpconfig)
		wpsites.add(wpconfig)


	logger.debug("found %i Sites in the configuration" % len(wpsites))


	for site in wpsites:
		con = mysqlconnect(site)
		s_u_core    = None
		s_u_themes  = None 
		s_u_plugins = None

		try:
			url  = wpsql_get_option(con,'siteurl',prefix=site.tableprefix)
			name = wpsql_get_option(con,'blogname',prefix=site.tableprefix)
			s_u_core    = wpsql_get_option(con,'_site_transient_update_core'    ,prefix=site.tableprefix)
			s_u_themes  = wpsql_get_option(con,'_site_transient_update_themes'  ,prefix=site.tableprefix)
			s_u_plugins = wpsql_get_option(con,'_site_transient_update_plugins' ,prefix=site.tableprefix)

		except Exception,e:
			logger.error("Database error while checking %s: %s - continue with next site" % (site,e))
			#logger.exception(e)
			#try to check the others
			continue

		con.close()

		c_age=p_age=t_age=-1
		limit = 60*60*24

		logger.info("Site '%s' at %s" % (name,url))

		if s_u_core:
			c_age,core_version,core_updates =  parse_core_to_dict(s_u_core)
		else:
			logger.error("No information on Wordpress Core updates for %s (%s)" % (name,url))

		if s_u_themes:
			t_age,t_checked,t_updates    =  parse_themes_to_dict(s_u_themes)
		else:
			logger.error("No information on Wordpress Theme updates for %s (%s)" % (name,url))

		if s_u_plugins:
			p_age,p_checked,p_updates    =  parse_plugins_to_dict(s_u_plugins)
		else:
			logger.error("No information on Wordpress Plugin updates for %s (%s)" % (name,url))


		# warning, below it really gets ugly....


		if c_age > limit or p_age > limit or t_age > limit:
			# FIXME: action to perform besides printing a warning?
			logger.error("ERROR: Site '%s': Some or all checks are outdated! Check your Cronjob for the site!" % site.name)

		logger.info("%s: last checks - core: %.0f secs ago, plugins: %.0f secs ago, themes: %.0f secs ago" %\
					(site.name,c_age,p_age,t_age) )

		print
		underline("Report for site '%s'" %site.name,'=')
		underline("Core")

		core_error=False

		if not s_u_core:
			print "   - NOT checked - no data!"
			core_error=True

		if c_age > limit:
			print "   - check is outdated: Last check was %.0f seconds ago!" % c_age
			core_error=True


		if s_u_core:
			# Okay, we have core data, lets try to check them

			logger.info("Site %s running at Wordpress %s" % (site.name,core_version))
			print "   - Version running: %s" % core_version

			if len(core_updates)==0:
				logger.error ("Site '%s': No results of core update check recorded. Running at %s" % (site.name,core_version))
				print "   - No results of core update check recorded!"
				core_error=True
			elif len(core_updates)>1:
				logger.error("DB contents not supported, found more than one cores? site: %s" % site.name)
				print "   - Internal error interpreting check data!"
				core_error=True
			else:
				data=core_updates[0]

				try:
					available_version =  data['current']

					if core_version!=available_version:
						# FIXME: action to perform besides printing a warning?
						logger.error("Site '%s' is running Wordpress %s while %s is available!"    % (site.name,core_version,available_version))
						print "   - Version %s is available!" % (available_version)
						core_error=True
					else:
						print "   - Version  %s is latest available!" % (available_version)

				except Exception,e:
					logger.error('Unable to cope with database contents: %s' % e)
					print "   - Internal error interpreting check data!"
					core_error=True



		print
		underline("Plugins")

		plugin_error=False

		if not s_u_plugins:
			print "   - NOT checked - no data!"
			plugin_error=True
		if p_age > limit:
			print "   - check is outdated: Last check was %.0f seconds ago!" % p_age
			plugin_error=True

		if s_u_plugins:
			# We have plugin data, yay!

			if len(p_checked)==0:
				# or maybe not...
				print "   - No Plugins installed"

			#items() is a copy, so we can remove elements in the end
			for plugin,version in p_checked.items():
				logger.info( "Site %s: found plugin %s, version %s" % (site.name, plugin,version) )

				print "   - Plugin %s - Version %s" % (plugin,version)

				if plugin in p_updates:
					update_info= p_updates[plugin]
					if 'new_version' in update_info:
						new_version=update_info['new_version']
						print "   -> Update on %s available!" % (new_version)
						plugin_error=True
					else:
						print "   -> No update available or no auto update."
					del(p_updates[plugin])

			#make sure we did not miss anything
			for plugin,data in p_updates.items():

				print "   - Plugin %s - Version unknown!" % (plugin)
				plugin_error=True
				if 'new_version' in data:
					new_version=data['new_version']
					print "   -> Update on %s available!" % (new_version)


		print
		underline("Themes")

		theme_error=False

		if not s_u_themes:
			print "   - NOT checked - no data!"
			theme_error=True
		if t_age > limit:
			print "   - check is outdated: Last check was %.0f seconds ago!" % t_age
			core_error=True

		if s_u_themes:

			if len(t_checked)==0:
				print "   - No themes installed"


			#items() is a copy, so we can remove elements in the end
			for theme,version in t_checked.items():
				logger.info( "Site %s: found theme %s, version %s" % (site.name, theme,version) )

				print "   - Theme  %s - Version %s" % (theme,version)

				if theme in t_updates:
					update_info= t_updates[theme]
					if 'new_version' in update_info:
						new_version=update_info['new_version']
						print "   -> Update on %s available!" % (new_version)
						theme_error=True
					else:
						print "   -> No update available or no auto update." 
					del(t_updates[theme])

			# for some reason I found plugins here that are not mentioned in the other 
			# deserialzed php opject...

			for theme,data in t_updates.items():
				print "   - Theme %s - Version unknown!" % (plugin)
				theme_error=True
				if 'new_version' in data:
					new_version=data['new_version']
					print "   -> Update on %s available!" % (new_version)


		print
		underline("Summary")

		if core_error:
			print " ERROR: Site %s is running an outdated Wordpress version or the check failed. " % site.name
		else:
			print " OK: Site %s is running the latest Wordpress Core. " % site.name

		if plugin_error:
			print " ERROR: Site %s is running outdated plugins or a check failed. " % site.name
		else:
			print " OK: Site %s is running the latest Wordpress Plugins. " % site.name


		if theme_error:
			print " ERROR: Site %s is running outdated themes or a check failed. " % site.name
		else:
			print " OK: Site %s is running the latest Wordpress Themes. " % site.name

		print






