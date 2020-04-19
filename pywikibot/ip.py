#!/usr/bin/python
# -*- coding: utf-8  -*-
"""
Nettoyage de page de discussion d'ip
"""
#
# (C) Pywikipedia bot team
# (C) Micthev
# (C) Toto Azéro, 2011-2016
#
# Distribué sous licence GNU GPLv3
# Distributed under the terms of the GNU GPLv3 license
# http://www.gnu.org/licenses/gpl.html
#
__version__ = '500'
__date__= '2016-07-18 20:34:04 (CEST)'
#
import pywikibot
from pywikibot import pagegenerators
import re
import datetime
import sys
import traceback
import os

# This is required for the text that is shown when you run this script
# with the parameter -help.
docuReplacements = {
	'&params;': pagegenerators.parameterHelp
}

class IPBot:
	def __init__(self, generator, dry):
		"""
		Constructor. Parameters:
			* generator - The page generator that determines on which pages
						  to work on.
			* dry       - If True, doesn't do any real changes, but only shows
						  what would have been changed.
		"""
		self.generator = generator
		self.dry = dry

	def run(self):
		global Boucle
		try:
			fichier = open("boucle-ip.mic", "r")
			for line in fichier:
				Boucle = (line)
				Boucle = int(Boucle)
		except IOError:
			open("boucle-ip.mic", "w")
			Boucle = 0
		Boucle = Boucle+1
		fichier = open("boucle-ip.mic", "w")
		Boucle=str(Boucle)
		fichier.write(Boucle)
		fichier.close()
		for page in self.generator:
			try:
				self.treat(page)				
			except:
				exc_type, exc_value, exc_tb = sys.exc_info()
				err = traceback.format_exception(exc_type, exc_value, exc_tb)
				erreur = ""
				for item in err:
					erreur=erreur+item
				print "Erreur:"+erreur
				continue
	

	def treat(self, page):
		try:
			text = page.get()
		except pywikibot.NoPage:
			pywikibot.output(u"Page %s does not exist; skipping." % page.title(asLink=True))
		except pywikibot.IsRedirectPage:
			pywikibot.output(u"Page %s is a redirect; skipping." % page.title(asLink=True))
		
		regpage = page.title(withNamespace=False)
		commentaire = u"[[WP:Bot|Bot]] :"

		isip = re.compile(u'([0-9]+)\.([0-9]+)\.([0-9]+)\.([0-9]+)')
		if not isip.search(regpage):
			pywikibot.output(u"\n> \03{lightblue}Zappe %s qui n'est pas une IP\03{default} <" % regpage)
			return False
		
		pywikibot.output(u"\n>>> \03{lightgreen}Chargement de la page de discussion de l'IP N° %s\03{default} <<<\n" % regpage)

		proxy = re.compile('(P|p)roxy')
		if proxy.search(text):
			pywikibot.output(u"> \03{lightblue}Zappe la page qui contient le mot "+proxy.search(text).group(0)+u"\03{default} <")
			return False
		
		deja_averti = re.compile(u'({{[aA]vertissement effacé.*}})')
		if deja_averti.search(text):
			pywikibot.output(u"> \03{lightblue}Zappe la page qui contient le modèle "+deja_averti.search(text).group(0)+u"\03{default} <")
			return False
			
		modele = re.compile(u"({{[Ii][Pp] Free}}|{{[Ii][Pp] (collectif|collective|serveur Web|partagée?)\|.*[^\s*]}}|{{[Ii][Pp] (collectif|collective|serveur Web|partagée?)}}|{{[Ii][Pp] scolaire\|.*[^\s*]}}|{{IP scolaire}})")
		modeles_str = ""
		text2 = text
		while modele.search(text2):
			result = modele.search(text2)
			pywikibot.output(u"> \03{lightred}Contient le modèle : "+result.group(0)+u"\03{default} <")
			modeles_str += result.group(0) + "\n"
			text2 = text2[text2.index(result.group(0))+len(result.group(0)):]
		
		## Dernière modification de l'historique
		datederniermessage = page.editTime()
		
		datemaxi = pywikibot.Timestamp.today() + datetime.timedelta(days=-366)
		
		filename = "Dates messages IP/%s/%s/%s" % (datederniermessage.strftime('%Y'), datederniermessage.strftime('%m'), datederniermessage.strftime('%d'))
		try:
			# Le dossier existe peut-être déjà, si tel est le cas,
			# la commande suivante va renvoyer une erreur.
			# L'argument exist_ok n'existe qu'en Python 3
			os.makedirs(os.path.dirname(filename))
		except:
			pass
		
		try:
			file = open(filename, "r")
			textToWrite = file.read().decode('utf-8')
			file.close
		except:
			textToWrite = u""
						
		file = open(filename, "w")
		if not regpage in textToWrite:
			file.write((textToWrite + u"\n" + regpage).encode('utf-8'))
		file.close()
				
		if datederniermessage > datemaxi:
			pywikibot.output(u"\n> \03{lightblue}Phase 1 : Zappe la page\03{default} <\n> \03{lightblue}Dernier message du "+datederniermessage.strftime("%d-%m-%Y")+u"\03{default} <\n> \03{lightblue}Postérieur au "+datemaxi.strftime("%d-%m-%Y")+u"\03{default} <")
		else:
			pywikibot.output(u"\n> \03{lightred}Dernier message du "+datederniermessage.strftime("%d-%m-%Y")+u"\03{default} <\n> \03{lightred}Antérieur ou égal au "+datemaxi.strftime("%d-%m-%Y")+u"\03{default} <\n> \03{lightred}Modification en cours...\03{default} <")	
			
			nettoyage = ""
			if modeles_str:
				nettoyage = modeles_str+"\n"
			
			nettoyage += u"{{Avertissement effacé|{{subst:#ifeq:{{subst:LOCALDAY}}|1|{{1er}}|{{subst:LOCALDAY}}}} {{subst:LOCALMONTHNAME}} {{subst:LOCALYEAR}}}}"		
			commentaire += u" Nettoyage : Page de discussion d'[[Wikipédia:Utilisateur sous IP|IP]] inutilisée → dernier message du "+datederniermessage.strftime("%d/%m/%Y")	
			text = nettoyage
		
		if text != page.get():
			#pywikibot.showDiff(page.get(), text)
			arretdurgence()
			if not self.dry:
				try:
					# Save the page
					page.put(text, comment=commentaire)
				except pywikibot.LockedPage:
					pywikibot.output(u"Page %s is locked; skipping." % page.title(asLink=True))
				except pywikibot.EditConflict:
					pywikibot.output(u'Skipping %s because of edit conflict' % (page.title()))
				except pywikibot.SpamblacklistError, error:
					pywikibot.output(u'Cannot change %s because of spam blacklist entry %s' % (page.title(), error.url))

							
def arretdurgence():
	arrettitle = ''.join(u"Discussion utilisateur:ZéroBot")
	arretpage = pywikibot.Page(pywikibot.Site(), arrettitle)
	gen = iter([arretpage])
	arret = arretpage.get()
	if arret != u"{{/Stop}}":
		pywikibot.output(u"\n*** \03{lightyellow}Arrêt d'urgence demandé\03{default} ***")	
		exit(0)

def main():
	# This factory is responsible for processing command line arguments
	# that are also used by other scripts and that determine on which pages
	# to work on.
	genFactory = pagegenerators.GeneratorFactory()
	# The generator gives the pages that should be worked upon.
	gen = None
	# This temporary array is used to read the page title if one single
	# page to work on is specified by the arguments.
	pageTitleParts = []
	# If dry is True, doesn't do any real changes, but only show
	# what would have been changed.
	dry = False

	# Parse command line arguments
	for arg in pywikibot.handleArgs():
		if arg.startswith("-dry"):
			dry = True
		else:
			# check if a standard argument like
			# -start:XYZ or -ref:Asdf was given.
			if not genFactory.handleArg(arg):
				pageTitleParts.append(arg)

	if pageTitleParts != []:
		# We will only work on a single page.
		pageTitle = ' '.join(pageTitleParts)
		page = pywikibot.Page(pywikibot.Site(), pageTitle)
		gen = iter([page])

	if not gen:
		gen = genFactory.getCombinedGenerator()
	if gen:
		# The preloading generator is responsible for downloading multiple
		# pages from the wiki simultaneously.
		gen = pagegenerators.PreloadingGenerator(gen)
		bot = IPBot(gen, dry)
		bot.run()
	else:
		pywikibot.showHelp()

if __name__ == "__main__":
	try:
		main()
	finally:
		pywikibot.stopme()
