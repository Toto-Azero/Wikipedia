#!/usr/bin/python
# -*- coding: utf-8  -*-

import almalog
import pywikibot as wikipedia
#from pywikibot import config, catlib, pagegenerators
import wikipedia, config, catlib, pagegenerators
import codecs, re, urllib

def get_moved_pages(site, last=False, nb=5000):

    if last:
        move_regex = re.compile(
            r'moved <a href.*?>.*?</a> to <a href=.*?>(.*?)</a>.*?</li>'
            )
    else:
        move_regex = re.compile(
            r'moved <a href.*?>(.*?)</a> to <a href=.*?>.*?</a>.*?</li>'
            ) 
    move_url =  site.path() + "?title=Special:Log&limit=%d&type=move&user=Nakor"%nb
    
    try:
        move_list = site.getUrl(move_url)
    except:
        import traceback
        wikipedia.output(unicode(traceback.format_exc()))
        return
    g = move_regex.findall(move_list)
    wikipedia.output(u"%s moved pages" % len(g))
    for moved_title in g:
        moved_page = wikipedia.Page(site, moved_title)
        yield moved_page

def fix_title(page, commandLogFile, debug, verbose):
    if page.exists():
        site = wikipedia.getSite()
        text=page.get()

        targettitle=''
        if re.search(u'Traduction/Suivi', text) or re.search(u'Translation/Information', text):
            if re.search(u'Traduction/Suivi', text):
                modtext=re.split(u'Traduction/Suivi', text, 1)[1]
            if re.search(u'Translation/Information', text):
                modtext=re.split(u'Translation/Information', text, 1)[1]
            #wikipedia.output(u'1: %s' % modtext)
            parts=re.split(u'\|', modtext)
            origtitle=parts[2]
            targettitle=parts[3]

        reftitle=re.sub(u'\'', u'&#39;', re.sub(u'&', u'&amp;', page.title()))
        if reftitle != u'Discussion:%s/Traduction' % targettitle:
            wikipedia.output(u'Change needed %s, %s' %  (page.title(), targettitle))
            newtitle=re.sub(u'\'', u'&#39;', re.sub(u'&', u'&amp;', re.sub(u'/Traduction', u'', page.titleWithoutNamespace())))
            replacestring=u'\| *'+origtitle+u'\| *'+targettitle+u' *\|'
            replacestring=re.sub(u'\(', u'\(', replacestring)
            replacestring=re.sub(u'\)', u'\)', replacestring)
            newtext=re.sub(replacestring, u'|'+origtitle+u'|'+newtitle+u'|', text)
            if debug==1:
                #newpage=wikipedia.Page(site, u'Utilisateur:AlmabotJunior/' + reftitle)
                newpage=wikipedia.Page(site, u'Utilisateur:AlmabotJunior/Test')
                newpage.put(text, u'Test ori [[%s]]' % reftitle)
                newpage.put(newtext, u'Test new [[%s]]' % reftitle)
            else:
                page.put(newtext, u'Mise à jour')


def movepage(page, commandLogFile, debug, verbose):
    site = wikipedia.getSite()
    
    title=page.title()
    regtitle=title
    # Escape parenthesis
    regtitle=re.sub(u'\(', u'\(', regtitle)
    regtitle=re.sub(u'\)', u'\)', regtitle)
    regtitle=re.sub(u'\?', u'\?', regtitle)
    
    # search for both spaces and underscores
    regtitle=re.sub(u' ', u'[ _]', regtitle)
    
    shorttitle=re.sub(u'Projet:Traduction/', u'', title)
    
    shortregtitle=shorttitle
    shortregtitle=u'{{L\|%s}}' % shortregtitle
    shorttitle=u'[[:%s]] ([[Discussion:%s/Traduction|\'\'\'sous-page\'\'\']])' % (shorttitle, shorttitle)

    regtitle=re.sub(u'Projet', u'[P|p]rojet', regtitle)
    regtitle=re.sub(u'Traduction', u'[T|t]raduction', regtitle)
    
    #if re.search(u':', shorttitle):
    #    parts=re.split(u':', shorttitle)
    #    subnamespaceidx=site.getNamespaceIndex(parts[0][1:])
    #    if subnamespaceidx==100:
    #        newtitle=re.sub(u'Wikipédia:Liste des articles non neutres/Portail:', u'Discussion Portail:', title)
    #    else:
    #        newtitle=re.sub(u'Wikipédia:Liste des articles non neutres/', u'Discussion:', title)
    #else:
    newtitleroot=re.sub(u'Projet:Traduction/', u'', title)
    if verbose:
        wikipedia.output(u'Destination: ' + newtitleroot)
    newtitlerootpage=wikipedia.Page(site, newtitleroot)
    if newtitlerootpage.isRedirectPage():
        newtitleroot=newtitlerootpage.getRedirectTarget().sectionFreeTitle()
        if verbose:
            wikipedia.output(u'Destination after redirect: ' + newtitleroot)

    newtitle = u'Discussion:%s/Traduction' % newtitleroot
        
    # First fix redirects
    references=page.getReferences(False)
    
    commandLogFile.write(u'* Page traitée : \'\'\'%s\'\'\'\n' % title)
    references=page.getReferences(False)
    refcount=0
    refchanged=0
    for reference in references:
        reftitle=reference.title()
        if (not re.search(u'Utilisateur:AlmabotJunior', reftitle)) and (not re.search(u'Utilisateur:DumZiBoT/Traduction', reftitle)):
            if verbose:
                wikipedia.output(u'Reference: %s' % reftitle)
            if re.search(u'Projet:Traduction/\*/Projet', reftitle):
                commandLogFile.write(u'** Page liée [[%s]] : non traitée, page générée automatiquement\n' % reftitle)
                if verbose:
                    wikipedia.output(u'** Page liée [[%s]] : non traitée, page générée automatiquement' % reftitle)
            else:
                if reference.canBeEdited() and reference.botMayEdit('AlmabotJunior'):
                    text=reference.get(False, True)
                    if reftitle==u'Projet:Traduction':
                        (tempnewtext, tempnumrep)=re.subn(shortregtitle, shorttitle, text)
                    else:
                        (tempnewtext, tempnumrep)=re.subn(regtitle, newtitle, text)
                    (newtext, numrep)=re.subn(u'[P|p]rojet:[T|t]raduction/{{PAGENAME}}', u'Discussion:{{PAGENAME}}/Traduction', tempnewtext)
                    numrep+=tempnumrep
                
                    if numrep==0:
                        templates=reference.templates()
                        correcttemplate = False
                        for template in templates:
                            templatetitle=template.title()
                            if verbose:
                                wikipedia.output(u'Template %s' % templatetitle)
                            if templatetitle==u'A':
                                correcttemplate=True
                                commandLogFile.write(u'** Page liée [[%s]] : pas de lien direct, lien via {{m|a}}\n' % reftitle)
                                if verbose:
                                    wikipedia.output(u'** Page liée [[%s]] : pas de lien direct, lien via {{m|a}}' % reftitle)
                                break
                            elif templatetitle==u'Traduction':
                                correcttemplate=True
                                commandLogFile.write(u'** Page liée [[%s]] : pas de lien direct, lien via {{m|Traduction}}\n' % reftitle)
                                if verbose:
                                    wikipedia.output(u'** Page liée [[%s]] : pas de lien direct, lien via {{m|Traduction}}' % reftitle)
                                break
                            elif templatetitle==u'À Traduire':
                                correcttemplate=True
                                commandLogFile.write(u'** Page liée [[%s]] : pas de lien direct, lien via {{m|à traduire}}\n' % reftitle)
                                if verbose:
                                    wikipedia.output(u'** Page liée [[%s]] : pas de lien direct, lien via {{m|à traduire}}' % reftitle)
                                break
                            elif templatetitle==u'Demande De Traduction':
                                correcttemplate=True
                                commandLogFile.write(u'** Page liée [[%s]] : pas de lien direct, lien via {{m|Demande de traduction}}\n' % reftitle)
                                if verbose:
                                    wikipedia.output(u'** Page liée [[%s]] : pas de lien direct, lien via {{m|Demande de traduction}}' % reftitle)
                                break
                        if not correcttemplate:
                            commandLogFile.write(u'** Page liée [[%s]] : pas de lien direct, pas de modèle\n' % reftitle)
                            wikipedia.output(u'** Page liée [[%s]] : pas de lien direct, pas de modèle' % reftitle)
                    else:
                        commandLogFile.write(u'** Page liée [[%s]] : %d lien(s) remplacé(s)\n' % (reftitle, numrep) )
                        if verbose:
                            wikipedia.output(u'** Page liée [[%s]] : %d lien(s) remplacé(s)' % (reftitle, numrep) )
                        if debug==1:
                            #newpage=wikipedia.Page(site, u'Utilisateur:AlmabotJunior/' + reftitle)
                            newpage=wikipedia.Page(site, u'Utilisateur:AlmabotJunior/Test')
                            newpage.put(text, u'Test ori [[%s]]' % reftitle)
                            newpage.put(newtext, u'Test new [[%s]]' % reftitle)
                        else:
                            reference.put(newtext, u'Selon [[Wikipédia:Prise de décision/Sous-pages de discussion des articles]]')
                        refchanged += 1
                else:
                    if not reference.canBeEdited():
                        commandLogFile.write(u'** Page liée [[%s]] : non traitée, page protégée\n' % reftitle)
                        if verbose:
                            wikipedia.output(u'** Page liée [[%s]] : non traitée, page protégée' % reftitle)
                    else:
                        commandLogFile.write(u'** Page liée [[%s]] : non traitée, page interdite aux bots\n' % reftitle)
                        if verbose:
                            wikipedia.output(u'** Page liée [[%s]] : non traitée, page interdite aux bots' % reftitle)
            
                refcount+=1

    # Then move page
    if page.exists():
        if debug==1:
            commandLogFile.write(u'*: Page à renommer en [[%s]]\n' % newtitle)
            if verbose:
                wikipedia.output(u'*: Page à renommer en [[%s]]' % newtitle)
        else:
            newpage=wikipedia.Page(site, newtitle)
            if not newpage.exists():
                page.move(newtitle, u'Selon [[Wikipédia:Prise de décision/Sous-pages de discussion des articles]]', True, False, True, False, True, True, False)
                commandLogFile.write(u'*: Page renommée en [[%s]]\n' % newtitle)
                if verbose:
                    wikipedia.output(u'*: Page renommée en [[%s]]' % newtitle)
            else:
                wikipedia.output(u'Unable to move %s to %s' % (page.title(), newtitle))
                commandLogFile.write(u'Unable to move %s to %s\n' % (page.title(), newtitle))
                if verbose:
                    wikipedia.output(u'Unable to move %s to %s' % (page.title(), newtitle))


    # Check remaining references
    refremain=0
    if (refcount):
        references=page.getReferences(False)
        for reference in references:
            reftitle=reference.title()
            if (not re.search(u'Utilisateur:AlmabotJunior', reftitle)) and (not reftitle == u'Wikipédia:Liste des articles non neutres/Justification de leur promotion') \
              and (not reftitle == u'Wikipédia:Articles de qualité/Justification de leur promotion'):
                refremain+=1
        
    if refcount == 0 and refremain == 0:
        commandLogFile.write(u'*: Pas de page liée à modifier\n')
        if verbose:
            wikipedia.output(u'*: Pas de page liée à modifier')
    else:
        if debug==1:
            commandLogFile.write(u'*: %d page(s) liée(s) : %d à traiter, %d restante(s)\n' % (refcount, refchanged, refremain))
            if verbose:
                wikipedia.output(u'*: %d page(s) liée(s) : %d à traiter, %d restante(s)' % (refcount, refchanged, refremain))
        else:
            commandLogFile.write(u'*: %d page(s) liée(s) : %d traitée(s), %d restante(s)\n' % (refcount, refchanged, refremain))
            if verbose:
                wikipedia.output(u'*: %d page(s) liée(s) : %d traitée(s), %d restante(s)' % (refcount, refchanged, refremain))

    


def main():
    # Open logfile
    commandLogFilename = config.datafilepath('logs', 'translation_move.log')
    try:
        commandLogFile = codecs.open(commandLogFilename, 'a', 'utf-8')
    except IOError:
        commandLogFile = codecs.open(commandLogFilename, 'w', 'utf-8')

    site = wikipedia.getSite()
    
    categlang=False
    categproj=False
    initlist=False
    debug=0
    debugwrite=False
    startindex=None
    finishindex=None
    finalverif=None
    verbose=False
    pagename=None
    fixlink=False
    fixtitle=False
    
    for arg in wikipedia.handleArgs():
        if arg.startswith('-categlang'):
            categlang = True
            if arg.startswith('-categlang:'):
                parts=re.split(u':', arg)
                subparts=re.split(u'-', parts[1])
                startindex=int(subparts[0])
                finishindex=int(subparts[1])
        elif arg.startswith('-categproj'):
            categproj = True
        elif arg.startswith('-sublist'):
            if arg.startswith('-sublist:'):
                parts=re.split(u':', arg)
                subparts=re.split(u'-', parts[1])
                startindex=int(subparts[0])
                finishindex=int(subparts[1])
        elif arg.startswith('-initlist'):
            initlist = True
            categ = True
        elif arg.startswith('-finalverif'):
            finalverif = True
        elif arg.startswith('-debugw'):
            debug = 2
        elif arg.startswith('-debug'):
            debug = 1
        elif arg.startswith('-verb'):
            verbose = True
        elif arg.startswith('-fixlink'):
            fixlink=True
        elif arg.startswith('-fixtitle'):
            fixtitle=True
        elif arg.startswith('-page:'):
            parts=re.split(u':', arg, 1)
            pagename=parts[1]
        else:
            wikipedia.output(u'Syntax: translation_move.py [-categ[:[start]-[finish]]] [-initlist] [-debug] [-finalverif]')
            exit()
    
    # Get category
     
    if not debug==0:
        artlist=list()

        artlist.append(wikipedia.Page(site, u'Projet:Traduction/Jun Kazama'))
        #artlist.append(wikipedia.Page(site, u'Discussion:Train Protection & Warning System/Traduction'))
        #artlist.append(wikipedia.Page(site, u'Discussion:Cathédrale d\'Espoo/Traduction '))
       
        #catname = u'Catégorie:Traduction du Projet Architecture chrétienne'
        #categ=catlib.Category(site, catname)
        #artlist=categ.articlesList(True)
        #artlist=fullartlist[0:150] 
        translationGenerator=iter(artlist)        
        #translationGenerator=site.prefixindex(u'Traduction/', 102)
        #artlist=list(translationGenerator)
        commandLogFile.write(u'== Traitement de %d article(s) ==\n' % len(artlist))
        if verbose:
            wikipedia.output(u'== Traitement de %d article(s) ==' % len(artlist))
    elif categlang:
        catname = u'Traduction par langue'
        categ=catlib.Category(site, catname)
        translationGenerator=categ.articles(True)
    elif categproj:
        catname = u'Traduction par projet'
        categ=catlib.Category(site, catname)
        translationGenerator=categ.articles(True)
    elif pagename:
        artlist=list()
        artlist.append(wikipedia.Page(site, pagename))
        translationGenerator=iter(artlist)
    elif fixlink:
        artlist=get_moved_pages(site, fixtitle)
        translationGenerator=iter(artlist)
    elif fixtitle:
        catname = u'Catégorie:Page de traduction mal paramétrée'
        categ=catlib.Category(site, catname)
        translationGenerator=categ.articles(True)
    else: 
        translationGenerator=site.prefixindex(u'Traduction/', 102)
    
    allset=0
    processed=0
    total=0
    
    translationPreloadingGen=pagegenerators.PreloadingGenerator(translationGenerator, 60)
    
    index=0
    for page in translationPreloadingGen:
        if (not startindex) or (index>=startindex):
            total=total+1
            namespace=site.namespace(page.namespace())
            title=page.titleWithoutNamespace()
            if verbose:
                wikipedia.output(u'Processing : %s in %s' % (title, namespace))
            if namespace == 'Discussion':
                if re.search (u'/Traduction', title):
                    if fixtitle:
                        fix_title(page, commandLogFile, debug, verbose)
                    elif not finalverif:
                        commandLogFile.write(u'* Page déjà renommée: [[%s:%s]]\n' % (namespace, title))
                        if verbose:
                            wikipedia.output(u'* Page déjà renommée: [[%s:%s]]' % (namespace, title))
                    allset=allset+1
                else:
                    commandLogFile.write(u'* Page ignorée (namespace incorrect): [[%s:%s]]\n' % (namespace, title))
                    if verbose:
                        wikipedia.output(u'* Page ignorée (namespace incorrect): [[%s:%s]]' % (namespace, title))
            elif namespace == u'Projet':
                if re.search(u'Traduction', title):
                    shorttitle=re.sub(u'Traduction/', u'/', title)
                    correctname = False
                    if re.search(u':', shorttitle):
                        if verbose:
                            wikipedia.output(shorttitle+u' has :')
                        parts=re.split(u':', shorttitle)
                        if verbose:
                            wikipedia.output(parts[0][1:])
                        subnamespaceidx=site.getNamespaceIndex(parts[0][1:])
                        if subnamespaceidx==None or subnamespaceidx==100:
                            # Test against old namespaces
                            if parts[0][1:] == 'Discussion':
                                commandLogFile.write(u'* Page ignorée (namespace lié incorrect): [[%s:%s]]\n' % (namespace, title))
                                if verbose:
                                    wikipedia.output(u'* Page ignorée (namespace lié incorrect): [[%s:%s]]' % (namespace, title))
                            else:
                                correctname = True
                        else:
                            commandLogFile.write(u'* Page ignorée (namespace lié incorrect): [[%s:%s]]\n' % (namespace, title))
                            if verbose:
                                wikipedia.output(u'* Page ignorée (namespace lié incorrect): [[%s:%s]]' % (namespace, title))
                    elif re.search(u'\*', shorttitle):
                        commandLogFile.write(u'* Page ignorée (page de maintenance): [[%s:%s]]\n' % (namespace, title))
                        if verbose:
                            wikipedia.output(u'* Page ignorée (page de maintenance): [[%s:%s]]' % (namespace, title))
                    else:
                        correctname = True
                    
                    #if verbose:
                    #   if correctname:
                    #       wikipedia.output(u'Correctname')
                    #   else:
                    #       wikipedia.output(u'Incorrectname')
                    if correctname:                    
                        if initlist:
                            processed=processed+1
                            commandLogFile.write(u'* Page potentiellement traitée: [[%s:%s]]\n' % (namespace, title))
                            if verbose:
                                wikipedia.output(u'* Page potentiellement traitée: [[%s:%s]]' % (namespace, title))
                        else:
                            if page.isRedirectPage():
                                commandLogFile.write(u'* Page ignorée (redirect): [[%s:%s]]\n' % (namespace, title))
                                if verbose:
                                    wikipedia.output(u'* Page ignorée (redirect): [[%s:%s]]' % (namespace, title))
                            elif not page.canBeEdited():
                                commandLogFile.write(u'* Page ignorée (protection): [[%s:%s]]\n' % (namespace, title))
                                if verbose:
                                    wikipedia.output(u'* Page ignorée (protection): [[%s:%s]]' % (namespace, title))
                            elif not page.botMayEdit('AlmabotJunior'):
                                commandLogFile.write(u'* Page ignorée (nobot): [[%s:%s]]\n' % (namespace, title))
                                if verbose:
                                    wikipedia.output(u'* Page ignorée (nobot): [[%s:%s]]' % (namespace, title))
                            elif not page.exists() and not fixtitle:
                                movepage(page, commandLogFile, debug, verbose)
                            else:
                                templates=page.templates()
                                correcttemplate = False
                                for template in templates:
                                    templatetitle=template.title()
                                    if verbose:
                                        wikipedia.output(templatetitle)
                                    if (templatetitle==u'Translation/Header'):
                                        correcttemplate = True
                                    elif (templatetitle==u'Translation/Header2'):
                                        correcttemplate = True
                                    elif (templatetitle==u'Traduction/Instructions'):
                                        correcttemplate = True
                                    elif (templatetitle==u'Traduction/Suivi'):
                                        correcttemplate = True
                                if correcttemplate and not fixtitle:
                                    processed=processed+1
                                    movepage(page, commandLogFile, debug, verbose)
                                else:
                                    commandLogFile.write(u'* Page ignorée (pas de modèle): [[%s:%s]]\n' % (namespace, title))
                                    if verbose:
                                        wikipedia.output(u'* Page ignorée (pas de modèle): [[%s:%s]]' % (namespace, title))
                else:
                    commandLogFile.write(u'* Page ignorée (nom incorrect): [[%s:%s]]\n' % (namespace, title))
                    if verbose:
                        wikipedia.output(u'* Page ignorée (nom incorrect): [[%s:%s]]' % (namespace, title))
            else:
                commandLogFile.write(u'* Page ignorée (namespace incorrect): [[%s:%s]]\n' % (namespace, title))
                if verbose:
                    wikipedia.output(u'* Page ignorée (namespace incorrect): [[%s:%s]]' % (namespace, title))
        index=index+1
        if finishindex and (index>=finishindex):
            break
       
    commandLogFile.write(u'%d page(s) au total\n' % total)
    commandLogFile.write(u'%d page(s) en place\n' % allset)
    commandLogFile.write(u'%d page(s) traitées\n' % processed)
    commandLogFile.close()
        
    
if __name__ == '__main__':
    try:
        main()
    except Exception, myexception:
        almalog.error(u'translation_move', u'%s %s'% (type(myexception), myexception.args))
        raise
    finally:
        wikipedia.stopme()
