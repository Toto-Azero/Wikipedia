#!/usr/bin/python
# -*- coding: utf-8  -*-

#
# (C) Nakor
# (C) Toto Azéro, 2011
#
# Distribué sous les terms de la licence MIT.
# Distributed under the terms of the MIT license.
#

import _errorhandler
import pywikibot
from pywikibot import catlib, config, pagegenerators
import codecs, re

def findStatus(text):
    retval=''
    modtext=None
    if re.search(u'Traduction/Suivi', text):
        modtext=re.split(u'Traduction/Suivi', text, 1)[1]
    elif re.search(u'Translation/Information', text):
        modtext=re.split(u'Translation/Information', text, 1)[1]
    if modtext:
        #pywikibot.output(u'1: %s' % modtext)
        parts=re.split(u'\|', modtext)
        for part in parts:
            #pywikibot.output(u'2: %s' % part)
            if re.match(r'\s*status', part):
                #pywikibot.output(u'3: %s' % part)
                string0=re.split(u'=\s*', part, 1)[1]
                #pywikibot.output(u'4: %s' % string0)
                string1=re.split(u'\s*[\n\r]', string0, 1)[0]
                string2=re.split(u'\s*<!--', string1, 1)[0]
                retval=re.split(u' $', string2, 1)[0]
                #retval=string0
                #pywikibot.output(u'5: |%s|' % retval)
                break
    

    return retval
    
def main():

    botName=config.usernames['wikipedia']['fr']
    
    debug=0
    debugwrite=False
    uniqueproject=None
    allprojects = False
    force = False
    warningtext=u''
    
    for arg in pywikibot.handleArgs():
        if arg.startswith('-project:'):
            parts=re.split(u':', arg)
            uniqueproject=parts[1]
        elif arg.startswith('-force'):
            force = True
        elif arg.startswith('-debugw'):
            debug = 2
        elif arg.startswith('-dbg'):
            debug = 1
        else:
            pywikibot.output(u'Syntax: translation_project.py -project:projet')
            exit()
            
    # Get category
    site = pywikibot.getSite()
    
    projectslist=list()
    if uniqueproject:
        projectslist.append(uniqueproject)
    else:
        maincat=catlib.Category(site, u'Traduction par projet')
        subcategorieslist=maincat.subcategories()
        for subcategory in subcategorieslist:
            found=re.search(r'.*Traduction du Projet (.*)', subcategory.title())
            if found:
                project=found.group(1)
                projectslist.append(project)
            
    
    commandLogFilename = config.datafilepath('logs', 'translation_project.log')
    commandLogFile = codecs.open(commandLogFilename, 'w', 'utf-8')    

    for project in projectslist:
        finalpagename=u'Projet:Traduction/*/Projet/%s' % project
        finalpage=pywikibot.Page(site, finalpagename)
    
        proceed=False
        if debug==0 and not force:
            if (finalpage.exists()):
                if (finalpage.getVersionHistory(revCount=1)[0][2]==botName):
                    pywikibot.output(u'%s last edit by bot, we can proceed' % finalpagename)
                    proceed=True
                else:
                    pywikibot.output(u'%s modifed, skipping' % finalpagename)
                    pywikibot.output(botName)
                    pywikibot.output(finalpage.getVersionHistory(revCount=1)[0][2])
                    commandLogFile.write(u'%s modifed, skipping\n' % finalpagename)
                    tmpCommandLogFilename = config.datafilepath('logs', 'translation_project_%s.log' % project)
                    tmpCommandLogFile = codecs.open(tmpCommandLogFilename, 'w', 'utf-8')    
                    tmpCommandLogFile.write(u'%s modifed, skipping\n' % finalpagename)
                    tmpCommandLogFile.close()
            else:
                proceed=True
                pywikibot.output(u'%s does not exists, we can proceed' % finalpagename)
        else:
            proceed=True

        if proceed:
            if not debug==0:
                #artlist=list()
                #artlist.append(pywikibot.Page(site, u'Projet:Traduction/Boccace'))
                #artlist.append(pywikibot.Page(site, u'Projet:Traduction/Administrateur systèmes'))
                #artlist.append(pywikibot.Page(site, u'Projet:Traduction/Alexa Internet'))
                #artlist.append(pywikibot.Page(site, u'Projet:Traduction/Algèbre de Kleene'))
                category = catlib.Category(site, u'Traduction du Projet %s' % project)
                gen=category.articles(True)
            else:
                category = catlib.Category(site, u'Traduction du Projet %s' % project)
                gen=category.articles(True)
            

            pagesToProcess=pagegenerators.PreloadingGenerator(gen, 60)
            
            demande=list()
            encours=list()
            arelire=list()
            enrelecture=list()
            terminee=list()
            
            for page in pagesToProcess:
                title=page.title(withNamespace=False)
                #pywikibot.output(title)
                subtitle=re.sub(u'/Traduction', u'', title)
                if title!=u'Traduction/*/Projet/%s' % project:
                    text=page.get()
                    status=findStatus(text)
                    #pywikibot.output(status)
                    if status == u'Demande' or status == u'1':
                        demande.append(subtitle)
                    elif status == u'En cours' or status == u'2':
                        encours.append(subtitle)
                    elif status == u'A relire' or status == u'3':
                        arelire.append(subtitle)
                    elif status == u'En relecture' or status == u'4':
                        enrelecture.append(subtitle)
                    elif status == u'Terminée' or status == u'5':
                        terminee.append(subtitle)
                    else:
                        pywikibot.output(u'No match: %s (%s)' % (subtitle, status))
                        warningtext+=u'No match: %s (%s)\n' % (subtitle, status)
                        
            # Sort lists
            demande.sort()
            encours.sort()
            arelire.sort()
            enrelecture.sort()
            terminee.sort()
            
                        
            # Create page
            newtext=u'<noinclude>{{Projet:Traduction/EnteteProjet|%s}}\n</noinclude>\n== Demande de traduction ==\n'% project
            for title in demande:
                newtext+=u'{{Discussion:%s/Traduction}}\n' % title
            newtext+=u'== Traduction en cours ==\n'
            for title in encours:
                newtext+=u'{{Discussion:%s/Traduction}}\n' % title
            newtext+=u'== Traduction à relire ==\n'
            for title in arelire:
                newtext+=u'{{Discussion:%s/Traduction}}\n' % title
            newtext+=u'== Relecture en cours ==\n'
            for title in enrelecture:
                newtext+=u'{{Discussion:%s/Traduction}}\n' % title
            newtext+=u'<noinclude>\n== Traduction terminée ==\n'
            for title in terminee:
                newtext+=u'{{Discussion:%s/Traduction}}\n' % title
            newtext+=u'</noinclude>'
            
            if debug==0:
                if finalpage.exists():
                    text=finalpage.get()
                if (text!=newtext):
                    finalpage.put(newtext, u'Traductions du projet %s' % project)
            else:
                page=pywikibot.Page(site, u'Utilisateur:'+botName+'/Test')
                text=page.get()
                if (text!=newtext):
                    page.put(newtext, u'Traductions du projet %s' % project)
    
    commandLogFile.close()
    
    if len(warningtext)>0 :
  
        logpage=pywikibot.Page(site, u'Utilisateur:'+botName+u'/Log/Avertissements')
    
        pagetext=logpage.get()
        pagetext+=u'\n== Traduction des projets =='
        pagetext+=warningtext
     
        logpage.put(pagetext, u'Traduction des projets', watchArticle = None, minorEdit = False);
    
if __name__ == '__main__':
    try:
        main()
    except Exception, myexception:
        _errorhandler.handle(myexception)
        raise
    finally:
        pywikibot.stopme()
