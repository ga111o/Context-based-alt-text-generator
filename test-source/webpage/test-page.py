from flask import Flask, render_template, jsonify

app = Flask(__name__)

@app.route('/')
def show_image():
    return render_template("./index.html")

@app.route('/output')
def output_json():
    with open('./output.json', 'r', encoding='utf-8') as file:
        data = file.read()

    from flask import Response
    return Response(data, mimetype='application/json')

if __name__ == '__main__':
    app.run(debug=True, port=8123)
