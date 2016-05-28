#! /usr/bin/python
# -*- coding: utf-8  -*-
"""
Mise à jour des PàS non listées mais catégorisées.

Dernières modifications :
* 1005 : Adaptation aux Labs
"""
#
# (C) Nakor
# (C) Toto Azéro, 2010-2013
#
# Distribué sous licence GNU GPLv3
# Distributed under the terms of the GNU GPLv3 license
# http://www.gnu.org/licenses/gpl.html
#
__version__ = '1005'
__date__ = '2013-08-24 20:57:33 (CEST)'
#
#import wikipedia, catlib, date, config, pagegenerators, userlib, almalog
#import re, time, os, time, codecs, sys, calendar, locale, urllib
import codecs, time, re, calendar
import pywikibot, almalog2
from pywikibot import config, pagegenerators


def tuple_sort(item):
	print item[1]
	sortkey=time.strptime(unicode(item[1]), '%Y-%m-%dT%H:%M:%SZ')
	ordinal=calendar.timegm(sortkey)
	return ordinal
	
# Define the main function
def main():
	# Process command line arguments
	fullmode = False
	debug = 0
	
	for arg in pywikibot.handleArgs():
		if arg.startswith('-full'):
			fullmode = True
		elif arg.startswith('-debug'):
			debug = 1
		else:
			pywikibot.output(u'Syntax: spa.py [-full]')
			exit()

	# Get interesting pages and category
	site = pywikibot.Site()
	
	catname = u'Catégorie:Wikipédien recherchant un parrain'
	pagename = u'Wikipédia:Parrainage_des_nouveaux/Nouveaux_en_attente'
	#pagename = u'Utilisateur:ZéroBot/Test'
	
	if debug:
		mainpage=pywikibot.Page(site, u'Utilisateur:ZéroBot/Tests')
	else:
		mainpage=pywikibot.Page(site, pagename)

	if fullmode:
		#wikipedia.output(u'Liste des utilisateurs à parrainer : mode complet');
		commandLogFilename = config.datafilepath('logs', 'spa.log')
		try:
			commandLogFile = codecs.open(commandLogFilename, 'a', 'utf-8')
		except IOError:
			commandLogFile = codecs.open(commandLogFilename, 'w', 'utf-8')
		# add a timestamp in ISO 8601 formulation
		isoDate = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
		commandLogFile.write("%s Starting ...\n" % isoDate)
	else:
		#wikipedia.output(u'Liste des utilisateurs à parrainer : mode rapide');
		oldpagetext=mainpage.get()

	#DEBUG
	if debug:
		artlist=list()
		#artlist.append(wikipedia.Page(site, u'Utilisateur:Amétisthe67'))
		artlist.append(pywikibot.Page(site, u'Utilisateur:Big 08'))
		artlist.append(pywikibot.Page(site, u'Utilisateur:Guillaume Dürr'))
		#artlist.append(wikipedia.Page(site, u'Utilisateur:Pouding'))
		#artlist.append(wikipedia.Page(site, u'Utilisateur:Grischkaja'))
		#artlist.append(wikipedia.Page(site, u'Utilisateur:Zeynab'))
		#artlist.append(wikipedia.Page(site, u'Utilisateur:Adieptel'))
		#categ=catlib.Category(site, catname)
		#artlist=categ.articlesList()
	else:
		categ=pywikibot.Category(site, catname)
		artlist=categ.articles()

	# Step one: remove invalid entries
	preloadingGen=pagegenerators.PreloadingGenerator(artlist, 60)
	
	#step two: add new entries
	user_list = list()
	time_list = list()
	tuples = list()
	redirectuser = list()
	
	existingusers=''
	for page in artlist:
		userpage=page.title(withNamespace=False)
		username=re.split(u'/', userpage,1)[0]
		#wikipedia.output(u'Processing %s' % username)
		   
		if fullmode:
			commandLogFile.write("   processing %s\n" % username)

		if not fullmode:
			existing=re.search(username, oldpagetext)
 
		if fullmode or not existing:		

			#history = page.getVersionHistory()
			history = page.fullVersionHistory()
			#print history
			history.sort(key=tuple_sort)
			#history.reverse()
			
			spadate=history[0][1]
			#print page.title(withNamespace=False)
			#wikipedia.output(u'#### Original date: %s / %d' % (spadate, len(history)))
			for data in history:
				revisionid=data[0]
				#print data
				#wikipedia.output(revisionid)
				
				try:
					usertext=page.getOldVersion(revisionid)
				except pywikibot.IsRedirectPage:
					redirectuser.append(username)
				except KeyError:
					usertext=''
					
				# We check for the spa model. If not present we do not save the date and keep the previous one when it was added
				spaok=re.search('[P|p]arrainez[-| ]moi', usertext)
				if spaok:
					spadate=data[1]
					#wikipedia.output(spadate)
					break
			   #wikipedia.output(u'#### Intermediate date: %s' % spadate)

			#wikipedia.output(username)
			#username2=username.encode('iso-8859-1')
			#wikipedia.output(username2)
			#urlusername=urllib.quote(username2)
			#wikipedia.output(urlusername)
			#user=userlib.User(site, urlusername)
			user=pywikibot.User(site,username)
			contribs=user.contributions(1)
			contribdate=u''
			for contrib in contribs:
				contribdate=contrib[2]
			   
			tuple=list()
			tuple.append(username)
			tuple.append(spadate)
			tuple.append(contribdate)
			tuples.append(tuple)
			#wikipedia.output(u' .. processed')
		else:
			existingusers+=username+' '
			#wikipedia.output(u' .. skipped')


	tuples.sort(key=tuple_sort)
	#tuples.reverse()
	
	if fullmode:
		newpagetext = u"<noinclude>" + u"""
{{Mise à jour bot|Toto Azéro|période=quotidiennement}}
{{confusion|Special:Newpages}}{{raccourci|WP:NEW}}
</noinclude>
La liste suivante regroupe les wikipédiens en quête d'un parrain. Elle est régulièrement mise à jour par un [[Wikipédia:Bot|robot]]. Suivez cette page si vous souhaitez être informé lorsqu'un nouveau contributeur demande un parrainage.

{| class="wikitable sortable" border="1" cellpadding="5"
|-----\n! Utilisateur\n! Depuis\n! Dernière contribution"""
	else:
		mainsplit=oldpagetext.split(u'\n|{{u|', 1)
		newpagetext=mainsplit[0]+u'\n'
		
	if not fullmode:
		submainsplit=mainsplit[1].split('|{{u|')
		for subsplit in submainsplit:
			#wikipedia.output(u'subsplit:'+subsplit)
			usersplit=subsplit.split('}}')
			stillthere=re.search(usersplit[0], existingusers)
			if stillthere: 
				newpagetext+=u'|{{u|'+subsplit
		splits=newpagetext.split(u'\n\n[[Catégorie:')
		newpagetext=splits[0]

	#curlocale=locale.getlocale()
	#locale.setlocale(locale.LC_ALL, 'fr_FR.UTF-8')
	for tuple in tuples:
		otime=time.strptime(unicode(tuple[1]), '%Y-%m-%dT%H:%M:%SZ')
		ttime1=time.strftime('%d %b %Y', otime)
		try:
		  otime=time.strptime("%d" % tuple[2], '%Y%m%d%H%M%S')
		  ttime2=time.strftime('%d %b %Y', otime)
		  newpagetext+='\n|-----\n|{{u|' + tuple[0] + '}}\n|' + ttime1 + u'\n|' + ttime2
		except TypeError:
		  pass
		except:
		  raise
	#locale.setlocale(locale.LC_ALL, curlocale)
	newpagetext+=u'\n|}\n\n[[Catégorie:Wikipédia:Parrainage]]'
	  

	if debug:
		newpage=pywikibot.Page(site, u'Utilisateur:ZéroBot/Test')
		botflag=True
	else:
		newpage=pywikibot.Page(site, u'Wikipédia:Parrainage_des_nouveaux/Nouveaux_en_attente')		  
		botflag=False
	#newpage=wikipedia.Page(site, u'Utilisateur:ZéroBot/Test')		  
	newpage.put(newpagetext, u'Mise à jour automatique de la liste', minorEdit = botflag, botflag = botflag);
	
	if fullmode and not debug:

		if len(redirectuser)>0:
	  
			logpage=pywikibot.Page(site, u'Utilisateur:ZéroBot/Log/Avertissements')
		
			pagetext=logpage.get()
			pagetext+=u'\n==Utilisateur avec un redirect =='

			for user in redirectuser:
				pagetext+='\n* {{u|' + user + '}}'
		  
			logpage.put(pagetext, u'Utilisateur en attente de parrainage et parrainés', minorEdit = False);

		isoDate = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
		commandLogFile.write("%s Finished.\n" % isoDate)
		#commandLogFile.write(s + os.linesep)
		commandLogFile.close()
	
if __name__ == '__main__':
	try:
		main()
	except Exception, myexception:
		#almalog2.error(u'spa', u'%s %s'% (type(myexception), myexception.args))
		print u'%s %s'% (type(myexception), myexception.args)
		raise
	finally:
		pywikibot.stopme()

