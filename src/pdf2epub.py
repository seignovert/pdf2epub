#!/usr/local/opt/python/bin/python2.7
import sys
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfparser import PDFParser
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfdevice import PDFDevice, TagExtractor
from pdfminer.pdfpage import PDFPage
from pdfminer.converter import XMLConverter, HTMLConverter, TextConverter
from pdfminer.cmapdb import CMapDB
from pdfminer.image import ImageWriter
from pdfminer.pdftypes import stream_value, dict_value, str_value

from articleLayout  import LAArticle
from xhtmlConverter import XHTMLConverter


# main
def main(argv):

    infile  = sys.argv[1]
    outfile = 'test.xhtml'

    fp    = file(infile, 'rb')
    outfp = file(outfile, 'w')     # OR sys.stdout

    password    = ''
    codec       = 'utf-8'
    caching     = True
    
    parser   = PDFParser(fp)
    document = PDFDocument(parser, password=password, caching=caching)
    rsrcmgr  = PDFResourceManager(caching=caching)
    device   = XHTMLConverter(rsrcmgr, outfp, codec=codec, laparams=LAArticle(), document=document)

    interpreter = PDFPageInterpreter(rsrcmgr, device)
    
    for page in PDFPage.create_pages(document):
        interpreter.process_page(page)

    fp.close()
    device.close()
    outfp.close()
    return

if __name__ == '__main__':
    sys.exit( main(sys.argv) )
