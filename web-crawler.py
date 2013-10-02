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
    
    We chose to have the prefix be a find function as opposed to a begin with as prefixes normally are.
    This is because we believe it would be much more useful for our target users. For instance if carleton.edu
    is the prefix given, the search space for a prefix would be empty because urls are www.carleton.edu or apps.carleton.edu.
    If the user wants to search cs.carleton.edu for example our program still works as if it were a prefix.
'''

import sys
import re
import urllib2
import argparse
import time
import urlparse


class WebPage:
    '''
    Stores a URL and important information (e.g. HTML code, its children links, etc.)
    '''
    def __init__(self, link, distance, p):
        '''
        @param link: the url of the web page
        @param distance: distance from home
        @param p: the parent url from which the webpage was accessed  
        '''
        self.parentURL = p
        self.givenURL = link
        self.brokenLinks = []
        self.distanceFromHome = distance
        self.pageHTML = self.readURL(self.givenURL)
        self.children = []
        if(self.pageHTML):
            self.children = self.getAllHrefValues(self.pageHTML)
            
    def getParentURL(self):
        '''
        @return: the url from which this page was accessed
        '''
        return self.parentURL
    
    def getGivenURL(self):
        '''
        @return: returns a string of the url for the web page
        '''
        return self.givenURL
    
    def setDistanceFromHome(self, d):
        '''
        @param d: the distance from home
        '''
        self.distanceFromHome = d
        
    def getDistanceFromHome(self):
        '''
        @return: the distance from the home page in a given path(not necessarily the shortest possible path)
        '''
        return self.distanceFromHome
    
    def getChildren(self):
        '''
        @return: list children links from the given url
        '''
        return self.children
    
    def getAllHrefValues(self, text):
        '''
        @param text: A string of html text
        @return: a list of links from the text 
        '''
        hrefPattern = re.compile(r'<a.*?href="(.*?)"')
        links = [] 
        for hrefValue in re.findall(hrefPattern, text): 
            links.append(hrefValue)
        return links
    

    def readURL(self, link):
        '''
            @param link: A link to read
            @return: A string of html from link if a working link is given, else returns false.
            if a link is broken add to list of broken links
            @author: Jeff Ondich
            
        '''
        try: 
            request = urllib2.Request(link) 
            response = urllib2.urlopen(request) 
            text_of_requested_page = response.read() 
            response.close()
            return text_of_requested_page
        except Exception, e:
            self.addBrokenLink(link, self.getParentURL())
            return False

    def addBrokenLink(self, brokenLink, parent):
        '''
        @param brokenLink: broken link
        @param parent: link from which the broken link was taken
        '''
        t = brokenLink, parent
        self.brokenLinks.append(t)
        

class WebCrawler:
    '''
    Crawls URLs from a starting url within the given prefix. If no prefix is given
    the prefix is the domain of the starting url.
    '''
    def __init__(self, homeURL, prefix, linksToVisit):
        '''
        @param homeURL: the web page from which to begin the crawl
        @param prefix: the search domain, will not crawl links outside of domain
        @param linksToVisit: number of links to visit during the crawl
        '''
        self.homeURL = homeURL
        self.prefix = self.getCorrectPrefix(prefix)
        self.linksToVisit = linksToVisit
        self.maxDistance = 0
        self.linksVisited = 0
        self.numDuplicateLinks = 0
        self.map = {}
        self.externalLinks = []
    '''
        If a prefix is given, return the prefix.
        If no prefix is given, parse the domain as a prefix from URL being searched.
    '''
    def getCorrectPrefix(self, prefixGiven):
        '''
        @param prefixGiven: the prefix passed to __init__
        @return: if no prefix was passed to __init__ then gets the search domain from the home page url, or else it returns the prefix given
        @note: If a prefix includes http:// then it greatly reduces the number of crawl-able web pages.
        @note: .com, .edu ... are not the only options however it is too hard to cut the string with a general case and this covers
        a large portion of the web we want to deal with.
        '''
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
        '''
        @param url: the url that requires fixing to a callable url
        @param currentDomain: the current domain of the website being crawled. Note that this has nothing to do with the search domain.
        @return: A url that is readable by urllib2 (most of the time).
        @bug: if a link is only //link then we try to add it to the current domain but it does not work all of the time.
        If it does not work we add it to broken links even though it could still be working on the actual website.
        '''
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
    
    def beginCrawl(self):
        '''
        When first called crawl begins crawling recursively from the given home page
        '''
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
           
    
    def isExternalURL(self, url):
        '''
        @param url: a url to be examined
        @return: True if the url is inside the search domain and false if it is not in the search domain 
        '''
        return url.find(self.prefix[self.prefix.find('.') + 1:]) == -1
    
    
    def getStrandedLinks(self):
        '''
        @return: returns a list of links that do not link to the homepage
        '''
        stranded = True
        strandedLinks = []
        for key in self.map:
             if(not isStrandedLink(key)):
                 strandedLinks.append(key)
        return strandedLinks
    
    
    def isStrandedLink(self, link):
        '''
        @param link: a url which needs to be checked to see if it cannot reach home
        @return: return true if the link does not have a link to the homepage and false if the link does have a link to the homepage
        '''
        for i in range(len(self.map[link])):
                for j in range(len(self.map[link][i].getChildren())):
                    stranded = True
                    if(link == self.homeURL or key == self.homeURL + '/' or link + '/' == self.homeURL):
                        stranded = False
                    elif(self.map[link][i].getChildren()[j] == self.homeURL or self.map[link][i].getChildren()[j] == self.homeURL + '/'):
                        stranded = False  
        return stranded
       
    def getNumLinksCrawled(self):
        '''
        @return: the number of unique links crawled.
        '''
        return self.linksVisited - self.numDuplicateLinks
    
    def getMaxDistance(self):
        '''
        @return: the length of the longest searched path from the home page
        '''
        return self.maxDistance
    
    def getMaxDistancePath(self):
        '''
        @todo: fix it
        @return: a list of links that form the longest searched path from the home page to the farthest web page
        @note: if there are multiple paths to a same page, we compare the shortest paths

        '''
        childrenList= self.map.values()
        allLinks = []
        
        #Extract all links from list of lists into a single list
        for i in range(len(childrenList)):
            for j in range(len(childrenList[i])):
                allLinks.append(childrenList[i][j])
                
        paths = []
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
        return maxDistancePages


    def getExternalLinks(self):
        '''
        @return: a list of links that are outside the searched domain
        '''
        return self.externalLinks
    
    def getBrokenLinks(self):
        '''
        @return: a list of tuples formatted so that each item in the list is (broken link, parent url)
        '''
        brokenLinks = []
        for url in self.map.values:
            for i in range(len(self.map[url])):
                for j in range(len(self.map[url][i].getBrokenLinks())):
                    brokenLinks.append(self.map[url][i].getBrokenLinks.pop())
        return brokenLinks
      
def main(arguments):
    '''
    @param arguments: command line arguments to be read
    @note: creates a crawler, runs the crawler, and prints out a summary
    '''
    linkLimit = arguments.linklimit

    crawler = WebCrawler(arguments.url, arguments.searchprefix, linkLimit)
    crawler.beginCrawl()
    
    if(arguments.action == 'brokenlinks'):
        printBrokenLinks(crawler)
    if(arguments.action == 'outgoinglinks'):
        printOutGoingLinks(crawler)
    else:
        printActionSummary(crawler)
        
    
def printBrokenLinks(crawler):
    '''
    @param crawler: The crawler from which the report is to be printed
    @note: prints a list of broken links 1 per line.
    '''
    brokenLinks = crawler.getBrokenLinks()
    print 'broken links: ' 
    for i in range(len(brokenLinks)):
        print brokenLinks[i]

def printOutGoingLinks(crawler):
    '''
    @param crawler: The crawler from which the report is to be printed
    @note: prints a list of outgoing links 1 per line
    '''
    outgoingLinks = crawler.getExternalLinks()
    for i in range(len(outgoingLinks)):
        print brokenLinks[i]
    
def printActionSummary(crawler):
    '''
    @param crawler: The crawler from which the report is to be printed
    @note: prints a list of outgoing links, the farthest page from home, the path to the farthest page, and a list of pages that can't get home
    '''
    linksCantGetHome = crawler.getStrandedLinks()
    print 'Files Found: ' + str(crawler.getNumLinksCrawled())
    print 'External Files: '
    externalLinks = crawler.getExternalLinks()
    for i in range(len(externalLinks)):
        print externalLinks[i]
    maxDistancePath =  crawler.getMaxDistancePath()
    print 'Longest Path Depth: ' + str(crawler.getMaxDistance())
    for i in range(len(maxDistancePath)):
        print maxDistancePath[i]
    print 'Can\'t Get Home: '
    strandedLinks = crawler.getStrandedLinks()
    for i in range(len(strandedLinks)):
        print strandedLinks[i]


if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser(description='Produce a report on the web page specified by the command line.')
    arg_parser.add_argument('url', help='The required starting url from which a crawl will begin')
    arg_parser.add_argument('--linklimit', type = int, default = 1000, help='Maximum number of links to be searched; default = 1000.')
    arg_parser.add_argument('--searchprefix',help='Include only web pages that include the prefix; if no prefix specified, the domain of the URL is treated as a prefix.')   
    arg_parser.add_argument('--action', choices=['brokenlinks', 'outgoinglinks', 'summary'], default = 'summary', type=str, help = 'brokenlinks will print out a list of broken links and the pages on which they occur. Outgoing links prints out a list of links that go outside of the search domain. Summary prints out the number of files found, the longest path found and the distance of that path, and a list of urls that can\'t get home')
    arguments = arg_parser.parse_args()

    main(arguments)
