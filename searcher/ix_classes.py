from string import punctuation
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
            word = word.strip(punctuation)
            if word.isalpha():
                t.text = word
                if keeporiginal:
                    t.original = word
                if positions:
                    t.pos = start_pos + pos
                if chars:
                    t.startchar = start_char
                    t.endchar = start_char + len(word)
                yield t
            start_char += word_len + 1
    

class MyFilter(Filter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.morph = MorphAnalyzer()
        self.stopwords = stopwords.words('russian')

    def __call__(self, tokens):
        for token in tokens:
            token.text = self.morph.parse(token.text.strip())[0].normal_form
            if token.text not in self.stopwords:
                yield token