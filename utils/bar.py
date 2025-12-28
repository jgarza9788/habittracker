def bar(percent):
    length=25
    fillnum = ((int)( (percent) * length))
    fillchar='▮'
    emptychar='_'
    return ( fillnum * fillchar ).ljust(length,emptychar) + f" {(percent)*100.0:05.2f}%" 

