#!/usr/bin/python
# -*- coding: utf-8  -*-

"""
Classement et archivage des requêtes aux sysops (génération 2.0).

Ce script classe les requêtes d'une page de requêtes aux sysops et a été
conçu pour faciliter la recherche dans les archives.

Différences avec la génération 1.0 :
	- les requêtes doivent posséder un paramètre "traitée", à remplir par 'oui'
		lorsque la requête a été traitée.
	- suppression de l'ancien paramètre "statut", suite à la fin de la
		différenciation requête acceptée/requête refusée.
	- archivage par semaine : toutes les requêtes traitées dans la même semaine
		se retrouveront sur la même page d'archive, des pages mensuelles et
		annuelles centralisant plusieurs pages d'archives hebdomadaires.

NB : La suppression des requêtes traitées reste toujours possible.

Dernières corrections :
* 3400 : PutQueue with safe_put : tout publier d'un coup,
         pour chaque page de requêtes
* 3252 : gestion (pas très propre) du paramètre "encours"
* 3250 : résolution du "bug de la nouvelle année", qui conduisait le bot
		 à mal archiver les requêtes de la dernière semaine de l'année
* 3238 : gestion éventuels espaces dans paramètres modèle type {{RA début}}
* 3235 : correction erreur archivage 1ère semaine de l'année
"""

#
# (C) Toto Azéro, 2011-2016
#
# Distribué sous licence GNU GPLv3
# Distributed under the terms of the GNU GPLv3 license
# http://www.gnu.org/licenses/gpl.html
#
__version__ = '3400'
__date__ = '2016-11-04 19:02:10 (CET)'
#

import almalog2
import pywikibot
from pywikibot import config, page, textlib
import locale, re, sys
import datetime
import complements

class PutQueue:
	def __init__(self):
		self.queue = []
	
	def add(self, page, text, comment):
		self.queue.append((page, text, comment))
	
	def safe_put(self, page, text, comment):
		try:
			page.put(text, comment = comment)
		except pywikibot.SpamfilterError as errorBlacklist:
			text.replace(errorBlacklist.url, "<nowiki>%s</nowiki>" % errorBlacklist)
			self.site.unlock_page(page) # Strange bug, page locked after the error
			page.put(text, comment = comment)
	
	def put_all(self):
		total_put = 0
		try:
			for li in self.queue:
				page, text, comment = li
				self.safe_put(page, text, comment)
				total_put += 1
		except Exception, myexception:
			#e = sys.exc_info()
			#pywikibot.output(e)
			
			if total_put == 0:
				pywikibot.output("WARNING: Nothing was put, and nothing will be")
				raise myexception
			else:
				pywikibot.output("CRITICAL: Some things were put, you may have to undo changes!")
				almalog2.error('sysops_archives_new', '\nWhile doing %s\nCRITICAL: Some things were already put, you may have to undo changes!'
						% page.title())
				raise myexception

class TreatementBot:
	def __init__(self, raccourci):
		"""
		Initialisation du bot.
		Chaque raccourci correspond à une page de requêtes aux admins et entraîne
		des traitements différents en fonction des réglages (archivage/suppression,
		délai de classement, etc.).
		
		Définition (entre autres) :
			- du dictionnaire principal (self.dict) contenant :
				* les délais de classement et d'archivage ou de suppression des requêtes
				* la méthode d'« archivage » à employer (archivage classique ou suppression)
			- de la page principale des requêtes (self.main_page)
			- de l'éventuelle page d'archivage des requêtes traitées (self.treated_page)
		"""
		
		self.site = pywikibot.Site('fr', 'wikipedia')
		
		###
		# Définitions spécifiques à la page de requêtes
		###
		if raccourci == 'ra':
			self.dict = {
			'archiver': True,
			'supprimer':False,
			'delai': {'classement': 12, 'archivage': 4*24, 'suppression': None} # En heures,
			}
			
			self.main_page = pywikibot.Page(self.site, u"Wikipédia:Requête aux administrateurs")
			self.treated_page = pywikibot.Page(self.site, u"Wikipédia:Requête aux administrateurs/Requêtes traitées")
			
			self.text_below_waiting_requests = u""
			self.text_below_untreated_requests = u"\n{{Wikipédia:Requête aux administrateurs/Note:Requêtes à traiter}}"
			self.template_prefix = "RA"
			self.template_title = u"%s début" % self.template_prefix
			self.template_end_title = u"%s fin" % self.template_prefix
			self.archivePrefix = u""#u"Archives/"
			
		elif raccourci == 'dph':
			self.dict = {
			'archiver': False,
			'supprimer':True,
			'delai': {'classement': 12, 'archivage': None, 'suppression': 7*24} # En heures,
			}
			
			self.main_page = pywikibot.Page(self.site, u"Wikipédia:Demande de purge d'historique")
			self.treated_page = pywikibot.Page(self.site, u"Wikipédia:Demande de purge d'historique/Requêtes traitées")
			
			self.text_below_waiting_requests = u""
			self.text_below_untreated_requests = u"\n{{Wikipédia:Requête aux administrateurs/Note:Requêtes à traiter}}"
			self.template_prefix = "RA"
			self.template_title = u"%s début" % self.template_prefix
			self.template_end_title = u"%s fin" % self.template_prefix
			self.archivePrefix = u""#u"Archives/"
			
		elif raccourci == 'test':
			self.dict = {
			'archiver': True,
			'delai': {'classement': 12, 'archivage': 4*24 - 12, 'suppression': None} # En heures,
			}
			
			self.main_page = pywikibot.Page(self.site, u"User:ZéroBot/Wikipédia:Requête aux administrateurs")
			self.treated_page = pywikibot.Page(self.site, u"User:ZéroBot/Wikipédia:Requête aux administrateurs/Requêtes traitées")
			
			self.text_below_waiting_requests = u""
			self.text_below_untreated_requests = u"\n{{Wikipédia:Requête aux administrateurs/Note:Requêtes à traiter}}"
			self.template_prefix = "User:ZéroBot/RA"
			self.template_title = u"User:ZéroBot/RA début"
			self.template_end_title = u"RA fin"
			self.archivePrefix = u""#u"Archives/"
		###
		
		self.les_mois = {
		u"janvier": "01",
		u"février": "02",
		u"mars": "03",
		u"avril": "04",
		u"mai": "05",
		u"juin": "06",
		u"juillet": "07",
		u"août": "08",
		u"septembre": "09",
		u"octobre": "10",
		u"novembre": "11",
		u"décembre": "12"
		}
		
		self.match_date = re.compile(u"(?P<day>[0-9]+) *(?P<month>[^ ]+) *(?P<year>20[0-9]{2}) *à *(?P<hours>[0-9]{2}):(?P<minutes>[0-9]{2})")
		self.match_titre_requete = re.compile(u"(\n|^)== *([^=].+[^=]) *==")

	def analyse_section(self, section, template_title = None):
		"""
		Analyse une section et retourne un dictionnaire contenant la date et le statut
		de la section (retourne : {'date': (string), 'traitée': (boolean), 'attendre': (boolean)}).
		Par défaut, le titre du modèle à analyser est celui du modèle correspondant
		à la page de requête associée à la classe (template_title).
		"""
		if not template_title:
			template_title = self.template_title
		
		date = None
		traitee = False
		wait = False
		found = False
		
		templates = textlib.extract_templates_and_params(section)
		# templates est du type :
		#     [(u'RA début', {u'date': u'27 février 2011 à 14:56 (CET)'
		#     , u'traitée': u'oui'}), (u'RA fin', {})]
		# avec éventuellement d'autres modèles, utilisés dans la requête par 
		# les contributeurs, et se trouvant entre le {{RA début}} et le {{RA fin}}
		
		for template in templates:
		# Si le modèle est celui qui annonce le début de la section.
			if template[0] == template_title:
			# On extrait les paramètres utiles (statut et date)
				try:
					date = template[1]['date']
					if template[1][u'traitée'].strip() == 'oui':
						traitee = True
					elif template[1][u'traitée'].strip() in ('attente', 'encours'):
						wait = True
				except:
					pywikibot.output(u"Erreur ! Les paramètres 'date' et 'traitée' ne semblent pas exister !")
					return None
				# On arrête d'analyser les modèles, étant donné qu'on a trouvé
				# celui qui nous intéresse.
				found = True
				break
		
		if found:
			return {'date': date, 'traitée': traitee, 'attente': wait}
		else:
			pywikibot.output(u"Aucun modèle de début trouvé !")
			return None
	
	def classement(self):
		"""
		Classement des requêtes.
		Le bot prend en compte deux statuts, passés par le paramètre 'traitée'
		dans un modèle de début du type {{RA début}} :
			- 'oui' : la requête a été traitée
			- 'attente' : la requête est en attente
		
		Si le paramètre 'traitée' n'est pas renseigné, où s'il ne correspond à aucun
		des deux statuts connus par le bot, celui-ci ignore la requête, et la laisse
		où elle est.
		
		Les requêtes traitées sont classées dès leur que la date renseignée via le
		paramètre 'date' du modèle de début satisfait le délai suivant configuré dans
		le dictionnaire principal self.dict :
			self.dict['delai']['classement'] (en heures)
		
		Les requêtes possédant un statut correct et satisfaisant le délai configuré
		sont supprimées de la section "= Requêtes à traiter =" et sont envoyées
			- sur la page self.treated_page pour les requêtes traitées
				(page définie dans la fonction __init__)
			- dans la section "= Requêtes en attente =" pour les requêtes en attente
		
		Les requêtes précédemment en attente et n'ayant pas changé de statut depuis
		sont laissées telles quelles, dans l'ordre initial, dans la section
		"= Requêtes en attente =".
		
		Aucun paramètre n'est supporté pour cette fonction.
		"""
		self.text = self.main_page.get()
		self.text = self.text.replace(self.text_below_waiting_requests, u'')
		self.text = self.text.replace(self.text_below_untreated_requests, u'')
			
		#print self.text_below_waiting_requests
		#print self.text_below_untreated_requests
		#print self.text
		#print re.search(re.compile(u"= *Requêtes en cours d'examen *= *\n+(.*)\n*= *Requêtes à traiter *=", re.S), self.text)
		
		text_requetes_en_attente = re.search(re.compile(u"= *Requêtes en cours d'examen *= *\n+(.*)\n*= *Requêtes à traiter *=", re.S), self.text).group(1)
		pywikibot.output('text_requetes_en_attente')
		pywikibot.output(text_requetes_en_attente)
		
		pywikibot.output('--------------------------------')
		
		self.text = self.text.replace(text_requetes_en_attente, '')
		self.text = re.sub(u"(= Requêtes à traiter =\n*)\n", u"\\1\n%s" % text_requetes_en_attente, self.text)
		
		#self.text = re.sub(u"(= *Requêtes à traiter *=)", u"\\1%s" % text_requetes_en_attente, self.text)
		text_requetes_a_traiter = re.search(u"= *Requêtes à traiter *=", self.text).group(0)
		
		titres = complements.extract_titles(self.text, beginning = text_requetes_a_traiter, match_title = self.match_titre_requete)
		sections = complements.extract_sections(self.text, titres)
		
		self.text = re.sub(u"(= *Requêtes en cours d'examen *= *)", u"\\1%s" % self.text_below_waiting_requests, self.text)
		self.text = re.sub(u"(= *Requêtes à traiter *= *)", u"\\1%s" % self.text_below_untreated_requests, self.text)
		
		pywikibot.output(self.text)
		
		#for numero_section in sections:
		#	print '--------------------------------'
		#	print sections[numero_section]
		
		# Dictionnaire de classement des requêtes en fonction de
		# leur statut
		dict_requetes_par_statut = {
		'traitée': list(),
		'attente': list(),
		'': list() # requêtes sans statut ou ne répondant pas à la contrainte du délai
		}
		
		if not sections:
			sections = []
				
		for numero_section in sections:
			pywikibot.output('--------------------------------')
			pywikibot.output(sections[numero_section])
			
			analyse = self.analyse_section(sections[numero_section])
			if analyse == None: # Une erreur a eu lieu
				print 'error: an unknown error occurred!'
				continue
			date = analyse['date']
			traitee = analyse['traitée']
			attente = analyse['attente']
			
			if not traitee and not attente:
				# La requête n'a pas été traitée et pourtant elle n'est pas en attente.
				# La requête n'a donc soit pas de statut, soit celui-ci n'est pas
				# reconnu ou pas pris en charge.
				#   ex : statuts 'autre' et 'autreavis'
				continue
			
			if not date and not attente:
				# Si la requête n'a pas de date et n'est pas en attente,
				# on la laisse  l'endroit où elle est, pour éviter de
				# modifier l'ordre d'apparition des requêtes.
				pywikibot.output(u'aucune date renseignée')
				continue
				
			if attente:
				# Si la requête est en attente, on la classe dans le dictionnaire, 
				# on la supprime du texte mais il est inutile d'aller plus loin
				# pour analyser la date, puisqu'elle sera automatiquement classée
				# dans la section "Requêtes en cours d'examen"
				self.text = self.text.replace(sections[numero_section], '')
				dict_requetes_par_statut['attente'].append(sections[numero_section])
				continue
				
			try:
				date = self.match_date.search(date)
				pywikibot.output(date.group('month'))
				
				# Il est préférable de reformater la date, toujours au format string
				# avant de la parser avec la commande datetime.datetime.strptime.
				# Ici, la date est normalisée suivant le format suivant :
				#        jour mois année heures:minutes (tout en chiffres)
				# ex :    13 02 2012 23:34
				# On préfèrera utiliser exclusivement des chiffres pour éviter
				# des problèmes liés aux accents sur le nom de certains mois, 
				# tels février, décembre et août.
				text_date = u"%s %s %s %s:%s" % (date.group('day'), self.les_mois[date.group('month')], date.group('year'), date.group('hours'), date.group('minutes'))
				date = datetime.datetime.strptime(text_date, u"%d %m %Y %H:%M")
				pywikibot.output(date)
			except:
				pywikibot.output(u'erreur: problème avec la date')
				continue
			
			now = datetime.datetime.now()
			#now = now + datetime.timedelta(days=9 - now.day) #debug : pour être le 8#
			
			pywikibot.output(now)
			pywikibot.output(self.dict['delai']['classement'])
			pywikibot.output((now-date))
			pywikibot.output(((now-date).seconds/3600) + (now-date).days*24)
			
			# Si la requête possède le délai requis pour être classée…
			if self.dict['delai']['classement'] <= ((now-date).seconds/3600 + (now-date).days*24):
				pywikibot.output('=> classement')
					
				# …on place la requête dans la liste appropriée…
				dict_requetes_par_statut['traitée'].append(sections[numero_section])
				
				# On supprime la requête de la section des requêtes à traiter.
				self.text = self.text.replace(sections[numero_section], '')
				
			else: # …sinon, on la met dans la liste dict_requetes_par_statut['']
				pywikibot.output('=> pas de classement')
				dict_requetes_par_statut[''].append(sections[numero_section])
				
		##
		# Pour les tests
		##
		for statut in dict_requetes_par_statut:
			pywikibot.output('=================================')
			pywikibot.output(statut)
			for requete in dict_requetes_par_statut[statut]:
				pywikibot.output('--------------------------------')
				pywikibot.output(requete)
		
		pywikibot.output('=================================')
		##
		
		# Récupération des requêtes déjà acceptées/refusées
		# et création des textes adéquats pour chaque type de
		# requêtes.
		text_treated = self.treated_page.get()
		if text_treated:
			while text_treated[-2:] != '\n\n': # Pour rajouter des sauts de lignes si nécessaire.
				text_treated += '\n'
		for requete in dict_requetes_par_statut['traitée']:
			text_treated += requete
		
		text_waiting = ""
		for requete in dict_requetes_par_statut['attente']:
			text_waiting += requete
		
		pywikibot.output('text_waiting')
		pywikibot.output(text_waiting)
		
	#	text_untreated = ""
	#	for requete in dict_requetes_par_statut['']:
	#		text_untreated += requete
	#	
	#	if text_untreated:
	#		while self.text[-2:] != '\n\n': # Pour rajouter des sauts de lignes si nécessaire.	
	#			self.text += '\n'
	#	
	#	self.text += text_untreated
	
	
		if text_waiting:
			# Permet d'avoir deux sauts de lignes après la dernière section,
			# en fin de page
			text_waiting = re.sub("(\n)*$", "\n\n", text_waiting)


		# Mise à jour
		#self.text = re.sub(u"(\n+= *[rR]equêtes *à *traiter *=)", u"%s\\1" % text_waiting, self.text)
		self.text = re.sub(u"\n+(= *[rR]equêtes *à *traiter *= *)", u"\n%s\\1" % text_waiting, self.text)
		
		#page = pywikibot.Page(self.site, u"User:ZéroBot/Wikipédia:Requête aux administrateurs")
		comment = u"Classement des requêtes (%i requête(s) traitée(s), %i requête(s) en attente)" % (len(dict_requetes_par_statut['traitée']), len(dict_requetes_par_statut['attente']))
		pywikibot.output(self.text)
		pywikibot.showDiff(self.main_page.get(), self.text)
		self.put_queue.add(self.main_page, self.text, comment)
		pywikibot.output(comment)
		
		#page = pywikibot.Page(self.site, u"User:ZéroBot/Wikipédia:Requête aux administrateurs/Requêtes traitées")
		comment = u"Classement des requêtes : %i requête(s) traitée(s)" % len(dict_requetes_par_statut['traitée']) 
		self.put_queue.add(self.treated_page, text_treated, comment)
		pywikibot.output(comment)
		
	def archivage(self):
		"""
		Archivage ou suppression des requêtes classées (suivant le paramétrage du
		dictionnaire principal self.dict), dès lors qu'elles satisfont le délai
		configuré (self.dict['delai']['archivage'] et self.dict['delai']['suppression']).
		
		Les requêtes archivées sont transférées vers une sous-page de la page principale
		(self.main_page). Le chemin de cette sous-page est déterminée comme suit :
			self.main_page + '/' + self.archivePrefix + année en cours +
				Semaine XX (semaine en cours)
			ex : Wikipédia:Requête aux administrateurs/2012/Semaine 24
		
		TODO (D):
			- mettre à jour la page principale d'archives lorsqu'une nouvelle page
			  d'archives est créée.
			- vérifier l. 475 (new_text = archive_page.get() + '\\n' + text_to_archive)
		"""

		text = self.treated_page.get()
		
		titres = complements.extract_titles(text, beginning = "", match_title = self.match_titre_requete)
		sections = complements.extract_sections(text, titres)
		
		now = datetime.datetime.now()
		#now = now + datetime.timedelta(days=11 - now.day) #debug : pour être le 11#			
		currentWeekNumber = now.isocalendar()[1]
		previousWeekNumber = currentWeekNumber - 1

		requests_to_archive = {}
		texts_requests_to_archive = {}
		requests_to_delete = []
			
		if not sections:
			sections = []
			
		# Début de la boucle d'analyse de chacune des sections, au cas par cas.
		for numero_section in sections:
			pywikibot.output('--------------------------------')
			pywikibot.output(sections[numero_section])
			
			analyse = self.analyse_section(sections[numero_section])
			
			if not analyse or not analyse['traitée']:
				# Une erreur a eu lieu ou le statut a été modifié
				continue
			
			date = analyse['date']
			
			if not date:
				pywikibot.output(u'erreur : pas de date !')
				continue

			try:
				date = self.match_date.search(date)
				pywikibot.output(date.group('month'))
				
				# Il est préférable de reformater la date, toujours au format string
				# avant de la parser avec la commande datetime.datetime.strptime.
				# Ici, la date est normalisée suivant le format suivant :
				#        jour mois année heures:minutes (tout en chiffres)
				# ex :    13 02 2012 23:34
				# On préfèrera utiliser exclusivement des chiffres pour éviter
				# des problèmes liés aux accents sur le nom de certains mois, 
				# tels février, décembre et août.
				text_date = u"%s %s %s %s:%s" % (date.group('day'), self.les_mois[date.group('month')], date.group('year'), date.group('hours'), date.group('minutes'))
				date = datetime.datetime.strptime(text_date, u"%d %m %Y %H:%M")
				pywikibot.output(date)
			except:
				pywikibot.output(u'erreur: problème avec la date')
				continue

			
			pywikibot.output(now)
			pywikibot.output(self.dict['delai']['classement'])
			pywikibot.output((now-date))
			pywikibot.output(((now-date).seconds/3600) + (now-date).days*24)
			
			if self.dict['archiver']:
			# Si l'archivage des requêtes est activé.
				if self.dict['delai']['archivage'] <= ((now-date).seconds/3600 + (now-date).days*24):
					pywikibot.output(u'=> archivage')
					
					year = date.isocalendar()[0]
					weekNumber = date.isocalendar()[1]
					
					if not requests_to_archive.has_key(year):
						requests_to_archive[year] = {}
						
					if not requests_to_archive[year].has_key(weekNumber):
						requests_to_archive[year][weekNumber] = []
					
					if not texts_requests_to_archive.has_key(year):
						texts_requests_to_archive[year] = {}
					
					if not texts_requests_to_archive[year].has_key(weekNumber):
						texts_requests_to_archive[year][weekNumber] = u""
					
					requests_to_archive[year][weekNumber].append(sections[numero_section])
					texts_requests_to_archive[year][weekNumber] += sections[numero_section]
				else:
					pywikibot.output(u'=> pas d\'archivage')
			
			elif self.dict['supprimer']:
			# Sinon, si leur suppression est activée.
				if self.dict['delai']['suppression'] <= ((now-date).seconds/3600 + (now-date).days*24):
					pywikibot.output(u'=> suppression')
					text = text.replace(sections[numero_section], '')
					requests_to_delete.append(sections[numero_section])
				else:
					pywikibot.output(u'=> pas de suppression')
					
		# Fin de la boucle traitant les sections au cas par cas.
		#
		# Variables requests_to_archive et texts_requests_to_archive complètes, 
		# si l'archivage est activé.
		
		
		if self.dict['archiver']:
			if not len(requests_to_archive):
				# Si rien n'est à archiver, on passe directement 
				# au traitement suivant (de l'autre type de requêtes).
				return
			
			for year in requests_to_archive:
				pywikibot.output('_____________ year : %i _____________' % year)
				for week_number in requests_to_archive[year]:
					for section in requests_to_archive[year][week_number]:
						text = text.replace(section, '')
				
					pywikibot.output('_________ week_number : %i _________' % week_number)
				
					if week_number == 52: # Nouvelle année
						archive_page = pywikibot.Page(self.site, u"%s/%s%i/Semaine %i" % (self.main_page.title(asLink = False), self.archivePrefix, year, week_number))
					else:
						archive_page = pywikibot.Page(self.site, u"%s/%s%i/Semaine %i" % (self.main_page.title(asLink = False), self.archivePrefix, year, week_number))
				
					if archive_page.exists():
						new_text = archive_page.get()
						while new_text[-2:] != '\n\n': # Pour rajouter des sauts de lignes si nécessaire.
							new_text += '\n'
						new_text += texts_requests_to_archive[year][week_number]
					else:
						new_text = texts_requests_to_archive[year][week_number]
			
					# Mise à jour de la page de classement en cours de traitement
					# ainsi que de la apge d'archive
					comment = (u"Archivage de %i requêtes" % len(requests_to_archive[year][week_number]))
					try:
						#pywikibot.showDiff(self.treated_page.get(), text)
						#pywikibot.output('******************************************************')
						#if archive_page.exists():
							#pywikibot.showDiff(archive_page.get(), new_text)
						self.put_queue.add(self.treated_page, text, comment = (comment + u" vers %s" % archive_page.title(asLink = True)))
						
						self.put_queue.add(archive_page, new_text, comment = comment)
					except Exception, myexception:
						pywikibot.output("erreur type 2 : %s %s" % (type(myexception), myexception.args))
						#print u'%s %s' % (type(myexception), myexception.args)
				
			
		elif self.dict['supprimer']:
			comment = (u"Suppression de %i requêtes" % len(requests_to_delete))
			self.put_queue.add(self.treated_page, text, comment = comment)				
				
	def traitement(self):
		"""
		Traitement complet des requêtes aux admins :
			- classement
			- archivage
		"""
		self.put_queue = PutQueue()
		self.classement()
		self.put_queue.put_all()
		self.archivage()
		self.put_queue.put_all()

def main():
	# Configuration de locale
	try:
		locale.setlocale(locale.LC_ALL, 'fr_FR.utf8')
	except:
		locale.setlocale(locale.LC_ALL, 'fr_FR')
	
	liste_raccourcis = ['ra', 'dph']
	
	for raccourci in liste_raccourcis:
		#try:
		pywikibot.output(u"""
************************************************
|              TRAITEMENT DE %s              |
************************************************""" %  raccourci)
		bot = TreatementBot(raccourci = raccourci)
		bot.traitement()
		pywikibot.output(u"""
************************************************
|          FIN DU TRAITEMENT DE %s            |
************************************************""" %  raccourci)
		#except Exception, myexception:
		#	pywikibot.output(u'erreur lors du traitement de %s' % raccourci)
		#	pywikibot.output(u'%s %s' % (type(myexception), myexception.args))
		#	continue
	
if __name__ == '__main__':
    try:
        main()
    except Exception, myexception:
        almalog2.error(u'sysops_archives_new', u'%s %s'% (type(myexception), myexception.args))
        pywikibot.output(u'%s %s' % (type(myexception), myexception.args))
        raise
    finally:
        almalog2.writelogs(u'sysops_archives_new')
        pywikibot.stopme()
