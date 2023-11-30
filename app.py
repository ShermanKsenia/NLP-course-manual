from flask import Flask, request, url_for, render_template, session, jsonify, redirect, flash
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import json
from urllib.parse import quote_plus
from search import MySearcher
import os
import random

app = Flask(__name__)
searcher = MySearcher(directory='indexdir')
searcher.create_index(filepath='./templates/lessons')

app.secret_key = 'your_secret_key_here'

# Загрузка данных об уроках из JSON-файла
with open('lessons.json') as json_file:
    lessons = json.load(json_file)

# Загрузка данных терминов с их определениями из JSON-файла
with open('terms.json') as json_file:
    terms = json.load(json_file)

def load_exercises(filename):
    """ Загружает задания из JSON-файла. """
    with open(filename, 'r', encoding='utf-8') as file:
        return json.load(file)

def get_exercises_for_lesson(lesson_key, exercise_ids):
    """ Возвращает задания для конкретного урока на основе списка идентификаторов. """
    if exercise_ids:
        exercises = load_exercises('answers.json')
        return [exercise for exercise in exercises if exercise['id'] in exercise_ids]
    return None

# Функция для URL-кодирования
def url_encode(s):
    return quote_plus(s, encoding='utf-8')

# Добавление пользовательского фильтра в Flask
app.jinja_env.filters['url_encode'] = url_encode

# Функция для перемешивания списков в шаблоне Flask
def shuffle_filter(s):
    random.shuffle(s)
    return s

app.jinja_env.filters['shuffle'] = shuffle_filter

def get_db_connection():
    conn = sqlite3.connect('users.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    print('Index is being executed')
    return render_template('home.html')

@app.route('/search_results')
def search_results():
    query = request.args.get('query', '')
    results = searcher.search(query)
    print(results)
    if results is None:
        results = []
    enriched_results = []
    for result in results:
        lesson_key = next((key for key, value in lessons.items() if value['content'] == result['title']), None)
        lesson_title = lessons[lesson_key]['title'] if lesson_key else "Неизвестный урок"
        #preview_text = result['text'][:200] + "..."
        preview_texts = searcher.highlight_fragment(result['text'], query)
        lesson_url = url_for('show_lesson', lesson_key=lesson_key) if lesson_key else "#"
        
        enriched_results.append({
            'title': lesson_title,
            'preview_texts': preview_texts,
            'url': lesson_url
        })
    
    return render_template('search_results.html', results=enriched_results)

@app.route('/register', methods=['POST'])
def register():
    username = request.form['newUsername']
    password = request.form['newPassword']
    hashed_password = generate_password_hash(password)

    conn = get_db_connection()
    cursor = conn.cursor()
    # Попытка добавления нового пользователя
    try:
        cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, hashed_password))
        conn.commit()
        registration_success = True
    except sqlite3.IntegrityError:
        # Если пользователь с таким именем уже существует
        registration_success = False
    
    conn.close()

    if registration_success:
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'error': 'Пользователь с таким именем уже существует'})

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']

    conn = get_db_connection()
    cursor = conn.cursor()
    user = cursor.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
    conn.close()

    if user and check_password_hash(user['password'], password):
        session['username'] = user['username']
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'error': 'Неверные данные для входа'})

@app.route('/logout', methods=['POST'])
def logout():
    session.pop('username', None)
    return jsonify({'success': True})

@app.route('/content')
def content():
    return render_template('content.html')

@app.route('/check_answer', methods=['POST'])
def check_answer():
    data = request.get_json()
    app.logger.debug('Received data: %s', data)
    if not data:
        return jsonify({'message': 'Нет данных.'}), 400

    exercise_id = data.get('exercise_id')
    user_answer = data.get('user_answer')

    if not exercise_id or user_answer is None:
        return jsonify({'message': 'Недостаточно данных.'}), 400

    # Преобразование exercise_id в int
    exercise_id = int(exercise_id)
    
    exercises = load_exercises('answers.json')
    exercise = next((ex for ex in exercises if ex['id'] == exercise_id), None)

    if exercise is None:
        return jsonify({'message': 'Задание не найдено.'}), 404

    correct_answer = exercise['correct_answer']

    if exercise['type'] == 'comma_list':
        user_answer = [int(el.strip()) for el in user_answer.split(',')]
    elif exercise['type'] == 'space_list':
        user_answer = [int(el.strip()) for el in list(user_answer)]
    elif exercise['type'] == 'string_list':
        user_answer = [el.strip().lower() for el in user_answer.split(',')]

    #if str(user_answer).strip() == str(correct_answer).strip():
    if user_answer == correct_answer:
        return jsonify({'message': 'Правильно!'})
    else:
        return jsonify({'message': 'Неправильно. Попробуйте еще раз.'})

@app.route('/check_answers_list', methods=['POST'])
def check_answers_list():
    data = request.get_json()
    app.logger.debug('Received data: %s', data)
    if not data:
        return jsonify({'message': 'Нет данных.'}), 400

    exercise_id = data.get('exercise_id')
    user_answers = data.get('user_answers')

    if not exercise_id or not user_answers:
        return jsonify({'message': 'Недостаточно данных.'}), 400

    exercise_id = int(exercise_id)
    exercises = load_exercises('answers.json')
    exercise = next((ex for ex in exercises if ex['id'] == exercise_id), None)

    if exercise is None:
        return jsonify({'message': 'Задание не найдено.'}), 404

    correct_answer = exercise['correct_answer']
    correct_count = sum(1 for key, value in user_answers.items() if value.lower() == correct_answer[key[-1]]['answer'].lower())

    message = f'Вы правильно ответили на {correct_count} из {len(correct_answer)} вопросов.'

    return jsonify({'message': message})

@app.route('/check_matching_answers', methods=['POST'])
def check_matching_answers():
    data = request.get_json()
    user_answers = data.get('answers')
    exercise_id = int(data.get('exercise_id'))
    app.logger.debug('Received data: %s', data)
    
    exercises = load_exercises('answers.json')
    exercise = next((ex for ex in exercises if ex['id'] == exercise_id), None)
    if not exercise:
        return jsonify({'message': 'Упражнение не найдено.'}), 404

    correct_answers = exercise['correct_answer']
    print(correct_answers)

    correct_count = 0
    for user_answer in user_answers:
        left_id = str(user_answer['leftId'])
        user_answer_value = user_answer['answer']

        # Проверяем, соответствует ли ответ пользователя правильному ответу
        if correct_answers.get(left_id) and correct_answers[left_id]['answer'] == user_answer_value:
            correct_count += 1

    # Формируем сообщение с результатами
    total_questions = len(correct_answers)
    message = f'Вы правильно ответили на {correct_count} из {total_questions} вопросов.'
    
    return jsonify({'message': message})

@app.route('/<lesson_key>')
def show_lesson(lesson_key):
    lesson = lessons.get(lesson_key)
    if lesson:
        lesson_content = os.path.join('lessons', lesson['content'])
        exercises = get_exercises_for_lesson(lesson_key, lesson['exercises'])
        print(exercises)
        return render_template('lesson.html', lesson_title=lesson['title'], 
                               lesson_content=lesson_content,
                               notebook_link=lesson['notebook_link'], exercises=exercises)
    else:
        return 'Урок не найден', 404

@app.route('/about')
def about():
    persons = {'Ксения Шерман': 'ksenia.shermanv@gmail.com',
               'Мария Островская': 'ostrovskaya.ms@mail.ru',
               'Элина Камаева': 'elinkamaeva@gmail.com'}
    return render_template('about.html', persons=persons)

@app.route('/terms')
def terms_list():
    return render_template('terms.html', terms=terms)

if __name__ == '__main__':
    app.run(debug=True)
