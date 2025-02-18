from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from os import path


db = SQLAlchemy()
MYDB_NAME = "new_db"

def create_app():
   app = Flask(__name__)
   app.config['SECRET_KEY']= 'pyadav'
   app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{MYDB_NAME}'
   db.init_app(app)

   from .models import User,Professional,Service,ServiceRequest,Review,Customer
   from .views import views
   app.register_blueprint(views,url_prefix='/')

   create_database(app)
   return app
   
def create_database(app):
   with app.app_context():
         db.create_all()
         admin = models.User.query.filter_by(is_admin=True).first()
         if not admin:
           admin = models.User(email='admin@gmail.com', password = '992660', name = 'admin', is_admin = True, is_customer = False)    
           db.session.add(admin)
           db.session.commit()