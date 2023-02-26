import os
import unittest
import json
from flask_sqlalchemy import SQLAlchemy

from flaskr import create_app
from models import setup_db, Question, Category

class TriviaTestCase(unittest.TestCase):
    """This class represents the trivia test case"""

    def setUp(self):
        """Define test variables and initialize app."""
        self.app = create_app()
        self.client = self.app.test_client
        self.database_name = "trivia_test"
        self.database_path = "postgres://{}/{}".format('postgres:admin@localhost:5432', self.database_name)
        setup_db(self.app, self.database_path)

        # binds the app to the current context
        with self.app.app_context():
            self.db = SQLAlchemy()
            self.db.init_app(self.app)
            # create all tables
            self.db.create_all()
    
    def tearDown(self):
        """Executed after reach test"""
        pass

    """
    TODO
    Write at least one test for each test for successful operation and for expected errors.
    """
    def test_retrieve_categories(self):
        # Arrange & Act
        response = self.client().get('/categories')
        data = json.loads(response.data)
        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['success'], True)

    def test_405_method_not_allowed_retrieve_categories(self):
        # Arrange & Act
        response = self.client().post('/categories')
        data = json.loads(response.data)
        # Assert
        self.assertEqual(response.status_code, 405)
        self.assertEqual(data['success'], False)

    def test_retrieve_questions(self):
        #Arrange & Act
        response = self.client().get('/questions')
        data = json.loads(response.data)
        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(data['questions']), 10)
    
    def test_422_invalid_pagination_retrieve_questions(self):
        #Arrange & Act
        response = self.client().get('/questions?page=405')
        data = json.loads(response.data)
        # Assert
        self.assertEqual(response.status_code, 422)
        self.assertEqual(data['success'], False)

    def test_delete_questions(self):
        #Arrange & Act
        question = { 'question': 'What is the capital city of France?', 'answer': 'Paris', 'category': 3, 'difficulty': 2 }
        response = self.client().post('/questions', json = question)
        data = json.loads(response.data)
        question_id = data['created']
        response = self.client().delete(f'/questions/{question_id}')
        data = json.loads(response.data)

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['deleted'], question_id)

    def test_422_invalid_id_delete_questions(self):
        #Arrange & Act
        response = self.client().delete('/questions/4005')
        data = json.loads(response.data)

        # Assert
        self.assertEqual(response.status_code, 422)
        self.assertEqual(data['success'], False)

    def test_create_question(self):
        #Arrange & Act
        question = { 'question': 'What is the capital city of india?', 'answer': 'New Delhi', 'category': 3, 'difficulty': 2 }
        response = self.client().post('/questions', json = question)
        data = json.loads(response.data)

        #Assert
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['success'], True)        

    def test_405_method_not_allowed_create_question(self):
        #Arrange & Act
        question = { 'question': 'What is the capital city of india?', 'answer': 'New Delhi', 'category': 3, 'difficulty': 2 }
        response = self.client().patch('/questions', json = question)
        data = json.loads(response.data)

        #Assert
        self.assertEqual(response.status_code, 405)
        self.assertEqual(data['success'], False)

    def test_search_question(self):
        #Arrange & Act
        searchTerm = { 'searchTerm': 'who' }
        response = self.client().post('/questions', json = searchTerm)       
        data = json.loads(response.data)

        #Assert
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['success'], True) 
        self.assertGreater(len(data['questions']), 0)   

    def test_422_invalid_search_question(self):
        #Arrange & Act
        searchTerm = { 'searchTerm': 'hdtddudjdg' }
        response = self.client().post('/questions', json = searchTerm)       
        data = json.loads(response.data)

        #Assert
        self.assertEqual(response.status_code, 422)
        self.assertEqual(data['success'], False) 
    
    def test_filter_by_category(self):
        # Arrange & Act
        response = self.client().get('/categories/5/questions')
        data = json.loads(response.data)

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['success'], True) 
        self.assertGreater(len(data['questions']), 0) 

    def test_404_category_not_found(self):
        # Arrange & Act
        response = self.client().get('/categories/5000/questions')
        data = json.loads(response.data)

        # Assert
        self.assertEqual(response.status_code, 404)
        self.assertEqual(data['success'], False) 

    def test_400_invalid_category_id_quizzes(self):
        # Arrange & Act
        quiz = { 'previous_questions': [], 'quiz_category': { 'id': 5000, 'type': 'Invalid'} }
        response = self.client().post('/quizzes', json = quiz)       
        data = json.loads(response.data)

        # Assert
        self.assertEqual(response.status_code, 400)
        self.assertEqual(data['success'], False) 

    def test_all_quizzes(self):
        # Arrange & Act
        quiz = { 'previous_questions': [6, 10], 'quiz_category': { 'id': 0, 'type': 'click'} }
        response = self.client().post('/quizzes', json = quiz)       
        data = json.loads(response.data)
        
        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['success'], True) 

# Make the tests conveniently executable
if __name__ == "__main__":
    unittest.main()