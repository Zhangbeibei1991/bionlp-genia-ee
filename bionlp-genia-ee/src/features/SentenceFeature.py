"""
Created on Sep 6, 2013

@author: Andresta
"""

from features.Feature import Feature
from model.Dictionary import WordDictionary, TriggerDictionary

class SentenceFeature(Feature):
    """
    classdocs
    """


    def __init__(self, prefix, WDict, TDict):
        """
        Constructor
        """                
        if not (isinstance(WDict, WordDictionary) and isinstance(TDict,TriggerDictionary)):
            raise TypeError("Dictionary type is not match")
        
        super(SentenceFeature, self).__init__(prefix)
                
        self.wdict = WDict
        self.tdict = TDict
        
    def _extract_common_feature(self, o_sen, trig_wn, arg_wn):
       
        nword = o_sen.nwords        
        
        ''' ------ position ------ '''
        # trigger first or last in sen
        if trig_wn == 0:
            self.add("tfirst", True)
        if trig_wn == nword:
            self.add("tlast", True)
            
        # arg first or last in sen
        if arg_wn == 0:
            self.add("afirst", True)
        if arg_wn == nword:
            self.add("alast", True)
            
        # argument before trigger
        if arg_wn < trig_wn:
            self.add("a_bef_t", True)
            
        # word distance trigger to argument
        self.add("dis_ta", trig_wn - arg_wn)
        
        
        ''' ------ word feature ------ '''
        # extract word feature for trigger
        self.extract_word_feature(o_sen.words[trig_wn], "t")
        
        # extract word feature for argument
        self.extract_word_feature(o_sen.words[arg_wn], "a")
        
        # extract word feature for words around trigger candidate
        if trig_wn - 1 >= 0:
            self.extract_word_feature(o_sen.words[trig_wn-1], "tw-1")
        if trig_wn + 1 < nword:
            self.extract_word_feature(o_sen.words[trig_wn+1], "tw+1")
            
        # extract word feature for words around protein
        if arg_wn - 1 >= 0:
            self.extract_word_feature(o_sen.words[arg_wn-1], "pw-1")
        if arg_wn + 1 < nword:
            self.extract_word_feature(o_sen.words[arg_wn+1], "pw+1")
        
    
    def in_between(self, i, trig_wn, arg_wn):
        if trig_wn > arg_wn:
            start = arg_wn
            end = trig_wn
        else:
            start = trig_wn
            end = arg_wn
        
        if i > start and i < end:
            return True
        else:
            return False
          
    def extract_feature_tp(self, o_sen, trig_wn, arg_wn):
        """
        extract sentence feature 
        """       
        # reset feature
        self.feature = {}
        
        # extract common feature
        self._extract_common_feature(o_sen, trig_wn, arg_wn)                


        # number of protein between trigger and argument
        n_prot = 0
        for p in o_sen.protein:
            if self.in_between(p, trig_wn, arg_wn):
                n_prot += 1
        self.add('n_prot', n_prot)

        # probability of trigger on each event
        self.add('score_1', self.get_score(o_sen.words[trig_wn], 'Gene_expression'))
        self.add('score_2', self.get_score(o_sen.words[trig_wn], 'Transcription'))
        self.add('score_3', self.get_score(o_sen.words[trig_wn], 'Protein_catabolism'))
        self.add('score_4', self.get_score(o_sen.words[trig_wn], 'Phosphorylation'))
        self.add('score_5', self.get_score(o_sen.words[trig_wn], 'Localization'))
        self.add('score_6', self.get_score(o_sen.words[trig_wn], 'Binding'))
        self.add('score_7', self.get_score(o_sen.words[trig_wn], 'Regulation'))
        self.add('score_8', self.get_score(o_sen.words[trig_wn], 'Positive_regulation'))
        self.add('score_9', self.get_score(o_sen.words[trig_wn], 'Negative_regulation'))
        
    
    def extract_feature_tt(self, o_sen, trig_wn, arg_wn):
        """
        extract sentence feature 
        """       
        # reset feature
        self.feature = {}
        
        # extract common feature
        self._extract_common_feature(o_sen, trig_wn, arg_wn)
        
        # argument type
        arg_type = o_sen.words[arg_wn]["type"]
        self.add("a_type", arg_type)
        
        # probability of argument event
        self.add('arg_prob', self.get_score(o_sen.words[trig_wn], arg_type))
                
        # probability of trigger on each event
        self.add('score_7', self.get_score(o_sen.words[trig_wn], 'Regulation'))
        self.add('score_8', self.get_score(o_sen.words[trig_wn], 'Positive_regulation'))
        self.add('score_9', self.get_score(o_sen.words[trig_wn], 'Negative_regulation'))
        
    def extract_tac_feature(self, o_sen, trig_wn, theme_wn, cause_wn):
        """
        extract sentence feature for trigger-theme-cause relation
        """
        
        # reset feature
        self.feature = {}
        
        # theme before trigger
        if theme_wn < trig_wn:
            self.add("a_bef_t", True)
            
        # cause before trigger
        if cause_wn < trig_wn:
            self.add("c_bef_t", True)
        
        # extract word feature for trigger
        self.extract_word_feature(o_sen.words[trig_wn], "t")
        
        # extract word feature for theme
        self.extract_word_feature(o_sen.words[theme_wn], "a")
        
        # extract word feature for cause
        self.extract_word_feature(o_sen.words[cause_wn], "c")
        
        # type of theme
        self.add("a_type", o_sen.words[theme_wn]["type"])
        
        # type of cause
        self.add("c_type", o_sen.words[cause_wn]["type"])
        
        # word distance trigger to theme
        self.add("dis_ta", trig_wn - theme_wn)
        
        # word distance trigger to cause
        self.add("dis_tc", trig_wn - cause_wn)
        
        
    
    def get_score(self, word, event_type):
        """
        calculate the probability score of trigger candidate for given event_type
        """
        retval = 0.0
        string = word["string"]
        w = self.wdict.count(string)
        if w != 0:
            retval = self.tdict.count(string, event_type) * 1.0 / w
        return retval
        
        
        
        
        
        