
def isdomain(url, domain) :
    w1 =  url.split("//")
    w2 = w1[1]
    w3 = w2.split("/")
    newDomain = w3[0]
    if(newDomain == domain) :
        return True
    else :
        return False

def giveDomain(url) :
    w1 =  url.split("//")
    w2 = w1[1]
    w3 = w2.split("/")
    domain = w3[0]
    return domain

    #A URL's syntax: protocol://domain/path?query#fragmen
#def notInRobo() :