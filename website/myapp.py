from flask import Flask
from flask import render_template

app = Flask(__name__)


@app.route('/')
def index():
    print('Index is being executed')
    return render_template('home.html')

@app.route('/content')
def content():
    return render_template('content.html')

@app.route('/regexp')
def regexp():
    return render_template('lesson.html')

@app.route('/about')
def about():
    persons = {'Ксения Шерман': 'ksenia.shermanv@gmail.com',
               'Мария Островская': 'ostrovskaya.ms@mail.ru',
               'Элина Камаева': 'elinkamaeva@gmail.com'}
    return render_template('about.html', persons=persons)

if __name__ == '__main__':
    app.run(debug=True)
