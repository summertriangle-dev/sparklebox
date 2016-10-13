from html.parser import HTMLParser
import urllib.request

def getHtml(url):
    page = urllib.request.urlopen(url)
    html = page.read()
    return html
    
class MyHTMLParser(HTMLParser):
    get_version = False
    
    def __init__(self):
        HTMLParser.__init__(self)
        self.version = "1.9.1"
    def handle_starttag(self, tag, attrs):
        if tag == "span":
            if len(attrs) == 0:
                pass
            else:
                for (variable, value) in attrs:
                    if (variable == "itemprop" and value == "softwareVersion"):
                        self.get_version = True
                        
    def handle_endtag(self,tag):
        if tag == 'span':
            self.get_version = False
              
    def handle_data(self,data):
        if self.get_version:
            self.version = data
            
if __name__ == "__main__":
    
    store_b = getHtml("https://itunes.apple.com/jp/app/aidorumasuta-shindereragaruzu/id1016318735?mt=8")
    store = store_b.decode('utf-8')
    
    proc = MyHTMLParser()
    proc.feed(store)
    proc.close()
    print("get app_ver:", proc.version)
    
