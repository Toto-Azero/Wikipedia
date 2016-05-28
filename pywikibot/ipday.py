#!/usr/bin/python
# -*- coding: utf-8  -*-

#
# (C) Toto Azéro, 2011-2015
#
# Distribué sous licence GNU GPLv3
# Distributed under the terms of the GNU GPLv3 license
# http://www.gnu.org/licenses/gpl.html
#

import pywikibot, ip
from pywikibot import pagegenerators
import os, datetime, shutil, locale, codecs

locale.setlocale(locale.LC_ALL, 'fr_FR.utf8')
site = pywikibot.Site()

#lesMois = {
#1 : u"janvier",
#2 : u"février",
#3 : u"mars",
#4 : u"avril",
#5 : u"mai",
#6 : u"juin",
#7 : u"juillet",
#8 : u"août",
#9 : u"septembre",
#10 : u"octobre",
#11 : u"novembre",
#12 : u"décembre"
#}

dateDuJour = datetime.date.today()

## Date d'il y a un an et un jour
dateFichierDuJour = dateDuJour + datetime.timedelta(days=-366)

#annee = int(dateFichierDuJour.strftime("%Y"))
#mois = int(dateFichierDuJour.strftime("%B"))
#jour = int(dateFichierDuJour.strftime("%d"))
cwd = os.getcwd()
os.chdir('/data/project/totoazero/pywikibot')
nomFichierDuJour = u"Dates messages IP/%s/%i" % (dateFichierDuJour.strftime("%Y/%m").decode('utf-8'), int(dateFichierDuJour.strftime('%d')))

if nomFichierDuJour[-1] == 1:
	nomFichierDuJour += u"er"

## Copie du fichier pour être sûr de ne pas le perdre
## en ne traitant pas l'original
#nomFichierSauvegarde = u"%s - sauvegarde" % nomFichierDuJour
#os.chdir('/home/totoazero/')
#shutil.copy(nomFichierDuJour, nomFichierSauvegarde)

fichierDuJour = codecs.open(nomFichierDuJour, 'r')
listeIP = fichierDuJour.read().split()
fichierDuJour.close()

os.chdir(cwd)

listePdDIP = []

for num_ip in listeIP:
	listePdDIP.append(pywikibot.Page(site, u"Discussion utilisateur:%s" % num_ip))
	
#print listePdDIP
pywikibot.output(u"Nombre de pages à traiter : %i" % len(listePdDIP))

gen = pagegenerators.PreloadingGenerator(listePdDIP)
IPBot = ip.IPBot(gen, False)
IPBot.run()
