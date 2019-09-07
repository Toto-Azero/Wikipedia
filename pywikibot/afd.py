#! /usr/bin/python
# -*- coding: utf-8  -*-
"""
Mise à jour des PàS non listées mais catégorisées.

* 1009 : workaround, problème avec l'extraction des modèles (trop de modèles pou pwb ?),
          traitement découpé par sections pour réduire le nombre de modèles

TODO : fix workaround
"""
#
# (C) Nakor
# (C) Toto Azéro, 2011-2015
#
# Distribué sous licence GNU GPLv3
# Distributed under the terms of the GNU GPLv3 license
# http://www.gnu.org/licenses/gpl.html
#
__version__ = '1009'
__date__ = '2015-10-03 16:23:42 (CEST)'
#
import almalog2
import pywikibot
from pywikibot import config, pagegenerators, textlib
from scripts import template
import codecs, re

def pageIsListed(page, listedlist, templateList):
    found = False
    if config.verbose_output:
        pywikibot.output(u'Traitement de %s' % page.title())
    title=re.sub(u'_', u' ', page.title())
    if title in listedlist:
        found = True
        
    # Not found, trying lowercase and uppercase for first letter of the title
    if not found:
        lowtitle=title[0].lower()+title[1:]
        if config.verbose_output:
            pywikibot.output(u'Not found, trying low title %s' % lowtitle)
        if lowtitle in listedlist:
            found=True
        else:
            uptitle=title[0].upper()+title[1:]
            if config.verbose_output:
                pywikibot.output(u'Not found, trying up title %s' % uptitle)
            if uptitle in listedlist:
                found=True
            
    # Not found, trying title in the AfD model on the article page
    if not found:
        pagetemplates=page.templatesWithParams()
        for tuple in pagetemplates:
            if tuple[0].title() in templateList and len(tuple[1])>0:
                for arg in tuple[1]:
                    alttitle=re.sub(u'^ +', u'',re.sub(r' +$', u'', re.sub(u'cat=', u'', re.sub(u'Discuter:', u'', re.sub(u'Discussion', u'', re.sub(u'Discussion:', u'', arg))))))
                    if config.verbose_output:
                        pywikibot.output(u'Not found, trying alt title %s' % alttitle)
                    if alttitle in listedlist:
                        found=True
                        break
                    else:
                      lowtitle=alttitle[0].lower()+alttitle[1:]
                      if config.verbose_output:
                          pywikibot.output(u'Not found, trying low alttitle %s' % lowtitle)
                      if lowtitle in listedlist:
                          found=True
                      else:
                          uptitle=alttitle[0].upper()+alttitle[1:]
                          if config.verbose_output:
                              pywikibot.output(u'Not found, trying up alttitle %s' % uptitle)
                          if uptitle in listedlist:
                              found=True

    # Not found, trying redirections
    if not found:
        reflist=page.getReferences(follow_redirects=False, withTemplateInclusion=False, onlyTemplateInclusion=False, redirectsOnly=True)
        for refpage in reflist:
            if config.verbose_output:
                pywikibot.output(u'Not found, trying reference %s' % refpage.title())
            if refpage.title(withNamespace=False) in listedlist:
                found=True
                break

    return found


def main():

    botName=config.usernames['wikipedia']['fr']
    
    templates=False
    afdlist=False
    
    for arg in pywikibot.handleArgs():
        # -templates check afd articles whose admissibility is listed to be checked and removes the template
        if arg.startswith('-templates'):
            templates = True
        # -afdlist check articles not listed on afdlist
        elif arg.startswith('-afdlist'):
            afdlist = True
        # -all does both
        elif arg.startswith('-all'):
            templates = True
            afdlist = True
        else:
            pywikibot.output(u'Syntax: afd.py [-templates|-afdlist|-all]')
            exit()

    if config.verbose_output:
        pywikibot.output("Running in VERBOSE mode")

    if len(config.debug_log):
        pywikibot.output("Running in DEBUG mode")

    # Get category
    site = pywikibot.getSite()
    
    # Open logfile
    commandLogFilename = config.datafilepath('logs', 'afd.log')
    try:
        commandLogFile = codecs.open(commandLogFilename, 'a', 'utf-8')
    except IOError:
        commandLogFile = codecs.open(commandLogFilename, 'w', 'utf-8')    

    if templates:
        templateList=list()
        templatepage=pywikibot.Page(site, u'Modèle:Admissibilité à vérifier')
        templateList.append(templatepage.title(withNamespace=False))
        reflist=templatepage.getReferences(follow_redirects=False, withTemplateInclusion=False, onlyTemplateInclusion=False, redirectsOnly=True)
        for page in reflist:
            templateList.append(page.title(withNamespace=False))

        templateKeys = {}
        for templateName in templateList:
            templateKeys[templateName] = None    

    
    catname=u'Catégorie:Page proposée à la suppression'
    categ=pywikibot.Category(site, catname)
    subcats=list(categ.subcategories())
    fullartlist=categ.articles()
    artlist=list()
    for page in fullartlist:
        if page.namespace()==0:
            artlist.append(page)
    artlist+=subcats
    
    if templates:
        gen = iter(artlist)

        pagesToProcess=pagegenerators.PreloadingGenerator(gen, 60)
        
        summary=u'Admissibilité en cours de discussion : débat de suppression en cours'
       
        bot = template.TemplateRobot(generator=pagesToProcess, templates=templateKeys, subst=False, remove=True, editSummary=summary, acceptAll=True, addedCat=None)
        bot.run()
        
    if afdlist:
        afdpage=pywikibot.Page(site, u'Wikipédia:Pages à supprimer')
        if len(config.debug_log):
            projectpage=pywikibot.Page(site, u'User:ZéroBot/Projet:Maintenance/Pages à supprimer')
        else:
            projectpage=pywikibot.Page(site, u'Projet:Maintenance/Pages à supprimer')
        
        # Workaround
        # TO FIX
        
  #      alltemplates=afdpage.templatesWithParams()
        #print alltemplates
        
        listedlist=list()
        
        sections_list = re.split('==.+==', afdpage.get())
        for section in sections_list:
            alltemplates_section = textlib.extract_templates_and_params(section)
            print 'alltemplates_section'
            print alltemplates_section
            
            for tuple in alltemplates_section:
                #pywikibot.output(u'Template %s' % tuple[0])
                if tuple[0].upper() == u'L':
   #             if tuple[0].title()==u'Modèle:L':
   #                 text=re.sub(u'_', u' ', re.sub(r' +$', u'', tuple[1][0]))
                    text=re.sub(u'_', u' ', re.sub(r' +$', u'', tuple[1]['1']))
                    listedlist.append(text)
                    if config.verbose_output:
                        pywikibot.output(u'Added %s' % text)

        print listedlist
        templateList=list()
        templatepage=pywikibot.Page(site, u'Modèle:Suppression')
        templateList.append(templatepage.title())
        reflist=templatepage.getReferences(follow_redirects=False, withTemplateInclusion=False, onlyTemplateInclusion=False, redirectsOnly=True)
        for page in reflist:
            templateList.append(page.title())

        notlisted=list()
        for page in artlist:
            found = pageIsListed(page, listedlist, templateList)
            if not found:
               talkpage=page.toggleTalkPage()
               afdpage=pywikibot.Page(site, u'%s/Suppression' % talkpage.title())
               if afdpage.isRedirectPage():
                   targetpage=afdpage.getRedirectTarget()
                   if targetpage.namespace()==0:
                       pagetocheck=pywikibot.Page(site, re.sub(u'/Suppression', u'', targetpage.title(withNamespace=False)))
                   else:
                       pagetocheck=pywikibot.Page(site, re.sub(u'/Suppression', u'', targetpage.title()))
                       pagetocheck=pagetocheck.toggleTalkPage()
                   found = pageIsListed(pagetocheck, listedlist, templateList)
            if not found:
                notlisted.append(page.title())
                pywikibot.output(u'Not listed: %s' % page.title())

        newtext=u'=== Catégorisé mais pas sur [[Wikipédia:Pages à supprimer|PàS]] ===\n'
        for title in notlisted:
            page=pywikibot.Page(site, title)
            talkpage=page.toggleTalkPage()
            newtext+=u'# [[:%s]]  ([[%s/Suppression|sous-page]])\n' % (title, talkpage.title())

        if not len(config.debug_log):
            projectpage.put(newtext, u'Mise à jour de la liste de maintenance')
        
if __name__ == '__main__':
    try:
        main()
    except Exception, myexception:
        almalog2.error(u'afd', u'%s %s'% (type(myexception), myexception.args))
        raise
    finally:
        pywikibot.stopme()
