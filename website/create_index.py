from search import MySearcher

if __name__ == "__main__":
    searcher = MySearcher(directory='indexdir')
    searcher.create_index(filepath='./templates/lessons')
    print("Индекс успешно создан.")
