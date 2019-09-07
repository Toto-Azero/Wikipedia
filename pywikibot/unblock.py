#!/usr/bin/python
# -*- coding: utf-8  -*-

"""
Notification aux administrateurs des demandes de déblocage (sur [[WP:RA]])

Dernières modifications :
* 1670 : coupé le texte si possible lorsqu'il est trop long,
         sinon textlib.extract_templates_and_params n'arrive pas à
         extraire tous les modèles et peut sauter {{Déblocage}},
         ce qui conduit à une erreur  
* 1651 : %i non complété
* 1650 : En cas d'erreur lors de la mise à jour de WP:RA (ex: conflit d'édit),
         supprimer les noms d'utilisateurs de la base SQL en l'abscen
         de traitement
* 1611 : Correction erreur encodage
* 1610 : Page créée avec une demande de déblocage,
         paramètre oldid dans la demande aux administrateurs
* 1605 : Ne rapatrie que les demandes faites par le propriétaire de la PdD
* 1540 : Ne rapatrie que les demandes faites en PdD utilisateur
* 1535+ : mise à niveau eqiad
"""

#
# (C) Nakor
# (C) Toto Azéro, 2011-2017
#
# Distribué sous licence GNU GPLv3
# Distributed under the terms of the GNU GPLv3 license
# http://www.gnu.org/licenses/gpl.html
#

__version__ = '$Id: unblock.py 1670 2017-01-29 01:22:07 (CET) Toto Azéro $'

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
		summary = u"%i demandes de déblocages : " % len(usernames_blocked)
		for username in usernames_blocked:
			summary += u"[[User:%s|]] ;" % username
		summary = summary[0:-2]
	else:
		summary = u"/* Demande de déblocage de %s */ nouvelle section" % usernames_blocked[0]
	
	try:
		page.put(text, summary, minorEdit = silent, botflag = silent)
	except Exception, myexception:
		pywikibot.output(u'erreur lors de la mise à jour de WP:RA :\n%s %s'% (type(myexception), myexception.args))
		for username in usernames_blocked:
			database.query('DELETE FROM unblocks WHERE username="%s"' % username.encode('utf-8'))
		raise myexception

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

def find_add(page):
	"""
	Returns (user, oldid) where
	  * user is the user thatwho added the {{Déblocage}} template
	     (pywikibot.User)
	  * oldid is the oldid of the revision of this add
	     (int)
	"""
	site = pywikibot.Site()
	
	unblock_found = True
	history = page.getVersionHistory()
	
	pywikibot.output(u"Analysing page %s" % page.title())
	if len(history) == 1:
		[(id, timestamp, user, comment)] = history
		return (pywikibot.User(site, user), id)
	
	oldid = None
	requester = None
	
	for (id, timestamp, user, comment) in history:
		pywikibot.output("Analyzing id %i: timestamp is %s and user is %s" % (id, timestamp, user))
		
		text = page.getOldVersion(id)
		# text might be too long, if so textlib.extract_templates_and_params won't
		# proceed and will skip some templates
		if u"{{déblocage" in text.lower():
			text = text[max(0,text.lower().index(u"{{déblocage")-12):]
		elif u"{{unblock" in text.lower():
			text = text[max(0,text.lower().index(u"{{unblock")-12):]

		templates_params_list = textlib.extract_templates_and_params(text)
		unblock_found = False
		for (template_name, dict_param) in templates_params_list:
			pywikibot.output((template_name, dict_param))
			try:
				template_page = pywikibot.Page(pywikibot.Link(template_name, site, defaultNamespace=10), site)
				print 1
				pywikibot.output(template_page)
				pywikibot.output(template_page.title(withNamespace=False))
				# TODO : auto-finding redirections
				if template_page.title(withNamespace=False) in [u"Déblocage", u"Unblock"]:
					# le modèle {{déblocage}} peut ne plus être actif
					print 2
					if ((not dict_param.has_key('nocat')) or (dict_param.has_key('nocat') and dict_param['nocat'] in ["non", ''])) and not (dict_param.has_key('1') and dict_param['1'] in ['nocat', 'oui', 'non', u'traité', u'traité', u'traitée', u'traitée']):				
						pywikibot.output('Found unblock request')
						pywikibot.output((template_name, dict_param))
						unblock_found = True
						print 3
						break
			except Exception, myexception:
				pywikibot.output(u'An error occurred while analyzing template %s' % template_name)
				pywikibot.output(u'%s %s'% (type(myexception), myexception.args))
		
		print("id is %i" % id)
		if oldid:
			print("oldid is %i" % oldid)
		else:
			print "no oldid"
		if not unblock_found:
			if id == oldid:
				pywikibot.output("Last revision does not contain any {{Déblocage}} template!")
				return None
			else:
				return (requester, oldid)
		else:
			requester = pywikibot.User(site, user)
			oldid = id
	
	# Si on arrive là, c'est que la première version de la page contenait déjà le modèle
	return (pywikibot.User(site, user), id)

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
		if page.namespace() != 3:
			pywikibot.output(u'Page %s is not in the user talk namespace, skipping.' % userpage)
			continue
		
		(requester, oldid) = find_add(page)
		pywikibot.output(u'Request for unblock has been made by %s in id %i' % (requester, oldid))
		if not requester.username in userpage.split('/')[0]:
			pywikibot.output(u'Request for unblock has been made by %s, who is not the owner of the page %s: skipping' % (requester, userpage))
			continue
		
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
				database = _mysql.connect(host='tools-db', db='s51245__totoazero', read_default_file="/data/project/totoazero/replica.my.cnf")
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
				text+=u'\n{{subst:Utilisateur:ZéroBot/Déblocage|%s|oldid=%i}}' % (username, oldid)
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
		database = _mysql.connect(host='tools-db', db='s51245__totoazero', read_default_file="/data/project/totoazero/replica.my.cnf")
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
		
		global silent
		silent = False
		main()
	except Exception, myexception:
		pywikibot.output(u'%s %s'% (type(myexception), myexception.args))
		if (not debug) and (not silent):
			almalog2.error(u'unblock', u'%s %s'% (type(myexception), myexception.args))
		raise
	finally:
		#almalog2.writelogs(u'unblock')
		pywikibot.stopme()

