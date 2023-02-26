import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import setup_db, Question, Category
from flask_cors import CORS
import json
from statistics import mode

QUESTIONS_PER_PAGE = 10

def paginate_questions(request, selection):
    page = request.args.get("page", 1, type=int)
    start = (page - 1) * QUESTIONS_PER_PAGE
    end = start + QUESTIONS_PER_PAGE

    questions = [question.format() for question in selection]
    current_questions = questions[start:end]

    return current_questions

def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    db = setup_db(app)

    CORS(app, resources={r"/api/*": {"origins": "*"}})

    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET, POST, PATCH, DELETE, OPTIONS')
        return response
    
    @app.route('/categories')
    def retrieve_categories():
        categories = Category.query.all() 
        if len(categories) == 0: 
            abort(404)       
        formatted_categories = { category.id:category.type for category in categories }       
        return jsonify({ 'success': True, 'categories': formatted_categories })
    
    @app.route('/questions')
    def retrieve_questions():
        questions = Question.query.all() 
        categories = Category.query.all()

        totalQuestions = len(questions)

        if totalQuestions == 0 or len(categories) == 0: 
            abort(404)       

        paginated_questions = paginate_questions(request, questions) 

        if len(paginated_questions) == 0:
            abort(422)

        formatted_categories = { category.id:category.type for category in categories }
        currentCategory = formatted_categories[paginated_questions[0]['category']]
        return jsonify({ 'success': True, 'questions': paginated_questions, 'total_questions': totalQuestions, 'categories': formatted_categories, 'current_category' : currentCategory })

    @app.route('/questions/<int:question_id>', methods=['DELETE'])
    def delete_question(question_id):        
        try:
            question = Question.query.filter(Question.id == question_id).one_or_none()            
            
            if question is None:
              abort(404)

            question.delete()
            selection = Question.query.order_by(Question.id).all()
            current_questions = paginate_questions(request, selection)

            return jsonify(
                {
                    "success": True,
                    "deleted": question_id,
                    "questions": current_questions,
                    "total_questions": len(Question.query.all()),
                })

        except:
            abort(422)        

    @app.route('/questions', methods=['POST'])
    def create_question():
        body = request.get_json()

        if 'searchTerm' in body:
            try:
                search_term = body.get('searchTerm')
                filtered_questions = Question.query.filter(Question.question.ilike('%' + search_term + '%')).all()
                categories = Category.query.all()
                paginated_questions = paginate_questions(request, filtered_questions) 
                totalQuestions = len(Question.query.all())

                if len(paginated_questions) == 0:
                    abort(422)

                formatted_categories = { category.id:category.type for category in categories }
                currentCategory = formatted_categories[paginated_questions[0]['category']]
                return jsonify({ 'success': True, 'questions': paginated_questions, 'total_questions': totalQuestions, 'current_category' : currentCategory })
            except:
                abort(422)
        else:            
            try:
                new_question = body.get('question', None)
                new_answer = body.get('answer', None)
                new_category = body.get('category', 1)
                new_difficulty = body.get('difficulty', 1)

                question = Question(question=new_question, answer=new_answer, category=new_category, difficulty=new_difficulty)
                question.insert()

                selection = Question.query.order_by(Question.id).all()
                current_questions = paginate_questions(request, selection)

                return jsonify(
                    {
                        "success": True,
                        "created": question.id,
                        "questions": current_questions,
                        "total_questions": len(Question.query.all())
                    }
                )

            except:
                abort(422)       

    @app.route('/categories/<int:category_id>/questions')
    def filter_questions_by_category(category_id):

        filtered_questions = []
        currentCategory = ''

        for question, category in db.session.query(Question, Category).filter(Question.category == Category.id).filter(Category.id == category_id).all():
            filtered_questions.append(question)
            currentCategory = category.type

        if len(filtered_questions) == 0:
             abort(404)
        
        totalQuestions = len(Question.query.all())

        paginated_questions = paginate_questions(request, filtered_questions) 
        
        if len(paginated_questions) == 0:
            abort(422)      

        return jsonify({ 'success': True, 'questions': paginated_questions, 'total_questions': totalQuestions, 'current_category' : currentCategory })
    
    @app.route('/quizzes', methods=['POST'])
    def quiz():
            body = request.get_json()
            previous_questions = body.get('previous_questions')
            quiz_category = body.get('quiz_category')
            category_id = quiz_category['id']

            category_ids = []
            for id in db.session.query(Category.id).distinct().all():
                category_ids.append(id)

            question_ids = []
            for id in db.session.query(Question.id).distinct():
                question_ids.append(id)

            filtered_question = {}

            # ALL
            if category_id == 0:
                if len(previous_questions) == 0:
                    question_id = random.choice(question_ids)                    
                else:
                    question_id = list(set(question_ids) - set(previous_questions)).pop()

                filtered_question = Question.query.filter(Question.id == question_id).one_or_none() 
                return jsonify({ 'success': True, 'question': filtered_question.format()  })

            filtered_category = Category.query.filter(Category.id == category_id).one_or_none()
            if filtered_category is None:
                abort(400)
            else:
                if len(previous_questions) == 0:
                    questions = Question.query.filter(Question.category == category_id).all()
                    question_id = random.choice([question.id for question in questions])
                    
                else:
                    questions = list(set(question_ids) - set(previous_questions))
                    filtered_questions = Question.query.filter(Question.id == category_id).filter(Question.id in questions)
                    question_id = random.choice([question.id for question in filtered_questions])

                filtered_question = Question.query.filter(Question.id == question_id).first()
                return jsonify({ 'success': True, 'question': filtered_question.format()  })

    # ERROR HANDLING
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({ "success": False,  "error": 400, "message": "bad request" }), 400

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({ "success": False,  "error": 404,  "message": "not found" }), 404

    @app.errorhandler(405)
    def method_not_allowed(error):
        return jsonify({ "success": False, "error": 405, "message": "method not allowed" }), 405

    @app.errorhandler(422)
    def unprocessable(error):
        return jsonify({ "success": False, "error": 422, "message": "unprocessable" }), 422

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({ "success": False, "error": 500, "message": "internal server error" }), 500

    return app

