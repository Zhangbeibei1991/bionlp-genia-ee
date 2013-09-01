'''
Created on Aug 27, 2013

@author: Andresta
'''

import os, re, json
from collections import defaultdict
from ctypes.test.test_array_in_pointer import Value

class GeniaReader(object):
    '''
    read all necessary file and convert it to internal format, then save it for latter feature extraction
    '''
    
    ''' list of extension'''
    TXT_EXT = ".txt"
    
    PROTEIN_EXT = ".a1"
    
    TRIGGER_REL_EXT = ".a2"
    
    CHUNK_EXT = ".chk"
    
    MCCCJ_TREE_EXT = ".txt.ss.mcccjtok.mcccj"
    
    MCCCJ_SD_EXT = ".txt.ss.mcccjtok.mcccj.basic.sd"
    

    CORPUS_DIR = ["dev","train","test"]    
    
    # this folder contains original corpus of bionlp2011: txt, a1, and a2 files 
    ORIGINAL_DIR = "original"
    
    # this folder contains parsed corpus (tree and dependency) and also chunk file
    PARSED_DIR = "parse"    

    def __init__(self, source, dest):
        '''
        Constructor
        '''
        self.src = source
        self.dest = dest
        
        self.Dep = DependencyReader()
        self.Tree = ParseTreeReader()
        self.Chunk = ChunkReader()
        
        
    def run(self):
        # read all files from dir
        for cdir in self.CORPUS_DIR:
            # reading txt a1 and a2 from original dir
            path = self.get_full_path(self.ORIGINAL_DIR, cdir)
    
    
    def load_data(self, cdir, is_test):
        '''
        list all files then read them
        '''
        
        ext = self.TXT_EXT
            
        for doc_id in self.get_doc_list(cdir, ext):
            self.load_save_doc(cdir, doc_id, is_test)
            
    
    '''
    read data and save it
    '''
    def load_save_doc(self, cdir, fname):
        triggers = []
        events = []
                
        # path for original file
        fpath = self.get_full_path(self.ORIGINAL_DIR,cdir) + '/' + fname
        
        txt = self.get_text(fpath + self.TXT_EXT)        
        proteins = self.get_protein(fpath + self.PROTEIN_EXT)                
        if cdir != 'test':            
            triggers, events = self.get_trigger_relation(fpath + self.TRIGGER_REL_EXT)
        
        
        # path for parsed file
        fpath = self.get_full_path(self.PARSED_DIR,cdir) + '/' + fname
        
        chunks = self.get_chunk(fpath + self.CHUNK_EXT)
        tree = self.get_tree_mcccj(fpath + self.MCCCJ_TREE_EXT)
        dep = self.get_dependency(fpath + self.MCCCJ_SD_EXT)
        
        doc = {"txt":txt,
               "protein":proteins,
               "trigger":triggers,
               "event":events,
               "chunk":chunks,
               "tree":tree,
               "dep":dep}
        
        print txt
        for prot in proteins:
            print prot
        for trig in triggers:
            print trig     
        for e in events:
            print e
        for line in chunks:
            print line   
        for line in tree:
            print line
        for line in dep:
            print line
            
        self.write_to_file(doc, fname)
    
    '''
    write to file
    '''
    def write_to_file(self, doc_to_write, fname):
        with open(self.dest + '/' + fname + '.json', 'w') as fout:
            fout.write(json.dumps(doc_to_write))
            
    
    '''
    return list of file names in cdir directory
    '''
    def get_doc_list(self, cdir, ext_filter):
        return [d.rstrip(ext_filter) for d in os.listdir(self.cdir) if d.endswith(ext_filter)]
            
    '''
    return text from txt file of given fpath
    '''
    def get_text(self, fpath):
        with open(fpath, 'r') as fin:
            txt = fin.read()
        return txt
            
    '''
    return list of protein
    pretein representation:
    ['T84', 'Negative_regulation', '2665', '2673', 'decrease']
    '''
    def get_protein(self, fpath):
        proteins = []
        with open(fpath, 'r') as fin:
            for line in fin:
                line = line.rstrip('\n')
                proteins.append(re.split("\\t|\\s+",line,4))
        return proteins
    
    '''
    return list of trigger and event tuple
    trigger tuple: (id, trigger type, start idx, end idx, trigger text)
    event tuple: (id, event type, trigger_id, theme1 id, theme2 id, cause id)
    '''
    def get_trigger_relation(self, fpath):
        triggers = []
        events = []
        with open(fpath, 'r') as fin:
            for line in fin:
                line = line.rstrip('\n')
                # process trigger
                if line[0] == 'T':
                    triggers.append(re.split("\\t|\\s+",line,4))
                
                # process event
                elif line[0] == 'E':                    
                    evt = re.split("\\t|\\s+",line)
                    eid = evt[0]
                    etype,_,trigid = evt[1].partition(':')
                    theme1 = evt[2].split(':')[1]
                    if len(evt) > 3:
                        argtype,_,argid = evt[3].partition(':')
                        if argtype == 'Theme2':
                            theme2 = argid
                            cause = ""
                        elif argtype == 'Cause':
                            theme2 = ""
                            cause = argid
                        else:
                            theme2 = ""
                            cause = ""
                    events.append((eid, etype, trigid, theme1, theme2, cause))
                    
                    
                    
                    
        return triggers, events
        
    '''
    return chunk data
    '''
    def get_chunk(self, fpath):        
        return self.Chunk.read(fpath)
    
    '''
    return parse tree data
    '''
    def get_tree_mcccj(self, fpath):
        return self.Tree.read(fpath)
    
    '''
    return dependency data
    '''
    def get_dependency(self, fpath):
        return self.Dep.read(fpath)
    
    '''
    cdir: dev, train, or test
    ctype: original or parsed
    '''
    def get_full_path(self, ctype, cdir):
        return self.src + '/' + ctype + '/' + cdir

            
            
    
class DependencyReader:
          
    '''
    return list of dependency by sentence
    ex dependency in a sentence
    {
        root: '2'
        nword: '6'
        data: {'2': [('1)', 'nsubj'), ('6)', 'dobj')], '6': [('3)', 'nn'), ('4)', 'amod'), ('5)', 'nn')]}
    }
    '''
    def read(self, fpath):        
        dep_doc = []
        with open(fpath, 'r') as fin:
            dep_line = defaultdict(list)
            root = []
            non_root = []
            n_word = 0
            for line in fin:
                if line != "\n":
                    par = re.split("\\(|\\,\s",line.rstrip(')\n'))
                    
                    # find gov and add it as candidate of root
                    gov = par[1].rsplit('-',1)[1]
                    root.append(gov)
                    
                    # find dep and add it as non root
                    dep = par[2].rsplit('-',1)[1]
                    non_root.append(dep)
                    
                    # save gov dep representation
                    dep_line[gov].append((dep,par[0]))
                    # update total word number
                    n_word = self.get_nword(n_word, gov, dep)
                    
                    
                else:
                    # add dep to doc
                    if len(dep_line) > 0:                       
                        dep_sentence = {}
                        dep_sentence["data"] = dict(dep_line)
                        dep_sentence["root"] = self.check_root(root, non_root)
                        dep_sentence["nword"] = n_word
                        dep_doc.append(dep_sentence)
                    
                    # reinit temp variable
                    dep_line = defaultdict(list) 
                    root = []
                    non_root = []
                    n_word = 0
                
        return dep_doc
        
    
    '''
    check root and return a root from list
    '''
    def check_root(self, root_list, non_root):
        root = [x for x in root_list if x not in non_root]
        root = list(set(root))
        if len(root) != 1:
            print root
            raise ValueError("root value is not single")
        
        return root[0]
        
    '''
    update number of word in a sentence
    total number of word is the largest dep value
    int current_nword : current total word
    str gov: word number of gov word
    str dep: word number of dep word
    '''
    def get_nword(self, current_nword, gov, dep):
        dep_number = int(dep)
        gov_number = int(gov)
        if gov_number > current_nword:
            current_nword = gov_number
        if dep_number > current_nword:
            current_nword = dep_number
        return dep_number
    
    def test(self, fpath):
        dep_data = self.read(fpath)
        line = 1
        for dep in dep_data:
            print "sentence:",line
            print "nword:", dep["nword"]
            print "root:", dep["root"]
            print dep["data"]
            print
            line += 1
      

class ParseTreeReader:
    
    '''
    return tree representation in a sentence, order by word number
    {
        nword: 6
        data: [['NP', 'NN', 'XXXX'], ['VP', 'VBZ', 'Inhibits'], ['VP', 'NP', 'NN', 'XXXXXXXX'], ..... ]
    }
    '''
    def read(self, fpath):
        tree_data = []
        stack = []
        with open(fpath,'r') as fin:
            for line in fin:
                line_par = line[7:-3].split(' ')
                tree_line = []
                tree_sentence = {}
                nword = 0
                for par in line_par:
                    if par[0] == '(':
                        # push to stack
                        stack.append(par[1:])
                    else:
                        # found a leave of tree (word)
                        npop = par.count(')')
                        word_tree = list(stack)
                        word_tree.append(par.rstrip(')'))
                        for _ in xrange(npop):
                            stack.pop()
                        tree_line.append(word_tree)
                        nword += 1
                
                tree_sentence["nword"] = nword
                tree_sentence["data"] = tree_line
                tree_data.append(tree_sentence)
                
                
        return tree_data

    def test(self, fpath):
        tree_data = self.read(fpath)
        line = 1
        for tree in tree_data:
            print "sentence:",line
            print "nword:", tree["nword"]    
            print tree["data"]
            print
            line += 1


class ChunkReader:
    
    '''
    return chunk data for a document
    chunk data is list of chunk in a sentence
    ex chunk in a sentence
    {
        nword: 6
        nchunk: 3
        data: [{'txt': 'XXXX', 'type': 'NP'}, {'txt': 'Inhibits', 'type': 'VP'}, {'txt': 'XXXXXXXX Mediated iTreg Commitment', 'type': 'NP'}]
    }
    '''
    def read(self, fpath):
        chunk_data = []
        with open(fpath, 'r') as fin:
            for line in fin:
                line_par = line[1:-3].split('] [')
                chunks_line = []
                chunk_sentence = {}
                nword = 0
                for par in line_par:                    
                    chk_type,_,text = par.partition(' ') 
                    chunks_line.append({"type":chk_type, "txt":text})
                    nword += self.get_nword(text)
                chunk_sentence["nword"] = nword
                chunk_sentence["nchunk"] = len(chunks_line)
                chunk_sentence["data"] = chunks_line
                chunk_data.append(chunk_sentence)
        return chunk_data
    
    '''
    return number of word in a chunk text
    words are separated by a space
    '''
    def get_nword(self, chunk_text):
        return chunk_text.count(" ") + 1
    
    def test(self, fpath):
        chunk_data = self.read(fpath)        
        line = 1
        for chunks in chunk_data:
            print "sentence:",line
            print "nword:", chunks["nword"]
            print "nchunk:", chunks["nchunk"]       
            print chunks["data"]
            print
            line += 1


if __name__ == "__main__":
    
    source = "E:/corpus/bionlp2011"
    dest = "E:/Project/bionlp-genia-ee/data"
    doc_id = "PMC-2222968-04-Results-03"
    
    Reader = GeniaReader(source,dest)
    Reader.load_doc("dev", doc_id)
    
    # testing
    dependency = False
    parse_tree = False
    chunk = False
    
    if dependency:
        dep_fpath = "E:/corpus/bionlp2011/parse/dev/" + doc_id + ".txt.ss.mcccjtok.mcccj.basic.sd"
        Dep = DependencyReader()
        Dep.test(dep_fpath)
    
    if parse_tree:
        tree_fpath = "E:/corpus/bionlp2011/parse/dev/" + doc_id + ".txt.ss.mcccjtok.mcccj"
        Tree = ParseTreeReader()
        Tree.test(tree_fpath)
    
    if chunk:
        chunk_fpath = "E:/corpus/bionlp2011/parse/dev/" + doc_id + ".chk"
        Chunk = ChunkReader()
        Chunk.test(chunk_fpath) 
    
    
    
    
    
        