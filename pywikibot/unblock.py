#!/usr/bin/python
# -*- coding: utf-8  -*-

#
# (C) Nakor
# (C) Toto Azéro, 2011-2013
#
# Distribué sous licence GNU GPLv3
# Distributed under the terms of the GNU GPLv3 license
# http://www.gnu.org/licenses/gpl.html
#

__version__ = '$Id: unblock.py 1535 2013-08-30 11:45:48 (CEST) Toto Azéro $'

import almalog2
import pywikibot
from pywikibot import pagegenerators, textlib
import re, _mysql, time, urllib

def get_text():
	site = pywikibot.Site()
	pagename = u'Wikipédia:Requête aux administrateurs'
	page=pywikibot.Page(site, pagename)
	
	return page.get()

def put_text(text, usernames_blocked):
	site = pywikibot.Site()
	if debug:
		pagename = u'Utilisateur:ZéroBot/Test2'
		silent=False
	else:
		pagename = u'Wikipédia:Requête aux administrateurs'
		silent=False
	page=pywikibot.Page(site, pagename)
	
	if len(usernames_blocked) > 1:
		summary = u"%i demandes de déblocages : "
		for username in usernames_blocked:
			summary += u"[[User:%s|]] ;" % username
		summary = summary[0:-2]
	else:
		summary = u"/* Demande de déblocage de %s */ nouvelle section" % usernames_blocked[0]
		
	page.put(text, summary, minorEdit = silent, botflag = silent)

def check_open_section(username):
	already_warned = False
	text = get_text()
	
	match = u"== Demande de déblocage de %s ==" % username
	try:
		if (match in text) or debug:
#			if debug:
#				text = u"""== Demande de déblocage de Toto Azéro ==
#{{RA début|traitée=|date=29 mars 2013 à 17:36 (CET)}}
#Test
#{{RA fin}}
#"""
			text = text[text.index(match):]
			text = text[:text.index(u"{{RA fin}}")]
			templates = textlib.extract_templates_and_params(text)
			for template in templates:
				if template[0] == u"RA début":
					if template[1][u'traitée'] != u'oui':
						already_warned = True
	except Exception, myexception:
		pywikibot.output('WARNING: error while looking for any request already posted!')
		pywikibot.output(u'%s %s'% (type(myexception), myexception.args))
	
	pywikibot.output(u"already_warned = %s" % already_warned)
	return already_warned

def main():
	text=False
	database=False
	usernames_blocked = []
	site = pywikibot.Site()
	catname = u'Catégorie:Demande de déblocage'
	
	#DEBUG
	if debug:
		userlist=list()
		userlist.append(pywikibot.Page(site, u'Utilisateur:Toto Azéro'))
		#categ=catlib.Category(site, catname)
		#userlist=categ.articlesList()
	else:
		categ=pywikibot.Category(site, catname)
		userlist=categ.articles()

	# Step one: remove invalid entries
	generator=iter(userlist);
	preloadingGen=pagegenerators.PreloadingGenerator(generator, 60)
	
	#step two: add new entries
	user_list = list()
   
	userlist=list()
	for page in generator:
		userpage=page.title(withNamespace=False)
		username=re.split(u'/', userpage,1)[0]
		pywikibot.output(u'Processing %s' % username)
		userlist.append(username)
		   
		user=pywikibot.User(site,username)
		#try:
# Désactivé : un utilisateur peut être bloqué par un blocage collatéral, or le bot
# ne reporte pas sa demande si il ne détecte pas de blocage.
#		blocked=user.isBlocked()
		blocked = True
		#except userlib.InvalidUser:
		#	params = {
		#		'action'	:'query',
		#		'list'	  :'blocks',
		#		'bkip'	  :username,
		#		}
#
		#	result=query.GetData(params, encodeTitle = False)
		#	blocked=len(result['query']['blocks'])
			
		if (blocked or debug) and not check_open_section(username):
			pywikibot.output("%s is blocked" % username)
			if not database:
				database = _mysql.connect(host='tools-db', db='p50380g50643__totoazero', read_default_file="/data/project/totoazero/replica.my.cnf")
			sqlusername=re.sub(u'\'', u'\'\'', username)
			database.query('SELECT date FROM unblocks WHERE username=\'%s\'' % sqlusername.encode('utf-8'))
			results=database.store_result()
			if results:
			  result=results.fetch_row(maxrows=0)
			  if len(result):
				  for res in result:
					  #date=res[0]
					  #now=datetime.datetime.now()
					  #delta=now-date
					  #print delta
					  #if (delta.days > 0):
					  print res
					  date=time.strptime(res[0], '%Y-%m-%d %H:%M:%S')
					  now=time.gmtime()
					  if (time.mktime(now) - time.mktime(date)) > (24*3600):
						  update=True
						  usernames_blocked.append(username)
						  database.query('DELETE FROM unblocks WHERE username="%s"' % sqlusername.encode('utf-8'))
					  else:
						  update=False
			  else:
				  update=True
				  usernames_blocked.append(username)
			else:
			  update=False
			if update:
				if not text:
					text=get_text()
				text+=u'\n{{subst:Utilisateur:ZéroBot/Déblocage|%s}}' % username
				database.query('INSERT INTO unblocks VALUES (NULL , \'%s\', CURRENT_TIMESTAMP)' % sqlusername.encode('utf-8'))

		elif not check_open_section(username):
			pywikibot.output("%s is not blocked"  % username)
			if not debug:
				usertext=page.get()
				newtext=re.sub(u'\{\{[Dd]éblocage\|(?!nocat)', u'{{Déblocage|nocat=oui|', usertext)
				page.put(newtext, u'Blocage terminé')
		else:
			pywikibot.output("%s is blocked but a request has already been made"  % username)
	
	if not database:
		database = _mysql.connect(host='tools-db', db='p50380g50643__totoazero', read_default_file="/data/project/totoazero/replica.my.cnf")
	database.query('SELECT username FROM unblocks')
	results=database.store_result()
	result=results.fetch_row(maxrows=0)
	for res in result:
		if res[0].decode('utf-8') not in userlist:
			pywikibot.output("Removing %s"% res[0])
			database.query('DELETE FROM unblocks WHERE username="%s"' % res[0])

	if text:
		put_text(text, usernames_blocked)


if __name__ == '__main__':
	try:
		global debug
		debug = False
		main()
	except Exception, myexception:
		pywikibot.output(u'%s %s'% (type(myexception), myexception.args))
		if not debug:
			almalog2.error(u'unblock', u'%s %s'% (type(myexception), myexception.args))
		raise
	finally:
		almalog2.writelogs(u'unblock')
		pywikibot.stopme()

