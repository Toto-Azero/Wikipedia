#!/usr/bin/python
# -*- coding: utf-8  -*-
"""

Dernières modifications :
* 0001 : Première version
"""
#
# (C) Toto Azéro, 2015
#
# Distribué sous licence GNU GPLv3
# Distributed under the terms of the GNU GPLv3 license
# http://www.gnu.org/licenses/gpl.html
#
__version__ = '$Id: mort_recente.py 0001 2015-10-30 13:55:17 (CET) Toto Azéro $'
#

import pywikibot
from pywikibot import textlib
import _errorhandler
import re, time, datetime
import locale
import _mysql

class BotMortRecente:
	def __init__(self):
		self.site = pywikibot.Site()
		self.modele = pywikibot.Page(self.site, u"Modèle:Mort récente")
		
		self.threshold = 7
		self.delai_mini = 7
		self.laps = 5
		self.delai_maxi = 15
	
	def find_add(self, page):
		"""
		Returns (user, oldid, timestamp) where
		  * user is the user who added the {{Mort récente}} template
			 (pywikibot.User)
		  * oldid is the oldid of the revision of this add
			 (int)
	 	  * timestamp
		"""
		death_found = True
		history = page.getVersionHistory()
	
		if len(history) == 1:
			[(id, timestamp, user, comment)] = history
			return (pywikibot.User(self.site, user), id)
	
		oldid = None
		requester = None
		timestamp = None
		previous_timestamp = None
		
		for (id, timestamp, user, comment) in history:
			pywikibot.output("Analyzing id %i: timestamp is %s and user is %s" % (id, timestamp, user))
		
			text = page.getOldVersion(id)
			templates_params_list = textlib.extract_templates_and_params(text)
			death_found = False
			for (template_name, dict_param) in templates_params_list:
				try:
					template_page = pywikibot.Page(pywikibot.Link(template_name, self.site, defaultNamespace=10), self.site)
					
					# TODO : auto-finding redirections
					if template_page.title(withNamespace=False) in [u"Mort récente", u"Décès récent"]:
						death_found = True
						break
				except Exception, myexception:
					pywikibot.output(u'An error occurred while analyzing template %s' % template_name)
					pywikibot.output(u'%s %s'% (type(myexception), myexception.args))
		
			if oldid:
				print("id is %i ; oldid is %i" % (id, oldid))
			else:
				print("id is %i ; no oldid" % id)
			if not death_found:
				if id == oldid:
					pywikibot.output("Last revision does not contain any {{Mort récente}} template!")
					return None
				else:
					pywikibot.output(u"-------------------------------------")
					triplet = (requester, oldid, previous_timestamp)
					pywikibot.output(u"Found it: user is %s; oldid is %i and timestamp is %s" % triplet)
					return triplet
			else:
				requester = pywikibot.User(self.site, user)
				oldid = id
				previous_timestamp = timestamp
	
		# Si on arrive là, c'est que la première version de la page contenait déjà le modèle
		return (pywikibot.User(self.site, user), id, timestamp)
	
	def check_add_sql(self, page):
		database = _mysql.connect(host='tools-db', db='s51245__totoazero', read_default_file="/data/project/totoazero/replica.my.cnf")
		database.query('SELECT added FROM mort_recente WHERE page = "%s"' % page.title(asLink=False).replace('"', '\\"').encode('utf-8'))
		results=database.store_result()
		result=results.fetch_row(maxrows=0)
		if not result:
			(user, oldid, timestamp) = self.find_add(page)
			database = _mysql.connect(host='tools-db', db='s51245__totoazero', read_default_file="/data/project/totoazero/replica.my.cnf")
			database.query('INSERT INTO mort_recente VALUES ("%s", %i, "%s")' % (page.title(asLink=False).replace('"', '\\"').encode('utf-8'), oldid, timestamp.strftime("%Y-%m-%d %H:%M:%S")))
			return timestamp
		else:
			return pywikibot.Timestamp.strptime(result[0][0], "%Y-%m-%d %H:%M:%S")
	
	def check_contributions(self, page):
		history = page.getVersionHistory()
		delay = datetime.timedelta(days=self.laps)
		
		count = 0
		now = pywikibot.Timestamp.now()
		date = now - delay
		
		timestamp = history[0].timestamp # pywikibot.Timestamp
		while timestamp >= date and count<(len(history)-1):
			count += 1
			timestamp = history[count].timestamp
		
		return count # nombre d'éditions sur les $delay derniers jours
	
	def operate(self, page):
		added_timestamp = self.check_add_sql(page) # pywikibot.Timestamp
		
		now = pywikibot.Timestamp.now()
		date_mini =  added_timestamp + datetime.timedelta(days=self.delai_mini)
		date_maxi = added_timestamp + datetime.timedelta(days=self.delai_maxi)
		
		remove = False
		comment = None
		
		pywikibot.output("added_timestamp: %s" % added_timestamp)
		pywikibot.output("date_maxi: %s" % date_maxi)
		pywikibot.output("date_mini: %s" % date_mini)
		if now > date_maxi:
			# présent depuis plus de self.delai_maxi jours
			remove = True
			comment = u"Bot: Suppression du [[modèle:Mort récente]] présent depuis plus de %i jours" % self.delai_maxi
		elif now > date_mini:
			count_contributions = self.check_contributions(page)
			if count_contributions < self.threshold:
				remove = True
				comment = u"Bot: Suppression du [[modèle:Mort récente]] (%i modification(s) dans les %i derniers jours)" % (count_contributions, self.laps)
			else:
				pywikibot.output("Nothing to do: activity is high")
		else:
			pywikibot.output("Nothing to do: out of delays")
		
		if remove:
			text = page.get()
			text = re.sub(u"\{ *\{ *([Mm]ort récente|[Dd]écès récent).* *\} *\}\n", "", text)
			pywikibot.output("Removing : %s" % comment)
			page.put(text, comment = comment)
					
	def run(self):
		pywikibot.output(u"Initialisation… Date : %s" % datetime.datetime.now())
		
		# Génère la liste des pages à traiter
		#pywikibot.output(self.modele)
 		liste_pages_a_traiter = [page for page in self.modele.getReferences(content=True, namespaces=[0], follow_redirects=True)]

		if not liste_pages_a_traiter:
			pywikibot.output(u"No page to be treated")
			return
				
		# Analyse page par page
		for page in liste_pages_a_traiter:
			pywikibot.output(u"\nAnalysing %s" % page.title(asLink=True))
			liste_pages_modeles = [couple[0] for couple in page.templatesWithParams()]

			self.operate(page)
		
def main():
	bot = BotMortRecente()
	bot.run()

if __name__ == "__main__":
	locale.setlocale(locale.LC_ALL, 'fr_FR.utf8')
	try:
		main()
	except Exception, myexception:
		_errorhandler.handle(myexception)
		raise
	finally:
		pywikibot.stopme()