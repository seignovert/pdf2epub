from pdfminer.layout import LAParams
# from pdfminer.layout import LTContainer
from pdfminer.layout import LTPage
# from pdfminer.layout import LTText
# from pdfminer.layout import LTLine
# from pdfminer.layout import LTRect
from pdfminer.layout import LTCurve
from pdfminer.layout import LTFigure
# from pdfminer.layout import LTImage
from pdfminer.layout import LTChar
# from pdfminer.layout import LTTextLine
# from pdfminer.layout import LTTextBox
# from pdfminer.layout import LTTextBoxVertical
# from pdfminer.layout import LTTextGroup
from pdfminer.layout import LTItem, LTComponent
from pdfminer.utils import bbox2str,INF

# import matplotlib.pyplot as plt

class LAArticle(LAParams):

    def __init__(self, line_overlap=0.5, header_perc=7.5, footer_perc=7.5):

        LAParams.__init__(self, line_overlap=line_overlap, char_margin=line_overlap,
                          line_margin=line_overlap, word_margin=line_overlap,
                          boxes_flow=line_overlap, detect_vertical=False, all_texts=False)

        self.header_perc = header_perc  # Fraction of the header (% of the page) 
        self.footer_perc = footer_perc  # Fraction of the footer (% of the page)
        return

    def __repr__(self):
        return ('<%s>' % (self.__class__.__name__))

    def getfont(self,fontname):
        for font in self.rsrcmgr._cached_fonts:
            if fontname in self.rsrcmgr._cached_fonts[font].basefont:
                return self.rsrcmgr._cached_fonts[font]
    
    def analyzePage(self, page, rsrcmgr ):
        self.rsrcmgr  = rsrcmgr 
        self.page     = page
        self.boxs     = []
        
        for box in self.scan(page.bbox, hmargin = 7.5, vmargin = 1.75):
            self.boxs.append( LTArticleBoxs(box) )      

        headFrac = ( 100. - self.header_perc ) * self.page.y1 /100.
        footFrac =          self.footer_perc   * self.page.y1 /100.

        for box in self.boxs:
            self.fill(box)
            box.find_lines()
            box.is_header(headFrac)
            box.is_footer(footFrac)
            print box, len(box)
            
        # plt.figure()        

        # for child in page:
        #     self.draw(child.bbox,'b')

        # for (ii,box) in enumerate(self.boxs):
        #     self.draw(box,'r',ii)

        # self.draw(self.page.bbox,'b')
        # plt.axis('equal')
        # plt.show()
        # plt.close()

        exit()
        
        return 0

    def is_bbox_inside(self,box,obj):  # Check if obj.bbox is in box
        return ( box[0] <= obj.x0 and obj.x1 <= box[2] and \
                 box[1] <= obj.y0 and obj.y1 <= box[3] )

    def is_matrix_inside(self,box,obj):  # Check if matrix is in box
        return ( box[0] <= obj.matrix[4] and obj.matrix[4] <= box[2] and \
                 box[1] <= obj.matrix[5] and obj.matrix[5] <= box[3] )

    def hscan(self,box,margin):
        """
        Child is a glyph print, Hline represent a white area. This scan finds blank vertical line (aera without glyph) in the box.

        |------| ll    lr  ;   |------|     ;     |-----|     ;  |----------|   ;      |------|  ;  ll    lr  |------|   Child
        cl    cr |------|  ;      |------|  ;  |----------|   ;     |-----|     ;  |------|      ;  |------|  cl    cr   HLine   
        F      F           ;   F      T     ;     T     T     ;  F          F   ;      T      F  ;            F      F   Is In? 
                 ll    lr  ;         cr lr  ; ll  cl   cr lr  ; ll          lr  ;  ll  cl        ;  ll    lr             
                 |------|  ;          |--|  ;  |--|     |-|   ;  |          |   ;  |---|         ;  |------|             Result 
               None        ;    cr -> ll    ;   add cl cr     ;   drop ll lr    ;     cl -> lr   ;       None            Action 
 
        """
        (bl,bb,br,bt) = box
        hline = [[0,bl],[bl,br],[br,self.page.x1]]
        nn    = 1
        for child in self.page:
            if isinstance(child, LTChar):
                if self.is_matrix_inside(box,child):
                    (cl,cb,cr,ct) = child.bbox
                else:
                    continue
            else:
                if self.is_bbox_inside(box, child):      # CHILD is in BOX            
                    (cl,cb,cr,ct) = child.bbox
                else:
                    continue

            for ii in range(nn,0,-1):                    # Horizontal scan of the lines avaibles
                (ll,lr) =  hline[ii]
                if cr > ll and cl < lr:                  # Exclude case 1 / 6
                    if cr < lr:                          # Exclude case 4 / 5
                        if cl <= ll:                     # Exclude case 3     => case 2
                            hline[ii][0] = cr                    
                            if cl >= hline[ii-1][1]:     # Check if the child can touch the next right hline
                                break                         
                        else :                           # => case 3
                            hline.insert(ii, [ll,cl] )
                            hline[ii+1][0] = cr
                            nn +=1
                            break                        
                    else :                                
                        if cl > ll:                      # Exclude case 4 => case 5
                            hline[ii][1] = cl
                            break
                        else :                           # => case 4 
                            hline.pop(ii)
                            nn -= 1
                            if cl >= hline[ii-1][1]:     # Check if the child can touch the next right hline
                                break
        for ii in range(nn+1,-1,-1):
            if ( hline[ii][1] - hline[ii][0] ) <= margin:
                hline.pop(ii)
                nn -= 1
        boxs = []
        for ii in range(0,nn+1):
            if hline[ii][1] != hline[ii+1][0] :
                boxs.append( [ hline[ii][1],bb,hline[ii+1][0],bt ] )
        return boxs

    def vscan(self,box, margin=0, char_height=12, char_descent=2):
        """
        Child is a glyph print, Vline represent a white area. This scan finds blank horizontal line (aera without glyph) in the box.
        (idem in vertical) 
        """
        (bl,bb,br,bt) = box
        vline = [[0,bb],[bb,bt],[bt,self.page.y1]]
        nn    = 1
        for child in self.page:
            if isinstance(child, LTChar):
                if self.is_matrix_inside(box,child):
                    (cl,cb,cr,ct) = child.bbox
                    cb = child.matrix[5] - char_descent
                    ct = child.matrix[5] + char_height - char_descent
                else:
                    continue
            else:
                if self.is_bbox_inside(box, child):      # CHILD is in BOX            
                    (cl,cb,cr,ct) = child.bbox
                else:
                    continue
                
            for ii in range(nn,0,-1):                    # Vertical scan of the lines avaibles
                (lb,lt) =  vline[ii]
                if ct > lb and cb < lt:                  # Exclude case 1 / 6
                    if ct < lt:                          # Exclude case 4 / 5
                        if cb <= lb:                     # Exclude case 3     => case 2
                            vline[ii][0] = ct                    
                            if cb >= vline[ii-1][1]:     # Check if the child can touch the next bottom vline
                                break                         
                        else :                           # => case 3
                            vline.insert(ii, [lb,cb] )
                            vline[ii+1][0] = ct
                            nn +=1
                            break                        
                    else :                                
                        if cb > lb:                      # Exclude case 4 => case 5
                            vline[ii][1] = cb
                            break
                        else :                           # => case 4 
                            vline.pop(ii)
                            nn -= 1
                            if cb >= vline[ii-1][1]:     # Check if the child can touch the next bootom vline
                                break
        for ii in range(nn+1,-1,-1):
            if ( vline[ii][1] - vline[ii][0] ) <= margin:
                vline.pop(ii)
                nn -= 1
        boxs = []
        for ii in range(nn,-1,-1):
            if vline[ii][1] != vline[ii+1][0] :
                boxs.append( [ bl,vline[ii][1],br,vline[ii+1][0] ] )
        return boxs

    def scan(self, init_box, hmargin=2.5, vmargin=2.5, hscan_first=True):
        boxs   = [init_box]
        _hscan = hscan_first
        nh = 0 ; nv = -1
        while nh != nv:             # Stop when then number of vertical boxs == number of horizontal boxs
            boxs_found =[]
            if _hscan:
                for box in boxs:
                    if hmargin > 0.:
                        hboxs = self.hscan(box, margin = hmargin)
                    else:
                        hboxs = [box]

                    for hbox in hboxs:
                        boxs_found.append(hbox)
                _hscan = False
                nh = len(boxs_found)
            else:
                for box in boxs:
                    if vmargin > 0. :
                        vboxs = self.vscan(box, margin = vmargin)
                    else:
                        vboxs = [box]
                    
                    for vbox in vboxs:
                        boxs_found.append(vbox)
                _hscan = True
                nv = len(boxs_found)
            boxs = boxs_found
            if (nh > 250 or nv > 250):
                raise ValueError('Number of boxs detected is too high (>250). Change V/H margins.')
        return boxs
    
    def fill(self,box):
        for child in self.page:
            if isinstance(child, LTChar):
                if self.is_matrix_inside(box.bbox,child):
                    box.add(child)
            elif self.is_bbox_inside(box.bbox, child):
                box.add(child)
        return






    
    # def draw(self,box,color,string=None):
    #     plt.plot( self.x(box), self.y(box), color+'-' )
    #     if string is not None:
    #         plt.text( self.xm(box), self.ym(box), string, color=color)

    # def draw2(self,pt,color, string=None):
    #     plt.plot( pt[0], pt[1], color+'o' )
    #     if string is not None:
    #         plt.text( pt[0], pt[1], string, color=color)

    # def x(self,bbox):
    #     (x0,_,x1,_) = bbox
    #     return [x0,x1,x1,x0,x0]
    
    # def y(self,bbox):
    #     (_,y0,_,y1) = bbox
    #     return [y0,y0,y1,y1,y0]

    # def xm(self,bbox):
    #     (x0,_,x1,_) = bbox
    #     return (x0+x1)/2.0
    
    # def ym(self,bbox):
    #     (_,y0,_,y1) = bbox
    #     return (y0+y1)/2.0





class LTArticleBoxs(LTComponent):
    
    def __init__(self, bbox):
        LTComponent.__init__(self, bbox)
        self._chars  = []
        self._figs   = []
        self._curves = []
        self.type = None
        self.font = None
        return

    def __repr__(self):
        return ('<%s %s Type=%r Font=%r>' % (self.__class__.__name__, bbox2str(self.bbox),
                                             self.type, self.font))
    def __iter__(self):
        return iter(self._chars)

    def __len__(self):
        return len(self._chars)

    def add(self, obj):
        if isinstance(obj, LTChar):
            self._chars.append(obj)
        elif isinstance(obj, LTFigure):
            self._figs.append(obj)
            self.set_type('Figure')
        elif isinstance(obj, LTCurve):
            self._curves.append(obj)
        else:
            raise TypeError('ADD %r to %r is not defined' % (obj.__class__.__name__, self.__class__.__name__))
        return
    
    def set_type(self,Type):
        self.type = Type
        return

    def is_header(self,headFrac):
        if self.y0 >= headFrac :
            if self.type is None:
                self.set_type('Header')
            else:
                raise TypeError('Header is already %r' % self.type)
        
    def is_footer(self,footFrac):
        if self.y1 <= footFrac :
            if self.type is None:
                self.set_type('Footer')
            else :
                raise TypeError('Footer is already %r' % self.type)

    def boxFont(self):
        fonts = {}
        for char in self:
            if not char.fontname in fonts:
                fonts[char.fontname] =1
            else:
                fonts[char.fontname] +=1
        return max(fonts, key=fonts.get)

    def fill_lines(self):
        lines = {}
        for char in self:
            baseline = char.matrix[5]
            if not baseline in lines:
                lines[ baseline ] = LTArticleLines(baseline, self.font)
            lines[ baseline ].add(char)

        for line in reversed(sorted(lines)):
            print lines[line].read()    
        
    def find_lines(self):
        self.font = self.boxFont()
        self.fill_lines()
        return

class LTArticleLines(LTComponent):

    def __init__(self,baseline,font):
        LTComponent.__init__(self, (+INF, +INF, -INF, -INF))
        self._chars   = []
        self._text    = []
        self.baseline = baseline
        self.font     = font
        self.type     = None
        return

    def __repr__(self):
        return ('<%s %s Type=%r Font=%r>' % (self.__class__.__name__, bbox2str(self.bbox),
                                             self.type, self.font))
    def __iter__(self):
        return iter(self._chars)

    def __len__(self):
        return len(self._text)

    def read(self):
        return self._text

    def updateBbox(self,char):
        if char.x0 < self.x0 :
            self.x0 = char.x0
        if char.y0 < self.y0 :
            self.y0 = char.y0
        if char.x1 < self.x1 :
            self.x1 = char.x1
        if char.y1 < self.y1 :
            self.y1 = char.y1
        return

    def add(self,char):
        if not char in self._chars:
            self._chars.append(char)
            self.updateBbox(char)
            
        self._text.append(char.get_text())
