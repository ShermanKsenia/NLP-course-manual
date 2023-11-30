import re
from pymorphy2 import MorphAnalyzer
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from whoosh.analysis import Filter, Tokenizer, Token
from whoosh.fields import *

class MyTokenizer(Tokenizer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tokenizer = word_tokenize

    def __call__(self, value, positions = False, chars = False,
                 keeporiginal = False, removestops = True,
                 start_pos = 0, start_char = 0, mode='',
                 **kwargs):
        
        t = Token(positions, chars, removestops = removestops, mode=mode)
        for pos, word in enumerate(self.tokenizer(value)):
            word_len = len(word)
            if word.isalpha() or re.match(r'\w+?-\w+?\b', word):
                t.text = word.lower()
                if keeporiginal:
                    t.original = word
                if positions:
                    t.pos = start_pos + pos
                if True:
                    t.startchar = start_char
                    t.endchar = start_char + word_len
                    start_char = t.endchar + 1
                yield t
            else:
                if word_len > 1:
                    start_char += word_len + 1
                else:
                    start_char += 1
            

class MyFilter(Filter):
    def __init__(self, *args, use_stopwords=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.morph = MorphAnalyzer()
        self.stopwords = stopwords.words('russian')
        self.use_stopwords = use_stopwords

    def __call__(self, tokens):
        for token in tokens:
            token.text = self.morph.parse(token.text.strip())[0].normal_form
            if self.use_stopwords:
                if token.text not in self.stopwords:
                    yield token
            else:
                yield token