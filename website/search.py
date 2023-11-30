import os
from ix_classes import MyTokenizer, MyFilter
from whoosh.qparser import QueryParser, OrGroup
from whoosh.index import create_in
from whoosh.fields import *
from whoosh import highlight
from bs4 import BeautifulSoup, Comment, NavigableString, Doctype
import re
from string import punctuation

# from whoosh import scoring

class MySearcher():

    def __init__(self, directory='indexdir', use_fragmenter=False):
        self.directory = directory

        if not os.path.exists(directory):
            os.mkdir(directory)

        self.analyzer = MyTokenizer() | MyFilter(use_stopwords=True)
        self.analyzer_highlight = MyTokenizer() | MyFilter(use_stopwords=False)

        self.schema = Schema(
            title=TEXT(stored=True, analyzer=self.analyzer),
            path=ID(stored=True), 
            content=TEXT(stored=True, analyzer=self.analyzer, spelling=True),
        )

        self.ix = create_in("indexdir", self.schema)
        self.qu = QueryParser("content", self.ix.schema,  group=OrGroup)
        self.use_fragmenter = use_fragmenter
        self.fragmenter = highlight.ContextFragmenter(maxchars=300, surround=100)

    def extract_text_from_html(self, filepath):
        with open(filepath, 'r', encoding='utf-8') as file:
            soup = BeautifulSoup(file, 'html.parser')

            strings = []
            for element in soup.find_all(text=True):
                # Игнорируем шаблонные теги Jinja2
                if re.match(r'\{%.*?%\}', element) or re.match(r'\{\{.*?\}\}', element):
                    continue
                
                # Получаем родительские классы элемента
                parent_classes = element.parent.get('class', [])
                
                # Пропускаем определенные элементы, элементы внутри блоков кода, шаблонные теги Jinja2 и специфичные div
                if (element.parent.name in ['script', 'style', 'title'] or
                    isinstance(element, (Comment, Doctype)) or
                    'anchor-link' in parent_classes or
                    'jp-CodeCell' in parent_classes):
                    continue
                
                if (element.parent.name != 'h1' or 'anchor-link' in parent_classes):
                    if isinstance(element, NavigableString):
                        original_text = element.string
                        strings.append(original_text.strip())

            text = ' '.join(strings)
            # Замена множественных переносов строк на один перенос строки
            text = re.sub(r'\n+', '\n', text)
            # Замена множественных пробелов на один пробел
            text = re.sub(r' +', ' ', text)
            return text
        
    def create_index(self, filepath = './templates/lessons'):
        '''
        Creates index direcotry amd writes documents into it
        '''
        writer = self.ix.writer()
        for address, _, files in os.walk(filepath):
            for name in files:
                if name.endswith('.html'):  # проверка, является ли файл HTML-файлом
                    full_path = os.path.join(address, name)  # Полный путь к файлу
                    text = self.extract_text_from_html(full_path)
                    writer.add_document(
                        title=name,
                        path=full_path,
                        content=text
                    )
        writer.commit()

    def search(self, query):
        # from whoosh import index
        # wix = index.open_dir(settings.WHOOSH_INDEX_DIR)
        with self.ix.searcher() as searcher:
            # corrector = searcher.corrector('content')
            search_query = self.qu.parse(query)
            corrected = searcher.correct_query(search_query, query)
            print('compare', corrected.query, search_query)
            if corrected.query != search_query:
                print("Возможно вы ищете:", corrected.string)
            results = searcher.search(search_query).copy()
            return_results = []

            if not results.is_empty():
                results.fragmenter = self.fragmenter
                results.fragmenter.surround = 50

                for hit in results:
                    text = hit.highlights('content') if self.use_fragmenter else hit['content']
                    return_results.append({
                        'title': hit['title'],
                        'path': hit['path'],
                        'text': text
                    })

                return return_results
            return None
        
    def highlight_fragment(self, fragment, query):
        fragment = re.sub(r'(\<b class=\"match term\d+?\"\>|\<\/b\>)', '', fragment)
        query_tokens = [token.text for token in self.analyzer_highlight(query)]
        fragment_orig_tokens = fragment.split()
        

        all_fragments = []
        for i, token in enumerate(fragment_orig_tokens):
            token = token.strip(punctuation)
            clean_token = [t.text for t in self.analyzer_highlight(token)]

            if (len(clean_token) > 0) and (clean_token[0] in query_tokens):
                if (len(all_fragments) > 0) and (fragment_orig_tokens[i] in all_fragments[-1]):
                    fragment_orig_tokens[i] = '<b>' + fragment_orig_tokens[i] + '</b>'
                    all_fragments.insert(0, ' '.join(fragment_orig_tokens[max(0, i-10):min(len(fragment_orig_tokens), i+10)]))
                    all_fragments.pop(-1)
                else:
                    fragment_orig_tokens[i] = '<b>' + fragment_orig_tokens[i] + '</b>'
                    all_fragments.append(' '.join(fragment_orig_tokens[max(0, i-10):min(len(fragment_orig_tokens), i+10)]))
        
        return all_fragments
