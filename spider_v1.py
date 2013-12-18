#!/usr/bin/python
# -*- coding:  utf-8 -*-
# Filename : spider_v1.py
# Date : 2013-11-11
# Author : wwpeng
# Email : 591826944@qq.com
import urllib2, re, StringIO, gzip, time, os, threading, json
#set global params
PARAMS = {
                    'debug' : 0,  \
                    'requestinfo' : 0,  \
                    'savepath': os.path.split(os.path.realpath(__file__))[0] + '/duowantuku', \
                    'dbpath' : os.path.split(os.path.realpath(__file__))[0] + '/db', \
                    'visiteddb' : 'visiteddb.json', \
                    'imagedb' : 'imagedb.json', \
                  }
#url and header params
URL = (
                "http://tu.duowan.com/tag/5037.html",  \
                {
                'Accept-Encoding' : 'gzip,deflate,sdch',  \
                'User-Agent' : 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/30.0.1599.114 Chrome/30.0.1599.114 Safari/537.36',  \
                'Referer' : 'http://tu.duowan.com/tu',  \
                'Cache-Control' : 'max-age=0',  \
                'Accept' : 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',  \
                },  \
                30, \
           ) 
#function main geturl
def main():
    trace('Download duowantuku images start!....')
    #read history
    mkdir(PARAMS['savepath'])
    mkdir(PARAMS['dbpath'])
    try : 
        with open(PARAMS['dbpath'] + '/' + PARAMS['visiteddb'], "r") as visited:
            visitedUrl = json.loads(visited.read())
    except : 
        visitedUrl = {}
    try : 
        with open(PARAMS['dbpath'] + '/' + PARAMS['imagedb'], "r") as db:
            imageDB = json.loads(db.read())
        if len(imageDB) == 0 :
            imageDB = {}
    except : 
        imageDB = {}
    #check response content-encodingcheckCompressData
    result = matchString(checkCompressData(requestUrl()),'<a href="(http://tu.duowan.com/.*\.html)" target="_blank">今日囧图第(.*)弹</a>', 0, 1)
    if result is None or visitedUrl.has_key(result[0][1]) :
        trace('Not found new "jiongtu" link!')
        exit()
    else : 
        visitedUrl[result[0][1]] = result[0][0]
    
    #get image gallery page content
    response = requestUrl(result[0][0])
    realUrl = response.geturl().replace('/gallery/', '/scroll/')
    response.close()
    #get 301 real url content
    content = checkCompressData(requestUrl(realUrl))
    images = getImageList(content)
    if not images :
        trace('Not found images!', 'warning')
        exit()
    #get pages
    pages = matchString(content, '<a class=".*" href="%s">\d*</a>' % ('/'+'/'.join(realUrl.split('/')[-2:]).replace('.', '(\/\d*)?\.')))
    trace('Get pages total %d ' % (len(pages, )))
    pages.remove("")
    if len(pages) > 1 :
        for page in pages : 
            images.extend(getImageList(checkCompressData(requestUrl(realUrl.replace('.html', '%s.html' % (page, ))))))
    trace('Get pictures total %d ' % (len(images, )))
    #download image
    dtrace('Start download image from 1 page!')
    for key, imageMatch in enumerate(images) :
        dtrace('Start download %dst image!' % (key+1, ))
        imagename = '%s_%d.%s' % (result[0][1], key+1, imageMatch[0].split('.')[-1])
        if imageDB.has_key(imagename) : 
            dtrace('%s has exists!' % (imagename, ))
        else : 
            image(imageMatch[0], PARAMS['savepath']+"/%s" % (imagename, )).start()
            imageDB[imagename] = imageMatch[1]
    
    while threading.activeCount() > 1 :
        time.sleep(2)
        trace('There are %d pictures download' % (threading.activeCount(), ))
    else : 
        #written record
        with open(PARAMS['dbpath'] + '/' + PARAMS['visiteddb'], "w") as visited:
            visited.write(json.dumps(visitedUrl, sort_keys=True))
        with open(PARAMS['dbpath'] + '/' + PARAMS['imagedb'], "w") as db:
            db.write(json.dumps(imageDB, sort_keys=True))
        #run completed
        trace('Download duowantuku images completed!....')
 
def getImageList(content):
    return matchString(content, '<img src="(http://s1.dwstatic.com/.*)" alt=".*"></a>\s*<p class="comment">(.*)</p>')
    
#Initiate a request
def requestUrl(url = URL[0], headers = URL[1], timeout=URL[2]):
    requestinfo()
    dtrace('Request url ( %s )' % (url, ))
    request = urllib2.Request(url, headers = headers)
    try : 
        response = urllib2.urlopen(request, timeout = timeout)
        dtrace('Read url ( %s ) content success!' % (url, ));
        return response
    except urllib2.HTTPError,  e:
        dtrace('Request url ( %s ) failed! < Error code > %s' % (e.code, ), 'error')
    except urllib2.URLError,  e:
        dtrace('We failed to reach a server! < Error reason > %s' % (e.reason, ), 'error')
    return None
#get match content
def matchString(content, regex , start = None, end = None):
    results = []
    #remove \r \n \t
    #content = content.replace('\r', '').replace('\n', '').replace('\t', '')
    if start is not None :
        start = int(start)
    if end is not None : 
        end = int(end)
    pattern = re.compile(regex, re.I)
    matchs = pattern.findall(content) 
    if not matchs :
        dtrace('( Regex: %s ) Match result is None!' % regex, 'warning')
    else:
        results =  matchs[start : end]
    return results
#get content
def checkCompressData(response):
    if not response : 
        return None
    if response.headers.has_key('Content-Encoding'):
        dtrace('Response content encodeing is %s' % (response.headers['Content-Encoding'], ))
        if response.headers['Content-Encoding'] != 'gzip' : 
            dtrace('Response encodeing is not gzip!', 'warning')
        fileobj = StringIO.StringIO()
        fileobj.write(response.read())
        fileobj.seek(0)
        gzip_file = gzip.GzipFile(fileobj=fileobj)
        content = gzip_file.read()
    else:
        content = response.read()
    response.close()
    return content
#create path
def mkdir(path):
    if not os.path.exists(path) : 
        os.makedirs(path)
        dtrace('Create path ( %s ) success!' % (path, ))
#show request header
def requestinfo():
    if PARAMS['requestinfo'] : 
        trace('Show request info!')
        # open debug and set opener
        httpHandler = urllib2.HTTPHandler(debuglevel=1)  
        httpsHandler = urllib2.HTTPSHandler(debuglevel=1)  
        opener = urllib2.build_opener(httpHandler, httpsHandler)  
        urllib2.install_opener(opener)  
#print debug message
def dtrace(message, flag="info") :
    if PARAMS['debug']  :
        trace(message, flag)
#print message
def trace(message, flag="info"):
    print '[ %s ] %s' % (flag, message)
#download image
class image(threading.Thread):
    def __init__(self,url, path):
        threading.Thread.__init__(self)
        self.url = url
        self.path = path
    
    def run(self):
        imageData = checkCompressData(requestUrl(self.url))
        if imageData : 
            with open(self.path, "wb") as image:
                image.write(imageData)
            dtrace('Download image ( %s ) success!' % (self.path.split('/')[-1]))
        else : 
            dtrace('Download image ( %s ) failed!' % (self.path.split('/')[-1]), 'warning')

main()
