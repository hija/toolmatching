import operator
import os
import json

from flask import Flask, jsonify, session, request, render_template
from io import open

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
        with open(os.path.join(app.instance_path, category['data']), encoding='utf-8') as data:
            category_data_dict[category['endpoint']] = json.load(data)

    print(category_data_dict)

    with open(os.path.join(app.instance_path, 'tools.json')) as data:
        tool_data = json.load(data)['Tools']

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
        data = category_data_dict[category]["Questions"][questionid]
        if data['type'] == 'yes-no':
            return render_template('YesNo.html', question=data['question'], questionid=data['id'])
        elif data['type'] == 'single-choice':
            return render_template('SingleChoice.html', question=data['question'],
                                   choices=data['choices'], questionid=data['id'])
        elif data['type'] == 'multiple-choice':
            return render_template('MultipleChoice.html', question=data['question'],
                                   choices=data['choices'], questionid=data['id'])
        elif data['type'] == 'number':
            return render_template('Slide.html', question=data['question'],
                                   min=data['min'], max=data['max'], default=data['default'], questionid=data['id'])

    def calculate_tool_result():
        tool_points = dict()
        category_data = category_data_dict[session['category']]

        tool_points = dict()
        for tool in category_data["Tools"]:
            tool_points[tool['name']] = 0
            for attribute in tool:
                if attribute in session['answers']:
                    tool_values = tool[attribute]
                    users_values = session['answers'][attribute]

                    if tool_values is list and users_values is list:
                        if bool(set(tool_values) & set(users_values)):
                            tool_points[tool['name']] += len(set(tool_values) & set(users_values))
                    elif isinstance(tool_values, str) and isinstance(users_values, str):
                        if tool_values == users_values:
                            tool_points[tool['name']] += 1
                    elif isinstance(tool_values, bool) and isinstance(users_values, bool):
                        if tool_values == users_values:
                            tool_points[tool['name']] += 1
                    elif isinstance(tool_values, int) and isinstance(users_values, int):
                        # Get if higher or lower is accepted
                        entry = [x for x in category_data['Questions'] if x['id'] == attribute][0]
                        if entry['better'] == 'lower' and tool_values <= users_values:
                            tool_points[tool['name']] += 1
                        elif entry['better'] == 'higher' and tool_values >= users_values:
                            tool_points[tool['name']] += 1
                    else:
                        print('ATTRIBUTE', attribute, 'TOOL:', type(tool_values), 'USER', type(users_values))

        sorted_tool_points = dict(sorted(tool_points.items(), key=operator.itemgetter(1), reverse=True))
        first_three_winners = list(sorted_tool_points.keys())[0:3]

        icons = list(map(lambda x: [d['icon'] for d in tool_data if d['name'] == x][0], first_three_winners))

        return render_template('Results.html', first_name=first_three_winners[0], first_image=icons[0],
                               second_name=first_three_winners[1], second_image=icons[1],
                               third_name=first_three_winners[2], third_image=icons[2])

    @app.route('/')
    def show_categories():
        return render_template('categories.html')

    @app.route('/questionnaire', methods=['POST'])
    def process_questionnaire():
        ## Check if questionnaire catergory exists --> Otherwise return error
        if request.values.get('category'):
            # This is just once called at the beginning --> We reset the session
            session.clear()

            category = request.values.get('category')
            if not(category in category_data_dict):
                return jsonify(
                    {'error': 'Unknown category. Please restart. In the worst case, please choose another category.'})

            # Initialize Data
            session['category'] = category
            session['question'] = 0
            session['answers'] = dict()

            return get_question(session['category'], session['question'])

        elif request.values.get('id') and request.values.get('response'):
            ### RESPONSE TO A QUESTION

            # response
            response = request.values.get('response')
            if response == 'true':
                response = True
            elif response == 'false':
                response = False
            elif response.isdigit():
                response = int(response)
            elif ';' in response:
                response = response.split(';')

            session['answers'][request.values.get('id')] = response
            session['question'] += 1  # Increase current questionnumber

            # Check if we are at the end...
            if len(category_data_dict[session['category']]["Questions"]) <= session['question']:
                return calculate_tool_result()
            else:
                return get_question(session['category'], session['question'])
        else:
            ### INVALID REQUEST
            return jsonify({'error': 'Invalid request'})

    return app
