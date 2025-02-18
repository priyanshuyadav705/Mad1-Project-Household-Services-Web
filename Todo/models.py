from . import db
from flask_login import UserMixin
from datetime import datetime , timedelta
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model, UserMixin):
     __tablename__ = 'user'
     user_id = db.Column(db.Integer, primary_key = True)
     email = db.Column(db.String(150), unique= True)
     _password = db.Column(db.String(150))
     name = db.Column(db.String(150))
     address = db.Column(db.String(500))
     location = db.Column(db.String(50))
     pincode = db.Column(db.String(20))
     contact_number = db.Column(db.String(10))
     created_at = db.Column(db.DateTime, default=datetime.utcnow)
     is_admin = db.Column(db.Boolean, nullable = False, default = False)
     is_customer = db.Column(db.Boolean, nullable = False, default=True)

     customer_details = db.relationship('Customer', backref='user_details', uselist = False)

     @property
     def password(self):
          raise AttributeError('password is not readable attribute')
     
     @password.setter
     def password(self, password):
          self._password = generate_password_hash(password)

     def check_password(self, password):
          return check_password_hash(self._password , password)
          
class Customer(db.Model):
     __tablename__ = 'customer'
     customer_id = db.Column(db.Integer,primary_key=True)
     user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable = False)
     name = db.Column(db.String(150))
     contact_number = db.Column(db.String(10))
     address = db.Column(db.String(500))
     created_at = db.Column(db.DateTime, default=datetime.utcnow)
     location = db.Column(db.String(50))
     pincode = db.Column(db.String(20))
     user = db.relationship('User', backref='customer_info',lazy = True)
     service_requests = db.relationship('ServiceRequest', backref= 'customers', lazy = True)

     @property
     def is_today(self):
          return self.created_at.date() == datetime.utcnow().date()
     def is_closed(self):
          return datetime.utcnow() - self.created_at > timedelta(days=60)


professional_service = db.Table('professional_service',
           db.Column('professional_id', db.Integer, db.ForeignKey('professional.professional_id'), primary_key = True),
           db.Column('service_id', db.Integer, db.ForeignKey('service.service_id'),primary_key = True)
           )

class Professional(db.Model):
     __tablename__ = 'professional'
     professional_id = db.Column(db.Integer, primary_key = True)
     email = db.Column(db.String(150), unique= True)
     _password = db.Column(db.String(150))
     name = db.Column(db.String(100), nullable = False)
     address = db.Column(db.String(150))
     file = db.Column(db.LargeBinary)
     pincode = db.Column(db.String(50))
     is_approved = db.Column(db.Boolean, default=False)
     action = db.Column(db.String(50), nullable = True ,default='None')
     experience = db.Column(db.String(10))
     phonenumber = db.Column(db.String(50))
     service_description = db.Column(db.String(150))

     services = db.relationship('Service', secondary=professional_service, backref = 'professional', lazy='joined',cascade = 'all,delete,delete')

     @property
     def password(self):
          raise AttributeError('password is not readibe attribute')
     
     @password.setter
     def password(self, password):
          self._password = generate_password_hash(password)

     def check_password(self, password):
          return check_password_hash(self._password , password)
     
class Service(db.Model):
     __tablename__ = 'service'
     professional_id = db.Column(db.Integer,db.ForeignKey('professional.professional_id'), nullable = True)
     service_id = db.Column(db.Integer, primary_key = True)
     description = db.Column(db.String(150))
     service_name = db.Column(db.String(54), nullable=False)
     base_price = db.Column(db.Float)
     created_at = db.Column(db.DateTime, default = datetime.utcnow)
     updated_at = db.Column(db.DateTime, onupdate = datetime.utcnow)
     
     professionals = db.relationship('Professional', secondary = professional_service , backref='service',  lazy = 'joined', cascade = 'all,delete')
     service_requests = db.relationship('ServiceRequest', backref = 'services', lazy = True, cascade = 'all, delete-orphan')

class ServiceRequest(db.Model):
      __tablename__ = 'service_request'
      id = db.Column(db.Integer, primary_key = True)
      service_id = db.Column(db.Integer,db.ForeignKey('service.service_id'), nullable = False)
      customer_id = db.Column(db.Integer,db.ForeignKey('customer.customer_id'), nullable = False)
      professional_id = db.Column(db.Integer,db.ForeignKey('professional.professional_id'), nullable = False)
      date_of_request = db.Column(db.DateTime,default= db.func.current_timestamp())
      date_of_completion = db.Column(db.DateTime,nullable = True)
      service_status = db.Column(db.String(50))

      professional = db.relationship('Professional', backref = 'service_requests', lazy = True)
      review = db.relationship('Review',uselist=False,backref = 'service_request',lazy='joined',cascade = 'all, delete-orphan')
      
class Review(db.Model):
      __tablename__ = 'review'
      id = db.Column(db.Integer, primary_key =True )  
      service_request_id = db.Column(db.Integer,db.ForeignKey('service_request.id'))
      customer_id = db.Column(db.Integer,db.ForeignKey('customer.customer_id'), nullable = False)
      rating = db.Column(db.Integer, nullable = False)
      remarks = db.Column(db.String(255),nullable = True)
      comments = db.Column(db.String(250))
