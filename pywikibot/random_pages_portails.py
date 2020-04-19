#!/usr/bin/python
# -*- coding: utf-8  -*-

"""
Mise à jour des générateurs de pages de portails aléatoires.

TODO : script à ré-écrire.

Dernières modifications :
* 200 : Adaptation aux Labs
"""

#
# (C) Pywikipedia bot team, 2006-2010
# (C) Toto Azéro, 2012-2013
#
# Distribué sous licence GNU GPLv3
# Distributed under the terms of the GNU GPLv3 license
# http://www.gnu.org/licenses/gpl.html
#

__version__ = '200'
__date= '2013-08-25 16:59:30'
import pywikibot
import re

class RandomBot:
	def __init__(self):
		self.summary = u'Bot: Mise à jour des pages rattachées au portail'
		self.site = pywikibot.Site()
		self.dry = False
		
	def run(self):
		#Dernière actualisation : 20 décembre 2015
				
		liste = [[u"Tunisie"], 
				[u"Catch", u"Modèle:Random catch"],
				[u"Culture"],
				[u"Chimie"],
				[u"Arménie"],
				[u"Humour"],
				[u"Cricket", u"Modèle:Random cricket"],
				[u"Réalisation audiovisuelle"],
				[u"Grèce", u"Modèle:Random Grèce", [u"Grèce", u"Grèce antique"]],
				[u"Football"]]
				#[u"Amérique précolombienne"],
				#[u"Astronautique"],
				#[u"Automobile"],
				#[u"Bagratides"],
				#[u"Islam"],
				#[u"Isère"],
				#[u"Italie"],
				#[u"Québec"],
				#[u"Rome antique"]]
		
		for params in liste:
			try:
				self.majPagesPortails(*params)
			except Exception, myexception:
				pywikibot.output(u"Error with %s" % params[0])
				pywikibot.output(u'%s %s'% (type(myexception), myexception.args))
				
		#self.majPagesPortails(u"Tunisie", u"Modèle:Random Tunisie") 
		#self.majPagesPortails(u"Catch", u"Modèle:Random catch")
		#self.majPagesPortails(u"Culture", u"Modèle:Random Culture")
		#self.majPagesPortails(u"Chimie", u"Modèle:Random Chimie")
		#self.majPagesPortails(u"Arménie", u"Modèle:Random Arménie")
		#self.majPagesPortails(u"Humour", u"Modèle:Random Humour")
		#self.majPagesPortails(u"Cricket", u"Modèle:Random cricket")
		#self.majPagesPortails(u"Réalisation audiovisuelle", u"Modèle:Random Réalisation audiovisuelle")
		#self.majPagesPortails(u"Grèce", u"Modèle:Random Grèce", listePortails = [u"Grèce", u"Grèce antique"])
		#self.majPagesPortails(u"Football", u"Modèle:Random Football")
		#self.majPagesPortails(u"Amérique précolombienne", u"Modèle:Random Amérique précolombienne")
		#self.majPagesPortails(u"Annecy", u"Modèle:Random Annecy")

	def majPagesPortails(self, leNomDuPortail, titrePageRandomArticles=None, listePortails=None):
		"""
		titrePageRandomArticles default is Modèle:Random [leNomDuPortail]
		"""
		
		namespacesAcceptes = [0]
		
		if not titrePageRandomArticles:
			titrePageRandomArticles = u"Modèle:Random %s" % leNomDuPortail
		
		pywikibot.output(u"\n> \03{lightblue}Traitement du portail %s\03{default} <" % leNomDuPortail)
		
		pywikibot.output(u'\03{lightpurple}Recherche des pages rattachées au portail\03{default}…')
		
		if listePortails == None:
			listePortails = [leNomDuPortail]

		listePages = []
		
		x = 0
		for nomPortailCategorie in listePortails:
			x = x + 1
			catTitle = u"Catégorie:Portail:"+ nomPortailCategorie + u"/Articles liés"
			cat = pywikibot.Category(self.site, catTitle)
			if x > 1:
				listePages.append(u"{[COUPURE NOUVELLE PAGE]}")
			listePages.extend(list(cat.articles()))
		
		listePagesASupprimer = []
		for page in listePages:
			if page != u"{[COUPURE NOUVELLE PAGE]}" and page.namespace() not in namespacesAcceptes:
				listePagesASupprimer.append(page)
		
		for page in listePagesASupprimer:
			listePages.remove(page)
		
		#pywikibot.output(listePages)
		if len(listePages) < 1301:
			#nbMaxPagesParPaquet = len(listePages)
			self.majUneSeuleListe(listePages, titrePageRandomArticles)
		else:
			#nbMaxPagesParPaquet = 1200
			self.majAvecSousPages(listePages, titrePageRandomArticles)
			
	def majUneSeuleListe(self, listePages, titrePageRandomArticles):
		pageAsLinkBoolean = True
		if titrePageRandomArticles in blackList:
			pageAsLinkBoolean = False
			
		exceptions = []
	
		texteARajouter = u""
		x = 0
		
		# Création d'un texte contenant la liste des pages
		for page in listePages:
			x = x + 1
			texteARajouter = texteARajouter + u"\n|" + str(x) + u"=" + page.title(asLink=pageAsLinkBoolean)
		
		nbPages = x
		
		pageRandomArticles = pywikibot.Page(self.site, titrePageRandomArticles)
		text = pageRandomArticles.get()

		pywikibot.output(u"\n> \03{lightblue}Traitement de %s\03{default} <" % pageRandomArticles.title())
		
		text = self.suppressionAncienneListe(text)
		
		old = re.compile(u"\{\{#switch:\{\{rand\|(1\||2=)[0-9]*\}\}")
		new = (u"{{#switch:{{rand|1|%i}}%s" % (nbPages, texteARajouter))
		text = pywikibot.replaceExcept(text, old, new, exceptions)
		
		if not self.save(text, pageRandomArticles, self.summary):
			pywikibot.output(u'Aucun changement nécessaire')
			
	def majAvecSousPages(self, listePages, titrePageRandomArticles):
	
		########## Variables paramétrables ##########
		nbMaxPagesParPaquet = 1200
		#############################################

		exceptions = []
		
		texte = u""
		nombrePagesDansChaqueListe = []
		paquetsListesPages = []
		x = 0
		pageAsLinkBoolean = True
		if titrePageRandomArticles in blackList:
			pageAsLinkBoolean = False
		# Création des paquets de listes de pages
		for page in listePages:
			x = x + 1
			if page != u"{[COUPURE NOUVELLE PAGE]}":
				texte = texte + u"\n|" + str(x) + u"=" + page.title(asLink=pageAsLinkBoolean)
			if x == nbMaxPagesParPaquet:
				paquetsListesPages.append(texte)
				nombrePagesDansChaqueListe.append(nbMaxPagesParPaquet)
				texte = u""
				x = 0
			elif page == u"{[COUPURE NOUVELLE PAGE]}" and x > 1:
				#pywikibot.output(u"{[COUPURE NOUVELLE PAGE]}")
				paquetsListesPages.append(texte)
				nombrePagesDansChaqueListe.append(x)
				texte = u""
				x = 0
		
		if x != 0:
			nombrePagesDansChaqueListe.append(x)
			paquetsListesPages.append(texte)
		
		pywikibot.output("nombrePagesDansChaqueListe = %s" % nombrePagesDansChaqueListe)
		
		num = 0
		listeSousPages = []
		for texte in paquetsListesPages:
			nbPages = nombrePagesDansChaqueListe[num]
			num = num + 1
			
			texteARajouter = texte
			page = pywikibot.Page(self.site,(u"%s/%i" % (titrePageRandomArticles, num)))
			listeSousPages.append(u"%s/%i" % (titrePageRandomArticles.replace(u"Modèle:", u""), num))
			
			try:
				text = page.get()
				
				pywikibot.output(u"\n> \03{lightblue}Traitement de %s\03{default} <" % page.title())
				
				text = self.suppressionAncienneListe(text)
				
				old = re.compile(u"\{\{#switch:\{\{rand\|(0\||1\||2=)[0-9]*\}\}\|?")
				new = (u"{{#switch:{{rand|1|%i}}%s" % (nbPages, texteARajouter))
				text = pywikibot.replaceExcept(text, old, new, exceptions)
				
				if not self.save(text, page, self.summary):
					pywikibot.output(u'Aucun changement nécessaire')
			except pywikibot.NoPage:
				pywikibot.output(u'Page %s inexistante' % page.title())
				text = (u"{{#switch:{{rand|1|%i}}%s\n}}" % (nbPages, texteARajouter))
				###### À décommenter pour le bon fonctionnement ######
				if not self.creerPage(text, page, self.summary):
					pywikibot.output(u'La page n\'a pas été crée…')
				
				
		###
		# On traite à présent la page même du random pour mettre à jour le nombre de sous-pages existantes
		page = pywikibot.Page(self.site, titrePageRandomArticles)
		text = page.get()
		pywikibot.output(u"\n> \03{lightblue}Traitement de %s\03{default} <" % page.title())
		
		texteARajouter = u""
		z = 0
		for titreSousPage in listeSousPages:
			z = z + 1
			texteARajouter = texteARajouter + u"\n|%i={{%s}}" % (z, titreSousPage)
		
		text = self.suppressionAncienneListe(text)
		
		#pywikibot.output(texteARajouter)
		
		old = re.compile(u"\{\{#switch:\{\{rand\|(1\||2=)[0-9]*\}\}")
		new = (u"{{#switch:{{rand|1|%i}}%s" % (len(listeSousPages), texteARajouter))
		text = pywikibot.replaceExcept(text, old, new, exceptions)
		
		if not self.save(text, page, self.summary):
			pywikibot.output(u'Aucun changement nécessaire')
	
	###############
	
	def suppressionAncienneListe(self, text, nombreCrochets=2):
		exceptions = []
		#old = re.compile(u"(\n\|[0-9]{1,} *= *[\[\{]{2}.*[\]\}]{2}|\n[0-9]{1,} *= *[\[\{]{2}.*[\]\}]{2}\|)")
		old = re.compile(u"(\n\|[0-9]{1,} *= *[\[\{]{0,2}.*[\]\}]{0,2}|\n[0-9]{1,} *= *[\[\{]{0,2}.*[\]\}]{0,2}\|)")
		new = u""
		text = pywikibot.replaceExcept(text, old, new, exceptions)
		return text
		
	########################################
	
	def load(self, page):
		"""
		Loads the given page, does some changes, and saves it.
		"""
		try:
			# Load the page
			text = page.get()
		except pywikibot.NoPage:
			pywikibot.output(u"Page %s does not exist; skipping."
							 % page.title(asLink=True))
		except pywikibot.IsRedirectPage:
			pywikibot.output(u"Page %s is a redirect; skipping."
							 % page.title(asLink=True))
		else:
			return text
		return None

	def creerPage(self, text, page, comment, minorEdit=True, botflag=True):
		# only save if something was changed
		if text != None:
			arretdurgence()
			# Show the title of the page we're working on.
			# Highlight the title in purple.
			pywikibot.output(u"\n\n>>> \03{lightpurple}%s\03{default} <<<" % page.title())
			# show what was changed
			#pywikibot.showDiff(page.get(), text)
			pywikibot.output(u'%s' % text)
			pywikibot.output(u'Comment: %s' %comment)
			if not self.dry:
				#choice = pywikibot.inputChoice(u'Êtes-vous sûr de vouloir créer la page ?', ['Yes', 'No'], ['y', 'N'], 'N')
				choice = 'y'
				if choice == 'y':
					try:
						arretdurgence()
						if arret == "Oui":
							pywikibot.inputChoice(u"Demande d'arrêt d'urgence",['vu'],['v'],'')
						# Save the page
						page.put(text, comment=comment,
								 minorEdit=minorEdit, botflag=botflag)
					except pywikibot.LockedPage:
						pywikibot.output(u"Page %s is locked; skipping."
										 % page.title(asLink=True))
					except pywikibot.EditConflict:
						pywikibot.output(
							u'Skipping %s because of edit conflict'
							% (page.title()))
					except pywikibot.SpamblacklistError, error:
						pywikibot.output(
u'Cannot change %s because of spam blacklist entry %s'
							% (page.title(), error.url))
					else:
						return True
		return False

	def save(self, text, page, comment, minorEdit=True, botflag=True):
		# only save if something was changed
		if text != page.get():
			arretdurgence()

			# Show the title of the page we're working on.
			# Highlight the title in purple.
			pywikibot.output(u"\n\n>>> \03{lightpurple}%s\03{default} <<<" % page.title())
			# show what was changed
			#pywikibot.showDiff(page.get(), text)
			pywikibot.output(text)
			pywikibot.output(u'Comment: %s' %comment)
			if not self.dry:
				#choice = pywikibot.inputChoice(u'Do you want to accept these changes?', ['Yes', 'No'], ['y', 'N'], 'N')
				choice = 'y'
				if choice == 'y':
					try:
						arretdurgence()
						if arret == "Oui":
							pywikibot.inputChoice(u"Demande d'arrêt d'urgence",['vu'],['v'],'')
						# Save the page
						page.put(text, comment=comment,
								 minorEdit=minorEdit, botflag=botflag)
					except pywikibot.LockedPage:
						pywikibot.output(u"Page %s is locked; skipping."
										 % page.title(asLink=True))
					except pywikibot.EditConflict:
						pywikibot.output(
							u'Skipping %s because of edit conflict'
							% (page.title()))
					except pywikibot.SpamblacklistError, error:
						pywikibot.output(
u'Cannot change %s because of spam blacklist entry %s'
							% (page.title(), error.url))
					else:
						return True
		return False

def arretdurgence():
	global arret
	arretpage = pywikibot.Page(pywikibot.Site('fr','wikipedia'), u"Discussion utilisateur:ZéroBot")
	arret = arretpage.get()
	if arret != u"{{/Stop}}":
		pywikibot.inputChoice(u"Demande d'arrêt d'urgence",['vu'],['v'],'')
	

def main():
	global blackList
	blackList = [u"Modèle:Random Réalisation audiovisuelle"]
	
	bot = RandomBot()
	bot.run()

if __name__ == "__main__":
	try:
		main()
	finally:
		pywikibot.stopme()