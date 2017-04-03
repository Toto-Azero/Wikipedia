#!/usr/bin/python
# -*- coding: utf-8  -*-

"""
Avertissement des nouveaux ayant reçu une réponse à leur question sur le [[WP:Forum des nouveaux]]
et sur [[WP:Forum des nouveaux/relecture]].

Dernières modifications :
* 0570 : résolution bug prise en charge titre de section avec un slash ('/') ou deux points (':')
* 0569 : mise à niveau eqiad
* 0568+ : vérification de la sauvegarde de l'oldid
* 0568 : changement modèle réponse : [[Utilisateur:ZéroBot/Forum des nouveaux/Réponse]]
* 0550 : précisions logs
* 0549 : traitement de plusieurs pages, recherche du demandeur améliorée
		 (avec détection d'un éventuel titre du type "Question déposée par …"
* 0502+ : pas d'avertissement pour les demandeurs autopatrolled.
"""

#
# (C) Toto Azéro, 2012-2013
#
# Distribué sous licence GNU GPLv3
# Distributed under the terms of the GNU GPLv3 license
# http://www.gnu.org/licenses/gpl.html
#
__version__ = '0600'
__date__ = '2017-04-03 11:35:20 (CEST)'
#
import pywikibot
from pywikibot import flow
import complements
import re
import urllib
import _mysql
import almalog2

class AnalyserBot:
	database = None
	def __init__(self, main_page):	
		self.les_mois = (
		u"janvier",
		u"février",
		u"mars",
		u"avril",
		u"mai",
		u"juin",
		u"juillet",
		u"août",
		u"septembre",
		u"octobre",
		u"novembre",
		u"décembre"
		)
		
		self.site = pywikibot.Site()
		self.page_forum_nouveaux = main_page
		self.id_sql = self.page_forum_nouveaux.title().strip().encode('utf-8')
		self.match_title = re.compile(u"(\n|^)== *([^=].+[^=]) *==")
		self.match_date = re.compile(u"(?P<day>[0-9]+) *(?P<month>[^ ]+) *(?P<year>20[0-9]{2}) *à *(?P<hours>[0-9]{2}):(?P<minutes>[0-9]{2})")
		
		self.history = self.get_history(self.page_forum_nouveaux)
		if not self.history:
			pywikibot.output(u"Erreur : aucun historique existant !")
			return
		
		self.id = ''
		if main_page.title().split("/")[-1] != u"Wikipédia:Forum des nouveaux":
			 self.id = main_page.title().split("/")[-1]
		
		
		# Les variables suivantes contiennent chacune différentes
		# informations, révision après révision de l'historique.
		#
		# self.history_text est uniquement une liste contenant le wikitexte
		# révision après révision.
		# self.history_titles est une liste de dict comme suit :
		#  [{0:'== titre 1 ==', 1: '== titre 2==', 2: '== titre 3=='}},
		#   {0:'== titre 1 ==', 1: '== titre 2=='}]
		# self.history_sections est également une liste de dict comme suit :
		#  [{'== titre 1 ==': 'contenu section 1', '== titre 2 ==': 'contenu section 2',
		#  '== titre 3 ==': 'contenu section 3'}, {'== titre 1 ==': 'contenu section 1',
		#  '== titre 2 ==': 'contenu section 2'}]
		self.history_text = [history_entry[3] for history_entry in self.history]
		self.history_titles = [complements.extract_titles(text, beginning = None, match_title = self.match_title) for text in self.history_text]
		self.history_sections = [complements.extract_sections_with_titles(text, beginning = None, match_title = self.match_title) for text in self.history_text]
		
		self.database = None
		
		self.reset_analyse_sections()
		
		# Listes des sections pour lesquelles le demandeur a déjà été averti.
		# Permet d'éviter d'avertir plusieurs fois d'affilée le demandeur
		# pendant le même lancement du script.
		self.sections_warned = list()

	def reset_analyse_sections(self):
		# Permet de remettre à zéro les variables utiles dans l'analyse 
		# des sections créées, supprimées ou modifiées.
		# Ces variables ne servent que lors de la comparaison de deux versions
		# puis sont réinitialisées à la boucle suivante.
		self.new_sections = []
		self.edited_sections = []
		self.deleted_sections = []
	
	def get_history(self, page, oldid = None):
		"""
		@param oldid : oldid de la dernière version à récupérer.
					   Laisser à None ou à False pour la récupérer depuis
					   la base SQL.
		"""
		# ‹!› Penser à inverser l'historique : les versions les plus
		#     anciennes viennent d'abord ! (cf. infra)
		if not oldid:
			oldid = self.get_oldid()
		
		pywikibot.output('Getting history after oldid %i' % oldid)
		if oldid:
			# ‹!› Bien laisser le paramètre rvdir à True pour permettre
			# 	  l'inversion de l'historique (cf. supra) 
			pywikibot.output(page)
			self.site.loadrevisions(page = page, getText = True, startid = oldid, rvdir = True)
			history = [(page._revisions[rev].revid,
						page._revisions[rev].timestamp,
						page._revisions[rev].user,
						page._revisions[rev].text
					   ) for rev in sorted(page._revisions)
					  ]
			return history
		else:
			pywikibot.output(u"Erreur lors de la récupération de l'oldid dans la base de donnée SQL")		
			return None
			
	def make_database(self):
		if not self.database:
			self.database = _mysql.connect(host='tools-db', db='s51245__totoazero', read_default_file="/data/project/totoazero/replica.my.cnf")
			pywikibot.output(u"Database initialized.")
			
	def get_oldid(self):
		self.make_database()
		pywikibot.output(u"Getting oldid with id %s." % self.id_sql.decode('utf-8'))
		self.database.query('SELECT * FROM oldid_forum_nouveaux WHERE id=\'%s\'' % self.id_sql)
		results = self.database.store_result()
		pywikibot.output(results)
		if results:
			oldid=results.fetch_row(maxrows=0)
			pywikibot.output(oldid)
			if len(oldid):
				oldid = int(oldid[0][0])
				pywikibot.output('Found oldid %i' % oldid)
				return oldid
			else:
				return None
		else:
			return None
	
	def save_oldid(self, oldid):
		"""
		@type oldid : int
		"""
		self.make_database()
		pywikibot.output("Deleting entry for id '%s'" % self.id_sql)
		self.database.query('DELETE FROM oldid_forum_nouveaux WHERE id=\'%s\'' % self.id_sql)
		
		results = None
		while not results:
			self.make_database()
			pywikibot.output("Saving oldid %i for id '%s'" % (oldid, self.id_sql))
			self.database.query('INSERT INTO oldid_forum_nouveaux VALUES ("%i", CURRENT_TIMESTAMP, \'%s\')' % (oldid, self.id_sql))
			self.database.query('SELECT * FROM oldid_forum_nouveaux WHERE id=\'%s\'' % self.id_sql)
			results = self.database.store_result()
		
		pywikibot.output(u"Last oldid analyzed (%i) saved into SQL database." % oldid)
		
	def analyse(self, history):
		list_for_i = range(len(history) - 1)
		# i va prendre toutes les valeurs en partant de 0 jusqu'au nombre
		# d'entrées de l'historique moins un.
		# Il est nécessaire d'enlever un au nombre d'entrées de l'historique
		# afin de pouvoir toujours comparer deux versions entre elles.
		
		# Analyse de l'historique en comparant toujours deux entrées ente elles
		for i in list_for_i:
			self.reset_analyse_sections()
			#print "i = %i" % i
			list_old_titles = self.history_titles[i]
			list_new_titles = self.history_titles[i+1]
			
			list_old_sections = self.history_sections[i]
			list_new_sections = self.history_sections[i+1]
			
			if not (list_old_titles and list_new_titles):
				pywikibot.output(u"Erreur : une liste des titres est vide ! (entrée n°%i ou %i)" % (i, i+1))
				continue
			
			if not (list_old_sections and list_new_sections):
				pywikibot.output(u"Erreur : une liste des sections est vide ! (entrée n°%i ou %i)" % (i, i+1))
				continue
			
			if len(list_new_sections) > len(list_old_sections):
				# Une ou plusieurs section(s) ont été créée(s)
				#self.new_sections = True
				pywikibot.output(u"\03{lightgreen}%i nouvelle(s) section(s) dans l'entrée n°%i\03{default} (diff avec n°%i)" % (len(list_new_sections) - len(list_old_sections), i+1, i))
			
			# Analyse des sections des deux entrées, une à une, par comparaison
			for j in range(len(list_old_titles)):
				current_title = list_old_titles[j]
				old_section = list_old_sections[current_title]
				if list_new_sections.has_key(current_title):
					new_section = list_new_sections[current_title]
					
					# Pour voir si une réponse ou un commentaire a été ajouté(e),
					# on compare le nombre de dates de signatures dans chacune
					# des deux versions de la même sections (avant et après).
					if len(re.split(self.match_date, new_section)) > len(re.split(self.match_date, old_section)):
						pywikibot.output(u"\03{lightpurple}section %s modifiée dans l'entrée n°%i\03{default} (diff avec n°%i)" % (list_old_titles[j], i+1, i))
						self.edited_sections.append(list_old_titles[j])
						demandeur = self.return_demandeur(old_section)
						if demandeur:
							userReponse = pywikibot.User(self.site, self.history[i+1][2])
							time = self.history[i+1][1]
							oldid = self.history[i][0]
							newid = self.history[i+1][0]
							self.warn_demandeur(demandeur, list_old_titles[j], userReponse, time, oldid, newid)
				else:
					# Si la section n'est pas dans la liste de la nouvelle entrée,
					# alors c'est qu'elle a été supprimée.
					pywikibot.output(u"\03{lightred}section %s supprimée dans l'entrée n°%i\03{default} (diff avec n°%i)" % (list_old_titles[j], i+1, i))
					self.deleted_sections.append(list_old_titles[j])

				if self.new_sections and len(self.new_sections) == len(self.deleted_sections):
					pywikibot.output(u"\03{lightblue}%i renommage(s) potentiel(s) dans l'entrée n°%i\03{default} (diff avec n°%i)" % (len(self.new_sections), i+1, i))
	
	def return_demandeur(self, section):
		try:
			if (u"Message déposé par {{u|" in section) or (u"Question déposée par {{u|" in section):
				pywikibot.output(u"Demandeur trouvé")
				name = re.search(u'\n(?:Message déposé|Question déposée) par \{\{u\|([^\|}]+)\}\}', section).group(1)
			elif (u"Message déposé par [[Utilisateur" in section) or (u"Question déposée par [[Utilisateur" in section):
				pywikibot.output(u"Demandeur enregistré")
				name = re.search(u'\n(?:Message déposé|Question déposée) par \[\[Utilisateur:([^\|]+)\|', section).group(1)
			elif (u"Message déposé par [[Spécial:Contributions" in section) or (u"Question déposée par [[Spécial:Contributions" in section):
				pywikibot.output(u"Demandeur anonyme")
				name = re.search(u'\n(?:Message déposé|Question déposée) par \[\[Spécial:Contributions/([0-9\.]+)\|', section).group(1)
			else:
				pywikibot.output(u"Type de demandeur inconnu")
			#name = re.search(u"<!-- Ne PAS MODIFIER cette ligne si vous souhaitez être averti par un bot lorsque quelqu'un apportera une réponse à votre demande. $user:\[\[Utilisateur:(.+)\|\\1\]\]$ -->", section).group(1)
			pywikibot.output(name)
			user = pywikibot.User(self.site, name)
			if user.isRegistered() or user.isAnonymous():
				return user
			else:
				return False
		except Exception, myexception:
			print type(myexception), myexception.args
			pywikibot.output(u"Erreur lors de la détection du demandeur !")
			return None
	
	def warn_demandeur(self, demandeur, section, user, time, oldid, newid):
		# @type user : pywikibot.User
		# @type time : ISO 8601 timestamp
		
		if u'autopatrolled' in demandeur.groups():
			pywikibot.output(u'demandeur autopatrolled : inutile de laisser un message')
			return False
		
		if demandeur == user:
			# L'utilisateur a fait une modification sur une section
			# qu'il a créé, inutile donc de l'en avertir.
			return False
		
		if section in self.sections_warned:
			# L'utilisateur vient déjà d'être averti d'une modification
			# antérieure, inutile de flooder sa PdD.
			pywikibot.output(u'Déjà averti une fois !')
			return False
		
		titre_section = section.strip('= ')
		titre_section_MediaWiki = titre_section.replace("[[", "").replace("]]", "")
		titre_section_MediaWiki = urllib.quote(titre_section_MediaWiki.encode('utf-8'), safe=" :").replace(" ", "_").replace("%", ".")
		
		talk_page = demandeur.getUserTalkPage()
		
		comment = u"/* Concernant votre demande sur le Forum des nouveaux */ nouvelle section"
		pywikibot.output(time)
		ts = pywikibot.Timestamp.fromISOformat(str(time))
		pywikibot.output('phase 1')
		date = u"le %s %s à %s" % (ts.strftime(u"%d"), self.les_mois[int(ts.strftime(u"%m")) - 1], ts.strftime(u"%H:%M"))
		
		#warning_message = u"{{subst:Wikipédia:Forum des nouveaux/Réponse|%s|~~~~|user=%s|date=%s (UTC)|oldid=%s}}" % (titre_section_MediaWiki, user_text, date, newid)
		
		
		if talk_page.isRedirectPage():
			talk_page = talk_page.getRedirectTarget()
		
		if talk_page.isFlowPage():
			board = flow.Board(talk_page)
			warning_message = u"\n\n{{subst:Utilisateur:ZéroBot/Forum des nouveaux/Réponse|%s|~~~~|user=%s|oldid=%s|id=%s|titre=0}}" % (titre_section_MediaWiki, user.name(), newid, self.id)
			pywikibot.output(warning_message)
			board.new_topic(u'Concernant votre demande sur le Forum des nouveaux', warning_message)	
		else:
			if not talk_page.exists():
				text = u""
			else:
				text = talk_page.get()
			
			warning_message = u"\n\n{{subst:Utilisateur:ZéroBot/Forum des nouveaux/Réponse|%s|~~~~|user=%s|oldid=%s|id=%s|titre=1}}" % (titre_section_MediaWiki, user.name(), newid, self.id)
			pywikibot.output(warning_message)
			text += warning_message
			if not talk_page.exists():
				text = text.strip()
			pywikibot.output(text)

			talk_page.put(text, comment, minorEdit=False)
		
		self.sections_warned.append(section)
		return True
		
	def run(self):
		self.analyse(self.history)
		self.save_oldid(self.history[-1][0])

def warn_Frakir():
	pass
#	check_page = pywikibot.Page(site, u"Utilisateur:ZéroBot/warned")
#	check_chain = u"true"
#	if check_page.get() == check_chain:
#		return 2
#	
#	pdD_Frakir = pywikibot.Page(site, u"Discussion utilisateur:Frakir")
#	text = pdD_Frakir.get() + u"\n\n== Houston… on a un problème ! ==\nJ'ai rencontré une erreur et n'ai pas pu effectuer correctement mon travail d'avertissement concernant le [[WP:Forum des nouveaux]]. ~~~~"
#	pdD_Frakir.put(text, comment=u"Houston… on a un problème !", minorEdit=False)
#	
#	check_page.put(check_chain, comment="", minorEdit=False)
#	
#	return 1
	
def main():
	site = pywikibot.Site()
	list_pages_titles = (u"Wikipédia:Forum des nouveaux", u"Wikipédia:Forum des nouveaux/relecture")
	list_pages = (pywikibot.Page(site, page_title) for page_title in list_pages_titles)
	for page in list_pages:
		bot = AnalyserBot(main_page=page)
		bot.run()

if __name__ == '__main__':
	try:
		main()
	except Exception, myexception:
		print type(myexception), myexception.args
		almalog2.error(u'forum_nouveaux', u'%s %s'% (type(myexception), myexception.args))
		if not warn_Frakir():
			pywikibot.output(u"Erreur : aucun message n'a pu être laissé à Frakir ([[fr:User talk:Frakir]]).")
		raise
	finally:
		pywikibot.output(u"\n----------------------------\n")
		pywikibot.stopme()
