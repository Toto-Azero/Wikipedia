#!/usr/bin/python
# -*- coding: utf-8  -*-
"""
** (fr) **
Ce bot crée les pages du "bistro" (voir [[WP:Le Bistro]]).

Les paramètres suivants sont supportés :

-force			  En plus de créer les pages, écrase celles
				  existantes.

** (en) **
This bot creates pages of "the bistro" (see [[fr:WP:Le Bistro]]).
‹!› This bot has been made to run on fr.wikipedia, running it on
en.wikipedia or another wiki may cause some dammages !

The following parameters are supported:

-force			  In addition of creating pages, overwrites
				  existing ones.
"""
#
# (C) Nakor
# (C) Toto Azéro, 2011-2013
#
# Distribué sous licence GNU GPLv3
# Distributed under the terms of the GNU GPLv3 license
# http://www.gnu.org/licenses/gpl.html
#
__version__ = '$Id: bistro.py 1000 2013-07-11 12:32:24 (CEST) Toto Azéro $'
#
import _errorhandler
import pywikibot
from pywikibot import config, pagegenerators
import locale
from datetime import datetime, timedelta

# Define the main function
def main():
	force = False
	for arg in pywikibot.handleArgs():
		if arg.startswith('-force'):
			force = True
		else:
			pywikibot.output(u'Syntax: bistro.py [-force]')
			exit()

	if config.verbose_output:
		pywikibot.output("Running in VERBOSE mode")

	if len(config.debug_log):
		pywikibot.output("Running in DEBUG mode")


	curlocale=locale.getlocale()

	# Configuration de locale
	try:
		locale.setlocale(locale.LC_ALL, 'fr_FR.utf8')
	except:
		locale.setlocale(locale.LC_ALL, 'fr_FR')

	datetimetarget=datetime.utcnow()+timedelta(15)
	datetimefinal=datetime.utcnow()+timedelta(44)

	date=datetimetarget.strftime('%d %B %Y')
	date=date.decode('utf-8')
	if date[0]=='0':
		date=date[1:]
	if len(config.debug_log):
	  date=u'User:ZéroBot/Wikipédia:Le Bistro/'+date
	else:
	  date=u'Wikipédia:Le Bistro/'+date

	site = pywikibot.Site()
	page=pywikibot.Page(site, date)

	datetimetarget=datetime.utcnow()

	if force or not page.exists():
		pywikibot.output('%s does not exists, creating missing pages' % date)
		titlelist=list()
		while datetimetarget < datetimefinal:
			date=datetimetarget.strftime('%d %B %Y')
			date=date.decode('utf-8')
			if date[0]=='0':
				date=date[1:]
			if len(config.debug_log):
			  date=u'User:ZéroBot/Wikipédia:Le Bistro/'+date
			else:
			  date=u'Wikipédia:Le Bistro/'+date
			page=pywikibot.Page(site, date)
			titlelist.append(page)
			datetimetarget=datetimetarget+timedelta(1)

		gen=iter(titlelist)

		catpreloadingGen=pagegenerators.PreloadingGenerator(gen, 60)

		newtext = u'{{subst:Wikipédia:Le Bistro/préchargement}}'

		for page in catpreloadingGen:
			if not force and not page.exists():
				## Création de la page non-existante
				pywikibot.output('Creating %s' % page.title())
				page.put(newtext, comment='Initialisation de la page', watchArticle = None, minorEdit = False)
			elif force:
				## Écrasement de la page existante
				pywikibot.output(u'Checking %s'% page.title())

				overwrite=False
				if page.exists():
				  history=page.getVersionHistory()
				  if len(history)==1:
					overwrite=True
				else:
				  overwrite=True

				if overwrite:
				  pywikibot.output('Correcting %s' % page.title())
				  page.put(newtext, comment='Initialisation de la page', watchArticle = None, minorEdit = False)

	else:
		pywikibot.output('%s exists, no action needed' % date)


#	locale.setlocale(locale.LC_ALL, curlocale)

if __name__ == '__main__':
	try:
		main()
	except Exception, myexception:
		_errorhandler.handle(myexception)
		raise
	finally:
		pywikibot.stopme()
