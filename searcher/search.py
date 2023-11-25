import os
from ix_classes import MyTokenizer, MyFilter
from whoosh.qparser import QueryParser, OrGroup
from whoosh.index import create_in
from whoosh.fields import *
from whoosh import highlight

# from whoosh import scoring

class MySearcher():

    def __init__(self, directory='indexdir', use_fragmenter=False):
        self.directory = directory

        if not os.path.exists(directory):
            os.mkdir(directory)

        self.analyzer = MyTokenizer() | MyFilter()

        self.schema = Schema(
            title=TEXT(stored=True, analyzer=self.analyzer),
            path=ID(stored=True), 
            content=TEXT(analyzer=self.analyzer, spelling=True),
        )

        self.ix = create_in("indexdir", self.schema)
        self.qu = QueryParser("content", self.ix.schema,  group=OrGroup)
        self.use_fragmenter = use_fragmenter
        self.fragmenter = highlight.SentenceFragmenter(sentencechars='.!?')

    def create_index(self, filepath = './texts'):
        '''
        Creates index direcotry amd writes documents into it
        '''

        writer = self.ix.writer()
        for address, _, files in os.walk(filepath):
            for name in files:
                path = os.path.join(address, name)
                with open(path, 'r', encoding='utf-8') as f:
                    text = f.read()
                    writer.add_document(
                        title = name, 
                        path = path,
                        content = text
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
                if self.use_fragmenter:
                    results.fragmenter = self.fragmenter
                    results.fragmenter.surround = 50

                    for hit in results:
                        title, path = hit['title'], hit['path']

                        with open(hit['path']) as f:
                            text = f.read()
                        
                        text = hit.highlights('content', text)
                        return_results.append({
                            'title': title,
                            'path': path,
                            'text': text
                        })

                else:
                    for hit in results:
                        title, path = hit['title'], hit['path']
                    
                        return_results.append({
                                'title': title,
                                'path': path,
                                'text': None
                            })

                return return_results
            return None