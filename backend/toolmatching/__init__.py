import os
import json

from flask import Flask, jsonify, session, request


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        QUESTIONNAIRE_CATEGORIES=os.path.join(app.instance_path, 'categories.json')
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # load questionnaire data
    with open(app.config['QUESTIONNAIRE_CATEGORIES']) as questionnaire_categories_file:
        questionnaire_categories_data = json.load(questionnaire_categories_file)

    category_data_dict = dict()
    for category in questionnaire_categories_data['categories']:
        with open(os.path.join(app.instance_path, category['data'])) as data:
            category_data_dict[category['name']] = json.load(data)

    # a simple page that says hello
    @app.route('/hello')
    def hello():
        return 'Hello, World!'

    @app.route('/categories')
    def get_categories():
        categories_data = {}
        for category_data in questionnaire_categories_data['categories']:
            categories_data[category_data['name']] = {'endpoint': 'questionnaire/' + category_data['endpoint']}
        return jsonify(categories_data)

    def get_question(category, questionid):
        return

    @app.route('/questionnaire', methods=['POST'])
    def process_questionnaire():
        ## Check if questionnaire catergory exists --> Otherwise return error
        if request.values.get('category'):
            # This is just once called at the beginning --> We reset the session
            session.clear()
            category = request.values.get('category')
            if not(any(category_data['endpoint'] == category for category_data in questionnaire_categories_data['categories'])):
                return jsonify({'error': 'Unknown category. Please restart. In the worst case, please choose another category.'})
            session['category'] = request.value.get('category')
            session['question'] = 0
        elif request.values.get('id') and request.values.get('response'):
            return jsonify({'text': 'SAVING'})
            session['question'] += 1 # Increase current questionnumber
        else:
            return jsonify({'error': 'Invalid request'})
    return app