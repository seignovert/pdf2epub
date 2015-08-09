#!/usr/bin/env python
import logging
import re
from pdfminer.pdfdevice import PDFTextDevice
from pdfminer.pdffont import PDFUnicodeNotDefined
from pdfminer.layout import LTContainer
from pdfminer.layout import LTPage
from pdfminer.layout import LTText
from pdfminer.layout import LTLine
from pdfminer.layout import LTRect
from pdfminer.layout import LTCurve
from pdfminer.layout import LTFigure
from pdfminer.layout import LTImage
from pdfminer.layout import LTChar
from pdfminer.layout import LTTextLine
from pdfminer.layout import LTTextBox
from pdfminer.layout import LTTextBoxVertical
from pdfminer.layout import LTTextGroup
from pdfminer.utils import apply_matrix_pt
from pdfminer.utils import mult_matrix
from pdfminer.utils import enc
from pdfminer.utils import bbox2str
from pdfminer.converter import PDFConverter

from articleLayout import LAArticle

##  XHTMLConverter
##
class XHTMLConverter(PDFConverter):

    CONTROL = re.compile(ur'[\x00-\x08\x0b-\x0c\x0e-\x1f]')

    def __init__(self, rsrcmgr, outfp, codec='utf-8', pageno=1,
                 laparams=None, imagewriter=None, stripcontrol=False, document=None):
        PDFConverter.__init__(self, rsrcmgr, outfp, codec=codec, pageno=pageno, laparams=laparams)
        self.imagewriter  = imagewriter
        self.stripcontrol = stripcontrol
        self.document     = document
        self.rsrcmgr      = rsrcmgr
        self.write_header()
        return
    
    def end_page(self, page):
        assert not self._stack
        assert isinstance(self.cur_item, LTPage)

        if self.laparams is not None:
            if isinstance( self.laparams, LAArticle):
                self.laparams.analyzePage(self.cur_item,self.rsrcmgr )
            else:
                self.cur_item.analyze(self.laparams)
        # exit()
        
        self.pageno += 1
        self.receive_layout(self.cur_item)
        return
    
    def write_header(self):
        self.outfp.write('<?xml version="1.0" encoding="%s" ?>\n' % self.codec)
        self.outfp.write('<html xmlns="http://www.w3.org/1999/xhtml">\n')
        self.outfp.write('<head>\n')
        self.outfp.write('<meta charset="%s"/>\n' % self.codec)
        if self.document is not None:
            contents = self.document.info[0]
            if contents is not None:
                for name in contents:
                    if 'itle' in name:
                        self.outfp.write('<title>%s</title>\n' % contents[name])
                    else:
                        self.outfp.write('<meta name="%s" content="%s"/>\n' % (enc(name), contents[name]) )
        self.outfp.write('<meta name="Note" content="Converted with PDFminer.py for xhtml format"/>\n')
        self.outfp.write('<link rel="stylesheet" type="text/css" href="css/style.css"/>\n')
        self.outfp.write('</head>\n')
        self.outfp.write('<body>\n')
        return

    def write_footer(self):
        self.outfp.write('</body>\n')
        self.outfp.write('</html>\n')
        return
    
    def write_text(self, text):
        if self.stripcontrol:
            text = self.CONTROL.sub(u'', text)
        self.outfp.write(enc(text, self.codec))
        return

    def receive_layout(self, ltpage):
        def render(item):
            if isinstance(item, LTPage):
                self.outfp.write('<a id="page_%s" data-bbox="%s" data-rotate="%d"></a>\n' %
                                 (item.pageid, bbox2str(item.bbox), item.rotate))
                for child in item:
                    render(child)
            elif isinstance(item, LTLine):
                self.outfp.write('<line linewidth="%d" bbox="%s" />\n' %
                                 (item.linewidth, bbox2str(item.bbox)))
            elif isinstance(item, LTRect):
                self.outfp.write('<rect linewidth="%d" bbox="%s" />\n' %
                                 (item.linewidth, bbox2str(item.bbox)))
            elif isinstance(item, LTCurve):
                self.outfp.write('<curve linewidth="%d" bbox="%s" pts="%s"/>\n' %
                                 (item.linewidth, bbox2str(item.bbox), item.get_pts()))
            elif isinstance(item, LTFigure):
                self.outfp.write('<figure name="%s" bbox="%s">\n' %
                                 (item.name, bbox2str(item.bbox)))
                for child in item:
                    render(child)
                self.outfp.write('</figure>\n')
            elif isinstance(item, LTTextLine):
                self.outfp.write('<span data-bbox="%s"/>\n' % bbox2str(item.bbox))
                for child in item:
                    render(child)
                # self.outfp.write('</p>\n')
            elif isinstance(item, LTTextBox):
                wmode = ''
                if isinstance(item, LTTextBoxVertical):
                    wmode = ' wmode="vertical"'
                self.outfp.write('<div id="%d" data-bbox="%s" data-wmode="%s"><p>\n' %
                                 (item.index, bbox2str(item.bbox), wmode))
                for child in item:
                    render(child)
                self.outfp.write('</p></div>\n')
            elif isinstance(item, LTChar):
                # self.outfp.write('<text font="%s" bbox="%s" size="%.3f">' %
                #                  (enc(item.fontname), bbox2str(item.bbox), item.size))
                self.write_text(item.get_text())
                # self.outfp.write('</text>\n')
            elif isinstance(item, LTText):
                self.outfp.write(item.get_text())
            elif isinstance(item, LTImage):
                if self.imagewriter is not None:
                    name = self.imagewriter.export_image(item)
                    self.outfp.write('<img src="%s" width="%d" height="%d" />\n' %
                                     (enc(name), item.width, item.height))
                else:
                    self.outfp.write('<img width="%d" height="%d" />\n' %
                                     (item.width, item.height))
            else:
                assert 0, item
            return
        render(ltpage)
        return

    def close(self):
        self.write_footer()
        return
