#!/usr/bin/python
# -*- coding: utf-8  -*-
"""
Nettoyage de page de discussion d'ip
"""
#
# (C) Pywikipedia bot team
# (C) Micthev
# (C) Toto Azéro, 2011-2013
#
# Distribué sous licence GNU GPLv3
# Distributed under the terms of the GNU GPLv3 license
# http://www.gnu.org/licenses/gpl.html
#
__version__ = '250'
__date__= '2013-05-01 16:35:52 (CEST)'
#
import pywikibot
from pywikibot import pagegenerators
import re
from array import array
import time
import datetime, urllib, urllib2, httplib, sys, traceback, socket, os

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
		# Set the edit summary message

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
			self.treat(page)
	

	def treat(self, page):
		try:
			"""
			Loads the given page, does some changes, and saves it.
			"""
			try:
				# Load the page
				text = page.get()
			except pywikibot.NoPage:
				pywikibot.output(u"Page %s does not exist; skipping." % page.title(asLink=True))
			except pywikibot.IsRedirectPage:
				pywikibot.output(u"Page %s is a redirect; skipping." % page.title(asLink=True))
			
			regpage = re.compile('Discussion utilisateur:(.*)')
			regpage.search(page.title())
			regpage = regpage.search(page.title())
			regpage = regpage.group(1)
			#log.log(u"ip", regpage)
			commentaire= u"[[WP:Bot|Bot]] :"
			try:
				isip = re.compile(u'([0-9]+)\.([0-9]+)\.([0-9]+)\.([0-9]+)')
				isip.search(regpage)
				isip = isip.search(regpage)
				isip = isip.group(4)
				isip = "Oui"
				pywikibot.output(u"\n>>> \03{lightgreen}Chargement de la page de discussion de l'IP N° %s\03{default} <<<\n" % regpage)
			except AttributeError:
				isip = "Non"
				pywikibot.output(u"\n> \03{lightblue}Zappe %s qui n'est pas une IP\03{default} <" % regpage)
			if isip == "Oui":
				proxy = re.compile('(P|p)roxy')
				proxy.search(text)
				proxy = proxy.search(text)
				try:
					pywikibot.output(u"> \03{lightblue}Zappe la page qui contient le mot "+proxy.group(0)+u"\03{default} <")
					proxy="Oui"
				except AttributeError:
					proxy="Non"
				if proxy == "Non":
					modele = re.compile(u"({{[Ii][Pp] Free}}|{{[Ii][Pp] (collectif|collective|serveur Web|partagée?)\|.*[^\s*]}}|{{[Ii][Pp] (collectif|collective|serveur Web|partagée?)}}|{{[Ii][Pp] scolaire\|.*[^\s*]}}|{{IP scolaire}})")
					modele.search(text)
					modele = modele.search(text)
					try:
						pywikibot.output(u"> \03{lightred}Contient le modèle : "+modele.group(0)+u"\03{default} <")
						modele=modele.group(0)
					except AttributeError:
						modele="Non"
					datepresence = re.compile(u"(janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre) ([0-9]+) à")
					datepresence.search(text)
					datepresence = datepresence.search(text)
					try:
						datepresence=datepresence.group(0)
						datepresence="Oui"
					except AttributeError:
						pywikibot.output(u"> \03{lightblue}Phase 1 : Zappe la page qui ne contient pas de date\03{default} <")
						datepresence="Non"
					if datepresence=="Oui":
						date = re.compile(u"([0-9]+) (janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre) ([0-9]+) à ([^þ]*)")
						date.search(text)
						date = date.search(text)	
						datetrouve = []
						text2=text
						for i in range(1000):
							try :
								date = re.compile(u"([0-9]+) (janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre) ([0-9]+) à ([^þ]*)")
								date.search(text2)
								date = date.search(text2)
								if date.group(2) == u"janvier":
									mois = "01"
								if date.group(2) == u"février":
									mois = "02"
								if date.group(2) == u"mars":
									mois = "03"
								if date.group(2) == u"avril":
									mois = "04"
								if date.group(2) == u"mai":
									mois = "05"
								if date.group(2) == u"juin":
									mois = "06"
								if date.group(2) == u"juillet":
									mois = "07"
								if date.group(2) == u"août":
									mois = "08"
								if date.group(2) == u"septembre":
									mois = "09"
								if date.group(2) == u"octobre":
									mois = 10
								if date.group(2) == u"novembre":
									mois = 11
								if date.group(2) == u"décembre":
									mois = 12	
								if date.group(1) == u"1er" or date.group(1) == "1" or date.group(1) == u"{{1er}}" or date.group(1) == u"1{{er}}" or date.group(1) == u"1<sup>er</sup":
									jour = "01"
								elif (date.group(1) == "2"):
									jour = "02"
								elif date.group(1) == "3":
									jour = "03"
								elif date.group(1) == "4":
									jour = "04"
								elif date.group(1) == "5":
									jour = "05"
								elif date.group(1) == "6":
									jour = "06"
								elif date.group(1) == "7":
									jour = "07"
								elif date.group(1) == "8":
									jour = "08"
								elif date.group(1) == "9":
									jour = "09"
								else:
									jour = date.group(1)		
								datee=str(date.group(3))+str(mois)+str(jour)
								dateee=int(datee)	
								datetrouve.append(dateee)
								text2 = date.group(4)
																																																																										
							except AttributeError:
								""
						try:
							datetrouve.sort()
							datetrouve.reverse()
							derniermessagenum = datetrouve[0]
							derniermessageannee = derniermessagenum / 10000
							
							now = datetime.datetime.now()
							if derniermessageannee < 2001 or derniermessageannee > now.year:
								pywikibot.output(u"Détection d'une anomalie dans l'année du dernier message : %i" % derniermessageannee)
								return False
							
							derniermessagemoisnum = (derniermessagenum - (derniermessageannee * 10000))/ 100
							if derniermessagemoisnum==1:
								derniermessagemois=u"janvier"
							if derniermessagemoisnum==2:
								derniermessagemois=u"février"
							if derniermessagemoisnum==3:
								derniermessagemois=u"mars"
							if derniermessagemoisnum==4:
								derniermessagemois=u"avril"
							if derniermessagemoisnum==5:
								derniermessagemois=u"mai"
							if derniermessagemoisnum==6:
								derniermessagemois=u"juin"
							if derniermessagemoisnum==7:
								derniermessagemois=u"juillet"
							if derniermessagemoisnum==8:
								derniermessagemois=u"août"
							if derniermessagemoisnum==9:
								derniermessagemois=u"septembre"
							if derniermessagemoisnum==10:
								derniermessagemois=u"octobre"
							if derniermessagemoisnum==11:
								derniermessagemois=u"novembre"
							if derniermessagemoisnum==12:
								derniermessagemois=u"décembre"		
							if derniermessagemois :
								derniermessagejour = derniermessagenum - (derniermessageannee * 10000) - (derniermessagemoisnum * 100)
								if derniermessagejour == 1:
									derniermessagejour = "1er"
								else:
									derniermessagejour = str(derniermessagejour)
								derniermessage = derniermessagejour+" "+derniermessagemois+" "+str(derniermessageannee)																																																		
								maintenant = datetime.date.today()
								datemaxinum = maintenant + datetime.timedelta(days=-366)
								datemaxinum = datemaxinum.strftime("%Y%m%d")
								datemaxinum = int(datemaxinum)
								datemaxiannee = datemaxinum / 10000
								datemaximoisnum = (datemaxinum - (datemaxiannee * 10000))/ 100
								if datemaximoisnum==1:
									datemaximois=u"janvier"
								if datemaximoisnum==2:
									datemaximois=u"février"
								if datemaximoisnum==3:
									datemaximois=u"mars"
								if datemaximoisnum==4:
									datemaximois=u"avril"
								if datemaximoisnum==5:
									datemaximois=u"mai"
								if datemaximoisnum==6:
									datemaximois=u"juin"
								if datemaximoisnum==7:
									datemaximois=u"juillet"
								if datemaximoisnum==8:
									datemaximois=u"août"
								if datemaximoisnum==9:
									datemaximois=u"septembre"
								if datemaximoisnum==10:
									datemaximois=u"octobre"
								if datemaximoisnum==11:
									datemaximois=u"novembre"
								if datemaximoisnum==12:
									datemaximois=u"décembre"		
								datemaxijour = datemaxinum - (datemaxiannee * 10000) - (datemaximoisnum * 100)
								if datemaxijour == 1:
									datemaxijour = u"1er"
								else:
									datemaxijour=str(datemaxijour)
								datemaxi = datemaxijour+" "+datemaximois+" "+str(datemaxiannee)						
							
								## Enregistrement des dates des messages
								if not os.path.isdir(u"Dates messages IP"):
									os.mkdir(u"Dates messages IP")
							
								if not os.path.isdir(u"Dates messages IP/%i" % derniermessageannee):
									os.mkdir(u"Dates messages IP/%i" % derniermessageannee)
								
								pywikibot.output(u"derniermessagemoisnum = %i" % derniermessagemoisnum)
								if not os.path.isdir(u"Dates messages IP/%i/%.2i" % (derniermessageannee, derniermessagemoisnum)):
									os.mkdir(u"Dates messages IP/%i/%.2i" % (derniermessageannee, derniermessagemoisnum))
							
								try:
									file = open(u"Dates messages IP/%i/%.2i/%s" % (derniermessageannee, derniermessagemoisnum, derniermessagejour), "r")
									textToWrite = file.read().decode('utf-8')
									file.close
								except:
									textToWrite = u""
								
								file = open(u"Dates messages IP/%i/%.2i/%s" % (derniermessageannee, derniermessagemoisnum, derniermessagejour), "w")
								if not regpage in textToWrite:
									file.write((textToWrite + u"\n" + regpage).encode('utf-8'))
								file.close()
							
								if derniermessagenum > datemaxinum:
									pywikibot.output(u"\n> \03{lightblue}Phase 1 : Zappe la page\03{default} <\n> \03{lightblue}Dernier message du "+derniermessage+u"\03{default} <\n> \03{lightblue}Postérieur au "+datemaxi+u"\03{default} <")
								else:
									pywikibot.output(u"\n> \03{lightred}Dernier message du "+derniermessage+u"\03{default} <\n> \03{lightred}Antérieur ou égal au "+datemaxi+u"\03{default} <\n> \03{lightred}Modification en cours...\03{default} <")	
									if modele!="Non":
										nettoyage = modele+"\n"
									else:
										nettoyage = ""
									nettoyage = nettoyage+u"{{Avertissement effacé|{{subst:#ifeq:{{subst:LOCALDAY}}|1|{{1er}}|{{subst:LOCALDAY}}}} {{subst:LOCALMONTHNAME}} {{subst:LOCALYEAR}}}}"		
									commentaire=commentaire + u" Nettoyage : Page de discussion d'[[Wikipédia:Utilisateur sous IP|IP]] inutilisée → dernier message du "+derniermessage	
									text=nettoyage				
							else:
								pywikibot.output(u"\n> \03{lightblue}Phase 1 : Zappe la page\03{default} <\n> \03{lightblue}Erreur interne\03{default} <")
						except IndexError:
							pywikibot.output('pywikibot.IndexError happened')

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
							except pywikibot.SpamfilterError, error:
								pywikibot.output(u'Cannot change %s because of spam blacklist entry %s' % (page.title(), error.url))
		except:
			exc_type, exc_value, exc_tb = sys.exc_info()
			err = traceback.format_exception(exc_type, exc_value, exc_tb)
			erreur = ""
			for item in err:
				erreur=erreur+item
			print "Erreur:"+erreur
			raise

							
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
