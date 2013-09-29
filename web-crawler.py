'''
    File: web-crawler.py
    Date: 9/23/2013
    Authors: Eric Ewing and Jialun "Julian" Luo
    The program crawls a given URL. If specified, the program can 
    1) give a summary of the crawl;
    2) show all broken links;
    3) show all links that are not linked back to the start page;
    4) show the greatest distance from start page to the farthest page (taking shortest paths)
    5) show all links that are farthest away from start page;
    6) show all outgoing links;
    etc.
'''

import sys
import re
import urllib2
import argparse
import time

'''
    Class: WebPage
    Stores its URL and important information (e.g. HTML code, its children links, etc.)
'''
class WebPage:
    
    def __init__(self, link, distance, p):
        self.parentURL = p
        self.givenURL = link
        self.pageHTML = self.readURL(self.givenURL)
        self.distanceFromHome = distance
        if(self.pageHTML):
            self.children = self.get_all_href_values(self.pageHTML)
    def getParentURL(self):
        return self.parentURL
    def getGivenURL(self):
        return self.givenURL
    def setDistanceFromHome(self, d):
        self.distanceFromHome = d
    def getDistanceFromHome(self):
        return self.distanceFromHome
    
    def getChildren(self):
        return self.children
    
    def get_all_href_values(self, text):
        href_pattern = re.compile(r'<a.*?href="(.*?)"')
        links = [] 
        for href_value in re.findall(href_pattern, text): 
            links.append(href_value)
        return links
    
    '''
        Credit: Jeff Ondich
        Modified by Eric Ewing.
        If the given link is broken, stored the link and its parent URL as a tuple in a list.
    '''
    def readURL(self, link):
        try: 
            request = urllib2.Request(link) 
            response = urllib2.urlopen(request) 
            text_of_requested_page = response.read() 
            response.close()
            return text_of_requested_page
        except Exception, e:
            global brokenLinks
            t = link, self.parentURL
            brokenLinks.append(t)


'''
    Crawls URLs from a starting url within the given prefix. If no prefix is given
    the prefix is the domain of the starting url.
'''
class WebCrawler:
    def __init__(self, homeURL, prefix, linksToVisit):
        self.homeURL = homeURL
        self.prefix = self.getCorrectPrefix(prefix)
        self.linksToVisit = linksToVisit
        self.maxDistance = 0
        self.linksVisited = 0
        self.numDuplicateLinks = 0

    '''
        If a prefix is given, return the prefix.
        If no prefix is given, parse the domain as a prefix from URL being searched.
    '''
    def getCorrectPrefix(self, prefixGiven):
        if(not prefixGiven):
            prefixGiven = self.homeURL
            if(self.homeURL.find('http://') == 0):
                prefixGiven = self.homeURL[7:]
            elif(prefixGiven.find('/') != -1):
                prefixGiven = prefixGiven[:prefixGiven.find('/')]
            if(prefixGiven.find('.com') != -1):
                prefixGiven = prefixGiven[:prefixGiven.find('.com') + 4]
            elif(prefixGiven.find('.edu') != -1):
                prefixGiven = prefixGiven[:prefixGiven.find('.edu') + 4]
            elif(prefixGiven.find('.gov') != -1):
                prefixGiven = prefixGiven[:prefixGiven.find('.gov') + 4]
            elif(prefixGiven.find('.org') != -1):
                prefixGiven = prefixGiven[:prefixGiven.find('.org') + 4]
        return prefixGiven
    
    
    '''
        Extract effective url from a given URL.
        (i.e. remove "#something", "mailto:some_address", etc.)
    '''
    def fixGivenURL(self, url, currentDomain):
        if(url.startswith('#')):
            return False
        elif(url.find('javascript:') != -1 or url.find('.java') != -1):
            return False
        elif(url.find('mailto') != -1):
            return False
        elif(url.find('#') != -1):
            url = url[0:url.find('#')]
        if(url.startswith('//')):
            url = 'http:' + url
        elif(url.find('.com') == -1 and  url.find('.edu') == -1 and url.find('.gov') == -1 and url.find('.org') == -1):
            if(currentDomain.find(url) != -1):
                if(currentDomain.find('.') == -1):
                    url = self.prefix.replace(self.prefix[:self.prefix.find('.') + 1], currentDomain[:currentDomain.find('.') + 1]) + url
                    url = self.prefix + url
                else: 
                    url = currentDomain
            else:
                url = currentDomain + url
    
        if(not url.startswith('http')):
            url = 'http://' + url
        return url
    
    '''When first called crawl begins crawling recursively from the given home page'''
    def beginCrawl(self):
        homePage = WebPage(self.homeURL, 0, '')
        self.crawlURL(homePage, 0)

    def crawlURL(self, page, counter):
        '''do not create a sub-map if the page is out of domain'''
        if(page.getGivenURL().find(self.prefix) == -1):
            return
        
        '''do not duplicate key'''
        if(self.map.has_key(page.getGivenURL())):
            self.numDuplicateLinks += 1
        else:
            time.sleep(.5) #Courtesy
            listOfChildren = []
            for i in range(len(page.getChildren())):
                self.linksVisited += 1
                if (self.linksVisited <= self.linksToVisit):
                    childURL = self.fixGivenURL(page.getChildren()[i], page.getGivenURL())
                else:
                    return
                global externalWebPages
                if(childURL):
                    if(self.isExternalURL(childURL)):
                        self.externalLinks.append(childURL)
                    child = WebPage(childURL, counter + 1, page.getGivenURL())
                    listOfChildren.append(child)
                    
            self.map[page.getGivenURL()] = listOfChildren
            for i in range(len(listOfChildren)):
                if (self.linksToVisit - self.linksVisited > 0):
                    self.crawlURL(self.map[page.getGivenURL()][i], counter + 1)
                else: 
                    return
           
    
    
    '''
        Return true if the url is inside the searched domain (or prefix if given)
    '''
    def isExternalURL(self, url):
        return url.find(self.prefix[self.prefix.find('.') + 1:]) == -1
            
    '''
        Credit: Jeff Ondich
        Extract href links from text.
    '''
    def get_all_href_values(self, text):
     
        href_pattern = re.compile(r'<a.*?href="(.*?)"') 
        links = [] 
        for href_value in re.findall(href_pattern, text): 
            links.append(href_value) 
        return links
    
    '''
    1) Find links that can't get home;
    2) Return a list of links that can't get home
    '''
    def getStrandedLinks(self):
       stranded = True
       strandedLinks = []
       for key in self.map:
            for i in range(len(self.map[key])):
                for j in range(len(self.map[key][i].getChildren())):
                    if(key == self.homeURL or key == self.homeURL + '/' or key + '/' == self.homeURL):
                        stranded = False
                    elif(self.map[key][i].getChildren()[j] == self.homeURL or self.map[key][i].getChildren()[j] == self.homeURL + '/'):
                        stranded = False      
                if(stranded and key not in strandedLinks):
                    strandedLinks.append(key)
            stranded = True
       return strandedLinks
   
    '''
        return the number of unique links crawled.
    '''
    def getNumLinksCrawled(self):
        return self.linksVisited - self.numDuplicateLinks
    
    '''
        return greatest distance from searched start page to farthest webpage;
        if there are multiple paths to a same page, we compare the shortest paths
    '''    
    def getMaxDistance(self):
        return self.maxDistance
    
    '''
        return a list of links that are farthest from start page being searched
    '''
    def getMaxDistanceLinks(self):
        childrenList= self.map.values()
        allLinks = []
        
        #Extract all links from list of lists into a single list
        for i in range(len(childrenList)):
            for j in range(len(childrenList[i])):
                allLinks.append(childrenList[i][j])
    
        maxDistancePages = []
        for i in range(len(allLinks)):
            for j in range(len(allLinks)):
                if(allLinks[j].getGivenURL() == allLinks[i].getGivenURL()):
                    
                    minDistance = min(allLinks[i].getDistanceFromHome(), allLinks[j].getDistanceFromHome())
                    allLinks[j].setDistanceFromHome(minDistance)
                    allLinks[i].setDistanceFromHome(minDistance)
                    if(allLinks[i].getDistanceFromHome() > self.maxDistance):
                        maxDistancePages = []
                        maxDistancePages.append(allLinks[i].getGivenURL())
                        self.maxDistance = allLinks[i].getDistanceFromHome()
                    elif(allLinks[i].getDistanceFromHome() == self.maxDistance):
                        maxDistancePages.append(allLinks[i].getGivenURL())
        return maxDistancePages

    '''
        return a list of links that are outside the searched domain
    '''
    def getExternalLinks(self):
        return self.externalLinks
    
    '''
        return a list of tuples including broken links and their parent URLs
    '''
    def getBrokenLinks(self):
        return self.brokenLinks
      
def main(arguments):
    global brokenLinks
    brokenLinks = []
    linklimit = 0
    if(arguments.linklimit):
        linklimit = int(arguments.linklimit)
    else:
        linklimit = 1000
    crawler = WebCrawler(arguments.url, arguments.searchprefix, linklimit)

    crawler.beginCrawl()
   
    linksCantGetHome = crawler.getStrandedLinks()
    
    #print report
    if(arguments.actionsummary):
        print 'Files Found: ' + str(crawler.getNumLinksCrawled())
        print 'External Files: '
        externalLinks = crawler.getExternalLinks()
        for i in range(len(externalLinks)):
            print externalLinks[i]
        maxDistanceLinks =  crawler.getMaxDistanceLinks()
        print 'Longest Path Depth: ' + str(crawler.getMaxDistance())
        for i in range(len(maxDistanceLinks)):
            print maxDistanceLinks[i]
        print 'CantGetHome: '
        strandedLinks = crawler.getStrandedLinks()
        for i in range(len(strandedLinks)):
            print strandedLinks[i]
        
    elif(arguments.brokenlinks):
        print 'broken links: ' 
        for i in range(len(brokenLinks)):
            print brokenLinks[i]
    elif(arguments.outgoinglinks):
        crawler.getExternalLinks()
    else:
        print 'Files Found: ' + str(crawler.getNumLinksCrawled())
        print 'External Files: '
        externalLinks = crawler.getExternalLinks()
        for i in range(len(externalLinks)):
            print externalLinks[i]
        maxDistanceLinks =  crawler.getMaxDistanceLinks()
        print 'Longest Path Depth: ' + str(crawler.getMaxDistance())
        for i in range(len(maxDistanceLinks)):
            print maxDistanceLinks[i]
        print 'Can\'t Get Home: '
        strandedLinks = crawler.getStrandedLinks()
        for i in range(len(strandedLinks)):
            print strandedLinks[i]
    
    
if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser(description='Produce a report on the web page specified on the command line.')
    arg_parser.add_argument('url', help='Include only words that have a sortkey starting with this prefix.')
    arg_parser.add_argument('--linklimit', help='Maximum number of links to be searched; default = 1000.')
    arg_parser.add_argument('--searchprefix',help='Include only web pages that include the prefix; if no prefix specified, the domain of the URL is treated as a prefix.')   
    arg_parser.add_argument('--brokenlinks', action='store_true', help='Show broken links.')
    arg_parser.add_argument('--outgoinglinks', action='store_true',help='Show outgoing links.')
    arg_parser.add_argument('--actionsummary', action='store_true',help='Print a summary of the crawl.')
    arguments = arg_parser.parse_args()

    main(arguments)
