from flask import Flask, render_template, request, redirect, url_for, send_file, flash, jsonify
import sqlite3
from io import BytesIO
import fitz  # PyMuPDF

app = Flask(__name__)
app.secret_key = 'supersecretkey'

def connect_db():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/autocomplete', methods=['GET'])
def autocomplete():
    query = request.args.get('query', '')
    suggestions = []

    if query:
        conn = connect_db()
        cur = conn.cursor()

        # Hier werden die unterschiedlichen Gerichte abgefragt
        cur.execute("SELECT DISTINCT meal1 FROM meals WHERE meal1 LIKE ?", ('%' + query + '%',))
        suggestions += [row['meal1'] for row in cur.fetchall()]

        cur.execute("SELECT DISTINCT meal2 FROM meals WHERE meal2 LIKE ?", ('%' + query + '%',))
        suggestions += [row['meal2'] for row in cur.fetchall()]

        cur.execute("SELECT DISTINCT salad FROM meals WHERE salad LIKE ?", ('%' + query + '%',))
        suggestions += [row['salad'] for row in cur.fetchall()]

        cur.execute("SELECT DISTINCT dessert FROM meals WHERE dessert LIKE ?", ('%' + query + '%',))
        suggestions += [row['dessert'] for row in cur.fetchall()]

        conn.close()

    return jsonify(list(set(suggestions)))  # set() entfernt Duplikate

@app.route('/')
def index():
    conn = connect_db()
    cursor = conn.execute('SELECT id, day, date, meal1, meal2, salad, dessert FROM meals')
    meals = cursor.fetchall()
    conn.close()
    return render_template('index.html', meals=meals)

@app.route('/add', methods=['POST'])
def add():
    day = request.form['day']
    date = request.form['date']
    meal1 = request.form['meal1']
    meal2 = request.form['meal2']
    salad = request.form['salad']
    dessert = request.form['dessert']

    conn = connect_db()
    conn.execute('INSERT INTO meals (day, date, meal1, meal2, salad, dessert) VALUES (?, ?, ?, ?, ?, ?)',
                 (day, date, meal1, meal2, salad, dessert))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):
    conn = connect_db()
    if request.method == 'POST':
        day = request.form['day']
        date = request.form['date']
        meal1 = request.form['meal1']
        meal2 = request.form['meal2']
        salad = request.form['salad']
        dessert = request.form['dessert']

        conn.execute('UPDATE meals SET day = ?, date = ?, meal1 = ?, meal2 = ?, salad = ?, dessert = ? WHERE id = ?',
                     (day, date, meal1, meal2, salad, dessert, id))
        conn.commit()
        conn.close()
        return redirect(url_for('index'))

    cursor = conn.execute('SELECT id, day, date, meal1, meal2, salad, dessert FROM meals WHERE id = ?', (id,))
    meal = cursor.fetchone()
    conn.close()
    return render_template('edit.html', meal=meal)

@app.route('/delete/<int:id>', methods=['GET'])
def delete(id):
    conn = connect_db()
    conn.execute('DELETE FROM meals WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/export', methods=['GET', 'POST'])
def export():
    if request.method == 'POST':
        selected_ids = request.form.getlist('meal_id')
        vegetarian_day = request.form['vegetarian_day']

        if len(selected_ids) > 5:
            flash('Sie können maximal fünf Wochentage auswählen.')
            return redirect(url_for('export'))

        conn = connect_db()
        cursor = conn.execute(f'SELECT day, date, meal1, meal2, salad, dessert FROM meals WHERE id IN ({",".join(["?"] * len(selected_ids))})', selected_ids)
        selected_meals = cursor.fetchall()
        conn.close()

        # Check for duplicate days
        days = [meal['day'] for meal in selected_meals]
        if len(days) != len(set(days)):
            flash('Jeder Wochentag darf nur einmal ausgewählt werden.')
            return redirect(url_for('export'))

        template_path = 'Vorlage_mitVeggieLogo3.pdf'
        image_path = 'vegetarian.png'  # Pfad zum Bild
        pdf_document = fitz.open(template_path)
        page = pdf_document.load_page(0)

        # Positionen für die einzelnen Tage (Datum und Gerichte)
        positions = {
            'Montag': {
                'date': (300, 110),
                'meal1': (30, 137),
                'meal2': (30, 212),
                'salad': (702, 157),
                'dessert': (702, 235),
                'image': (552, 77)  # Position für das Bild (x, y)
            },
            'Dienstag': {
                'date': (300, 285),
                'meal1': (30, 316),
                'meal2': (30, 391),
                'salad': (702, 335),
                'dessert': (702, 410),
                'image': (552, 255)  # Position für das Bild (x, y)
            },
            'Mittwoch': {
                'date': (300, 466),
                'meal1': (30, 500),
                'meal2': (30, 575),
                'salad': (702, 517),
                'dessert': (702, 595),
                'image': (552, 440)  # Position für das Bild (x, y)
            },
            'Donnerstag': {
                'date': (300, 648),
                'meal1': (30, 680),
                'meal2': (30, 756),
                'salad': (702, 699),
                'dessert': (702, 777),
                'image': (552, 620)  # Position für das Bild (x, y)
            },
            'Freitag': {
                'date': (300, 837),
                'meal1': (30, 871),
                'meal2': (30, 944),
                'salad': (702, 887),
                'dessert': (702, 965),
                'image': (552, 815)  # Position für das Bild (x, y)
            }
        }

        for meal in selected_meals:
            day, date, meal1, meal2, salad, dessert = meal
            pos = positions[day]

            formatted_meal1 = format_text(meal1, 60)
            formatted_meal2 = format_text(meal2, 60)
            formatted_salad = format_text(salad, 15)
            formatted_dessert = format_text(dessert, 15)

            page.insert_text(pos['date'], date, fontsize=18)
            page.insert_text(pos['meal1'], formatted_meal1, fontsize=18)
            page.insert_text(pos['meal2'], formatted_meal2, fontsize=18)
            page.insert_text(pos['salad'], formatted_salad, fontsize=18)
            page.insert_text(pos['dessert'], formatted_dessert, fontsize=18)

            if day == vegetarian_day:
                image_rect = fitz.Rect(pos['image'][0], pos['image'][1], pos['image'][0] + 147, pos['image'][1] + 147)
                page.insert_image(image_rect, filename=image_path)

        buffer = BytesIO()
        pdf_document.save(buffer)
        buffer.seek(0)
        pdf_document.close()

        return send_file(buffer, as_attachment=True, download_name='speiseplan.pdf', mimetype='application/pdf')

    conn = connect_db()
    cursor = conn.execute('SELECT id, day, date, meal1, meal2, salad, dessert FROM meals')
    meals = cursor.fetchall()
    conn.close()
    return render_template('export.html', meals=meals)

def format_text(text, line_length):
    words = text.split()
    formatted_text = ""
    current_line = ""

    for word in words:
        if len(current_line) + len(word) + 1 > line_length:
            if len(word) > line_length:
                part1 = word[:line_length-len(current_line)-1] + "-"
                part2 = word[line_length-len(current_line)-1:]
                current_line += part1
                formatted_text += current_line + "\n"
                current_line = part2
            else:
                formatted_text += current_line.strip() + "\n"
                current_line = word + " "
        else:
            current_line += word + " "

    formatted_text += current_line.strip()
    return formatted_text

if __name__ == '__main__':
    app.run(debug=True)
