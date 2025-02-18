from functools import wraps
from sqlalchemy.exc import IntegrityError
from sqlalchemy import or_
from flask import Blueprint,render_template,redirect ,url_for,request,flash, session
from datetime import datetime
from . import db
from .models import User,Professional,Service, ServiceRequest, Review , Customer
from sqlalchemy.orm import joinedload
from sqlalchemy import func
import matplotlib 
matplotlib.use('Agg')
from matplotlib import pyplot as plt
from collections import Counter

views = Blueprint('views',__name__)

def auth_required(function):
    @wraps(function)
    def wrap(*args, **kwargs):
        if 'professional_id' not in session:
            flash('you need to login first.','danger')
            return redirect(url_for('views.professional_login'))
        return function(*args, **kwargs)
    return wrap


def admin_required(function):
    @wraps(function)
    def inner(*args, **kwargs):
        if 'admin_id' not in session:
            flash('you need to login first.','danger')
            return redirect(url_for('views.admin_login'))
        return function(*args, **kwargs)
    return inner


@views.route('/')
def index():
    return render_template('index.html')


def views_required(function):
    @wraps(function)
    def inner(*args, **kwargs):
        if 'user_id' not in session:
            flash('you need to login first.','danger')
            return redirect(url_for('views.login'))
        return function(*args, **kwargs)
    return inner

@views.route('/login')
def login():
    return render_template("login.html")
    
@views.route('/customer/signup')
def customer_signup():
    return render_template("customer_signup.html")

@views.route('/professionals/register')
def professionals_register():
    services = Service.query.all()
    return render_template("professionals_signup.html",services=services)

@views.route('/customer/signup', methods = ['POST'])
def signup_post():
    email = request.form.get('email')
    password = request.form.get('password')
    name = request.form.get('name')
    address = request.form.get('address')
    location = request.form.get('location')
    pincode = request.form.get('pincode')
    contact_number = request.form.get('contact')
    if email == '' or password == '' or name == '' or address == '' or location == '' or pincode == '' or contact_number == '':
       flash('please fill out the form','danger')
       return redirect(url_for('views.customer_signup'))
    if User.query.filter_by(email=email).first():
        flash('Email already exists.','danger')
        return redirect(url_for('views.customer_signup'))
    if Professional.query.filter_by(email=email).first():
        flash('email already exists.','danger')
        return redirect(url_for('views.customer_signup'))
        
    user = User(email=email, password=password, name=name, address=address, location=location, pincode=pincode, contact_number = contact_number)
    db.session.add(user)
    db.session.commit()

    new_customer = Customer(user_id = user.user_id,name = name, contact_number = contact_number, address = address,location=location, pincode=pincode)

    db.session.add(new_customer)
    db.session.commit()
    flash('User successfully signed up.','success')
    return redirect(url_for('views.login'))

@views.route('/login', methods = ['POST'])
def login_post():
    email = request.form.get('email')
    password = request.form.get('password')
    if not email or not password:
        flash('please fill out all fields','danger')
        return redirect(url_for('views.login'))

    user = User.query.filter_by(email=email).first()
    if not user:
        flash('Email does not exist','danger')
        return redirect(url_for('views.login'))
    if not user.check_password(password):
        flash('incorrect password','danger')
        return redirect(url_for('views.login'))
    if user.is_admin:
        flash('You are not authorized to view this page, please login with admin login','danger')
        return redirect(url_for('views.login'))
    if user.is_customer is False:
        flash('You are not authorized log in as a customer.','danger')

    session['user_id'] = user.user_id
    generate_customer_summary(user.user_id)
    return redirect(url_for('views.customer_dashboard'))
       # login succesfull 
    

@views.route('/customer/dashboard')
@views_required
def customer_dashboard():
    user = User.query.get(session['user_id'])
    customer = user.customer_details
    service_requests = ServiceRequest.query.filter(
        ServiceRequest.customer_id == customer.customer_id,
        ServiceRequest.service_status.isnot(None)
     ).all()

    all_services = Service.query.all()


    
    return render_template("customer_dashboard.html",user=user, service_requests=service_requests,all_services=all_services)

@views.route('/customer/dashboard/<service_name>',methods=['GET'])
@views_required
def service_details(service_name):
    user = User.query.get(session['user_id'])
    customer = user.customer_details
    service_requests = ServiceRequest.query.filter(
        ServiceRequest.customer_id == customer.customer_id,
        ServiceRequest.service_status.isnot(None)
     ).all()

    service = Service.query.filter_by(service_name = service_name).first()
    all_services = Service.query.all()
    if not service:
        flash(f'No {service_name} services found','danger')
        return redirect(url_for('views.customer_dashboard'))
    
    professionals = service.professionals
    professional_avg_rating = {}
    for professional in professionals:
        ratings = [request.review.rating for request in  professional.service_requests if request.review]
        avg_rating = None
        if ratings:
            avg_rating = sum(ratings) / len(ratings)
        professional_avg_rating[professional.professional_id] = avg_rating
    return render_template('customer_dashboard_service.html',service=service,user=user,service_requests=service_requests, professionals=professionals, service_name=service_name,all_services=all_services,professional_avg_rating=professional_avg_rating)

@views.route('/customer/dashboard/book/<professional_id>/<service_id>', methods=['GET','POST'])
@views_required
def service_book(professional_id,service_id):
    user = User.query.get(session['user_id'])
    customer = user.customer_details
    professional = Professional.query.get_or_404(professional_id)
    service = Service.query.get_or_404(service_id) 
    service_request = ServiceRequest(
        customer_id = customer.customer_id,
        professional_id = professional.professional_id,
        service_id = service.service_id,
        service_status = 'Requested',
    )

    db.session.add(service_request)
    db.session.commit()
    flash('booking done','success')
    return redirect(url_for('views.customer_dashboard'))

@views.route('/customer/dashboard/service_close/<professional_id>/<service_request_id>',methods = ['GET','POST'])
@views_required
def service_close(professional_id, service_request_id):
    user = User.query.get(session['user_id'])
    customer = user.customer_details
    service_request = ServiceRequest.query.filter_by(id=service_request_id, customer_id = customer.customer_id).first()

    professional = Professional.query.get_or_404(professional_id)
    current_time = datetime.utcnow().date()
    service = professional.services[0] if professional.services else None
    if request.method == 'POST':
        service_request_id = service_request.id
        customer_id = customer.customer_id
        rating = (request.form.get('rating'))
        remarks = request.form.get('remarks')

        
        if  not rating :
            flash('Rating can not be empty, please fill again','danger')
            return redirect(url_for('views.service_close',professional_id = professional_id , service_request_id = service_request_id ))
        
        new_review = Review(service_request_id=service_request_id,customer_id=customer_id,rating = rating,remarks=remarks)
        service_request.service_status = 'closed'
        service_request.date_of_completion = datetime.utcnow()
        db.session.add(new_review)
        db.session.commit()
        flash('Service done succesfully, Have a nice day.','success')
        return redirect(url_for('views.customer_dashboard'))
    return render_template('service_close.html',user = user, customer = customer,professional = professional,service=service, service_request=service_request,current_time = current_time)


@views.route('/customer/summary')
@views_required
def customer_summary():
    user = User.query.get(session['user_id'])
    customer = user.customer_details
    generate_customer_summary(user.user_id)
    service_requests = ServiceRequest.query.filter(ServiceRequest.customer_id == customer.customer_id).order_by(ServiceRequest.id.desc()).first()
    return render_template('customer_summary.html',service_requests=service_requests,customer=customer)

@views.route('/customer/profile')
@views_required
def customer_profile():
    return render_template('customer_profile.html', user=User.query.get(session['user_id']))

@views.route('/customer/profile', methods = ['POST'])
@views_required
def customer_profile_post():
    user = User.query.get(session['user_id'])
    email = request.form.get('email')
    name = request.form.get('name')
    currentpassword = request.form.get('currentpassword')
    password = request.form.get('password')
    if email == '' or currentpassword == '' or password == '':
        flash('Email or Current Password or New Password cannot be empty.','danger')
        return redirect(url_for('views.customer_profile'))
    if not user.check_password(currentpassword):
        flash('Incorrect Current Password','danger')
        return  redirect(url_for('views.customer_profile'))
    if User.query.filter_by(email=email).first() and email != user.username:
        flash('Email with this email already exists. Please choose some other email.','danger')
        return redirect(url_for('views.customer_profile'))
    user.email = email
    user.name = name
    user.password = password
    db.session.commit()
    flash('Profile updated Succesfully','success')
    return  redirect(url_for('views.customer_profile'))



@views.route('/customer/search', methods=['GET'])
@views_required
def customer_search():
    parameter = request.args.get('type')
    search = request.args.get('search', '').strip()
    if not parameter or not search:
       return render_template('customer_search.html', service_name = [] , professional_name = [] , pincode =[], search = ''), 400
    
    service_name = []
    professional_name = [] 
    pincode = []

    if parameter == 'service_name':
       service_name = Service.query.filter(
            Service.service_name.contains(search)
            ).all()
       return render_template('customer_search.html', service_name = service_name , professional_name = [] , pincode = [], search = search)

    elif parameter == 'professional_name':
       professional_name = Professional.query.filter(Professional.name.contains(search)
            ).all()
       return render_template('customer_search.html',service_name = [] , professional_name = professional_name , pincode = [], search = search)

    elif parameter == 'pincode':
        pincode = Professional.query.filter(Professional.pincode.contains(search)
            ).all()
        return render_template('customer_search.html',service_name = [], professional_name = [] , pincode = pincode, search = search)

    return render_template('customer_search.html',service_name = [] , professional_name = [] , pincode = [], search = search)


@views.route('/professionals/register', methods = ['GET','POST'])
def register_post():
    email = request.form.get('email')
    password = request.form.get('password')
    name = request.form.get('name')
    address = request.form.get('address')
    experience = request.form.get('experience')
    file = request.files.get('file')
    pincode = request.form.get('pincode')
    service_name = request.form.get('service')
    service_description = request.form.get('service_description')
    phonenumber = request.form.get('phonenumber')
    
    if email == '' or password == '' or name == '' or address == '' or file == '' or pincode == '' or service_name == '' or experience == '' or phonenumber == '' :
       flash('please fill out the form','danger')
       return redirect(url_for('views.professionals_register'))
    if Professional.query.filter_by(email=email).first():
        flash('email already exists.','danger')
        return redirect(url_for('views.professionals_register'))
        
    if User.query.filter_by(email=email).first():
        flash('email already exists.','danger')
        return redirect(url_for('views.professionals_register'))
        
    file_data = file.read() if file and file.filename else None
    
    professional = Professional(email=email, name=name, address=address, file=file_data, pincode=pincode, experience = experience, phonenumber = phonenumber, service_description=service_description)
    professional.password = password
    db.session.add(professional)

    try:
        db.session.commit()

        service = Service.query.filter_by(service_name=service_name).first()
        if not service:
            service = Service(service_name=service_name,professional_id = professional.professional_id)
            db.session.add(service)
        service.professionals.append(professional)
        db.session.commit()
        flash('Professional succesfully registered.','success')
    except IntegrityError:
          db.session.rollback()
          flash('registeration failed. Please try again.','danger')
    
    return redirect(url_for('views.professional_login'))



@views.route('/professional/login')
def professional_login():
    return render_template("professionals_login.html")

@views.route('/professional/login', methods = ['POST'])
def professionals_login():
    email = request.form.get('email')
    password = request.form.get('password')
    if not email or not password:
        flash('please fill out all fields','danger')
        return redirect(url_for('views.professional_login'))
    professional = Professional.query.filter_by(email=email).first()
    if not professional:
        flash('Email does not exist','danger')
        return redirect(url_for('views.professional_login'))

    if professional.action == 'Rejected':
        flash('Your account has been rejected. please contact admin.','danger')
        return redirect(url_for('views.professional_login'))

    if not professional.check_password(password):
        flash('incorrect password','danger')
        return redirect(url_for('views.professional_login'))
    


    session['professional_id'] = professional.professional_id
    generate_professional_summary(professional.professional_id)
    return redirect(url_for('views.professional_dashboard'))

@views.route('professional/dashboard')
@auth_required
def professional_dashboard():
    current_professional_id = session.get('professional_id')
    today = datetime.utcnow().date()

    today_services = db.session.query(ServiceRequest).filter(
        ServiceRequest.professional_id == current_professional_id,
        func.date(ServiceRequest.date_of_request) == today
    ).all()

    
    closed_services = db.session.query(ServiceRequest).filter(
        ServiceRequest.professional_id == current_professional_id,
        ServiceRequest.service_status == 'closed').all()
    
    return render_template('professional_dashboard.html',today_services = today_services,closed_services = closed_services)

@views.route('professional/dashboard/accept/int:<id>', methods =['GET','POST'])
@auth_required
def professional_customer_accept(id):
    professional = Professional.query.get(session['professional_id'])
    service_request = ServiceRequest.query.get(id)
    if request.method == 'POST':
        service_request.service_status = 'accepted'
        db.session.commit()
        flash('Service Request is accepted.','success')
        return redirect(url_for('views.professional_dashboard'))
    return render_template('professional/accept.html', professional=professional, service_request=service_request)
    
 

    

@views.route('professional/dashboard/reject/int:<id>', methods = ['GET','POST'])
@auth_required
def professional_customer_reject(id):
    professional = Professional.query.get(session['professional_id'])
    service_request = ServiceRequest.query.get(id)
    if request.method == 'POST':
        service_request.service_status = 'rejected'
        db.session.commit()
        flash('Service Request is rejected.','success')
        return redirect(url_for('views.professional_dashboard'))
    return render_template('professional/reject.html', professional=professional, service_request=service_request)
    

@views.route('/professional/search', methods = ['GET'])
@auth_required
def professional_search():
    professional = Professional.query.get(session['professional_id'])
    parameter = request.args.get('type')
    search = request.args.get('search')
    dates = [] 
    names = []
    pincodes = []
    locations = []
    if not parameter or not search:
        return render_template('professional_search.html', dates = [] , names = [] , pincodes = [] , locations =[], search ='' ), 400
    elif parameter == 'dates':
         dates = ServiceRequest.query.filter(ServiceRequest.date_of_request.contains(search),ServiceRequest.professional_id == professional.professional_id).all()
         return render_template('professional_search.html', dates = dates , names = [] , pincodes = [] , locations =[], search = search )
    elif parameter == 'names':
        names = ServiceRequest.query.filter(ServiceRequest.customers.has(Customer.name.contains(search)),ServiceRequest.professional_id == professional.professional_id).all()
        return render_template('professional_search.html', dates = [] , names = names , pincodes = [] , locations =[], search = search)
    elif parameter == 'locations':
        locations = ServiceRequest.query.filter(ServiceRequest.customers.has(Customer.location.contains(search)),ServiceRequest.professional_id == professional.professional_id).all()
        return render_template('professional_search.html', dates = [] , names = [] , pincodes = [] , locations = locations , search = search )
    elif parameter == 'pincodes':
        pincodes = ServiceRequest.query.filter(ServiceRequest.customers.has(Customer.pincode.contains(search)),ServiceRequest.professional_id == professional.professional_id).all()
        return render_template('professional_search.html', dates = [] , names = [] , pincodes = pincodes , locations =[], search = search )

    return render_template('professional_search.html', dates = [] , names = [] , pincodes = [] , locations =[], search = '')



@views.route('/professional/summary')
@auth_required
def professional_summary():

    professionals = Professional.query.get(session['professional_id'])
    professional = professionals.professional_id
    generate_professional_summary(professional)
    return render_template('professional_summary.html',professional=professional)

@views.route('professionals/profile')
@auth_required
def professional_profile():
    return render_template('professional_profile.html', user = Professional.query.get(session['professional_id']))

@views.route('professionals/profile', methods = ['POST'])
@auth_required
def professional_profile_post():
    user = Professional.query.get(session['professional_id'])
    email = request.form.get('email')
    name = request.form.get('name')
    service_name = request.form.get('service')
    currentpassword = request.form.get('currentpassword')
    password = request.form.get('password')
    if email == '' or currentpassword == '' or password == '':
        flash('Email or Current Password or New Password cannot be empty.','danger')
        return redirect(url_for('views.professional_profile'))
    if not user.check_password(currentpassword):
        flash('Incorrect Current Password','danger')
        return  redirect(url_for('views.professional_profile'))
    if Professional.query.filter_by(email=email).first() and email != user.username:
        flash('Email with this email already exists. Please choose some other email.','danger')
        return redirect(url_for('views.professional_profile'))
    user.email = email
    user.name = name
    user.password = password
    
    service = Service.query.filter_by(service_name = service_name).first()
    if service:
        user.services= [service]
    else:
        new_service = Service(service_name=service_name)
        db.session.add(new_service)
        db.session.commit()
        user.services.append(new_service) #add the newly created service to the professional's service
    db.session.commit()
    flash('Profile updated Succesfully','success')
    return  redirect(url_for('views.professional_dashboard'))



@views.route('/admin')
def admin_login():
    return render_template('admin_login.html')

@views.route('/admin', methods = ['POST'])
def admin_login_post():
    email = request.form.get('email')
    password = request.form.get('password')
    if not email or not password:
        flash('please fill out all fields','danger')
        return redirect(url_for('views.admin_login'))

    user = User.query.filter_by(email=email).first()
    if not user:
        flash('Email does not exist','danger')
        return redirect(url_for('views.admin_login'))
    if not user.check_password(password):
        flash('incorrect password','danger')
        return redirect(url_for('views.admin_login'))
    if not user.is_admin:
        flash('You are not authorized to view this page','danger')
        return redirect(url_for('views.admin_login'))
    session['admin_id'] = user.user_id
    generate_admin_summary(user.user_id)
    return redirect(url_for('views.admin_dashboard'))
    # login succesfull as Admin



@views.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    services = Service.query.all()
    professionals = Professional.query.all()
    service_requests = ServiceRequest.query.all()
    return render_template('admin_dashboard.html', services = services , professionals = professionals, service_requests = service_requests)


@views.route('/admin/search', methods=['GET'])
@admin_required
def admin_search():
    parameter = request.args.get('type')
    search = request.args.get('search', '').strip()
    search_date = request.args.get('search')
    if not parameter or not search:
       return render_template('admin_search.html', services = [] , professionals = [] , servicereqs = [] , customers = [],search = ''), 400
    if parameter == 'service':
       services = Service.query.filter(
            or_(
                Service.service_id.contains(search),
                Service.service_name.contains(search),
                Service.base_price.contains(search)
            )
        ).all()
       return render_template('admin_search.html', services = services , professionals = [] , servicereqs = [] ,customers = [], search = search)
    elif parameter == 'professional':
       professionals = Professional.query.join(Professional.services).filter(
            or_ (
                Professional.professional_id.contains(search), 
                Professional.name.contains(search),
                Professional.experience.contains(search),
                Service.service_name.contains(search),
                Professional.action.contains(search)
                )
            ).all()
       return render_template('admin_search.html',services = [] , professionals = professionals, servicereqs = [],customers = [] , search = search)
    elif parameter == 'servicerequest':
        
        
        servicereqs = ServiceRequest.query.filter(
            or_ (ServiceRequest.id.contains(search),
                ServiceRequest.professional.has(Professional.name.contains(search)),
                ServiceRequest.date_of_request.contains(search_date),
                ServiceRequest.service_status.contains(search)
                )
            ).all()
        return render_template('admin_search.html' , services = [] , professionals = [] , servicereqs = servicereqs , customers = [], search = search)
            
    elif parameter == 'customer':
        customers = Customer.query.join(Customer.service_requests).filter(
            or_(
                Customer.customer_id.contains(search),
                Customer.name.contains(search),
                Customer.contact_number.contains(search),
                Customer.address.contains(search),
                ServiceRequest.service_status.contains(search)
            )    
        ).all()
        return render_template('admin_search.html',services = [] , professionals = [] , servicereqs = [] , customers = customers, search = search)
    return render_template('admin_search.html', services = [] , professionals = [] , servicereqs = [] ,customers = [], search = '')

@views.route('/admin/dashboard/service_detail/<int:service_id>')
@admin_required
def service_id_details(service_id):
    service = Service.query.get(service_id)
    service_requests = ServiceRequest.query.filter(ServiceRequest.service_id == service.service_id)
    return render_template('service/service_details.html',service_requests = service_requests,service =service)

@views.route('/admin/dashboard/professional_detail/<int:professional_id>')
@admin_required
def professional_id_details(professional_id):
    professional = Professional.query.get(professional_id)

    ratings = [request.review.rating for request in  professional.service_requests if request.review]
    avg_rating = None
    if ratings:
        avg_rating = sum(ratings) / len(ratings)
    return render_template('professional/professional_details.html',professional=professional,avg_rating=avg_rating)
    
@views.route('/admin/summary')
@admin_required
def admin_summary():
    user = User.query.get(session['admin_id'])
    generate_admin_summary(user.user_id)
    service_requests = ServiceRequest.query.order_by(ServiceRequest.id.desc()).all()
    return render_template('admin_summary.html', service_requests = service_requests)
    

@views.route('/admin/services/newservice')
@admin_required
def admin_add_newservice():
    return render_template('service/add.html')

@views.route('/admin/services/newservice', methods = ['GET','POST'])
@admin_required
def admin_addd_newservice():
    if request.method == 'POST':
        service_name = request.form.get('name')
        description = request.form.get('description')
        base_price = request.form.get('base_price')
        if service_name == '':
            flash('Service name cannot be empty.','danger')
            return redirect(url_for('views.admin_add_newservice'))
        if description == '':
            flash('Description cannot be empty.','danger')
            return redirect(url_for('views.admin_add_newservice'))
        if base_price == '':
            flash('Base price cannot be empty.','danger')
            return redirect(url_for('views.admin_add_newservice'))
        existing_service = Service.query.filter_by(service_name=service_name).first()
        if existing_service:
            flash('Service name already existed.','danger')    
            return redirect(url_for('views.admin_dashboard'))
        new_service= Service(service_name = service_name, description = description, base_price = base_price)
        db.session.add(new_service)
        db.session.commit()
        flash('Service added succesfully.','success')
        return redirect(url_for('views.admin_dashboard'))
    return render_template('service/add.html')

@views.route('/admin/service/<int:service_id>/edit')
@admin_required
def admin_edit_service(service_id):
    return render_template('service/edit.html')

@views.route('/admin/service/<int:service_id>/edit', methods = ['POST'])
@admin_required
def admin_edit_service_post(service_id):
    service = Service.query.get(service_id)
    service_name = request.form.get('name')
    base_price = request.form.get('base_price')
    description = request.form.get('description')
    if service_name == '' :
        flash('service name can not be empty.','danger')
        return redirect(url_for('views.admin_edit_service',service_id = service_id))
    if base_price == '':
        flash('Base price can not be empty.','danger')
        return redirect(url_for('views.admin_edit_service',service_id = service_id))
    service.service_name = service_name
    service.base_price = base_price
    service.description = description
    db.session.commit()
    flash('Service updated succesfully.','success')
    return redirect(url_for('views.admin_dashboard'))


@views.route('/admin/service/delete/<int:service_id>')
@admin_required
def admin_delete_service(service_id):
    user = User.query.get(session['admin_id'])
    service = Service.query.get(service_id)
    return render_template('service/delete.html', user = user, service = service)

@views.route('/admin/service/delete/<int:service_id>',methods = ['POST'])
@admin_required
def admin_delete_service_post(service_id):
    service = Service.query.get(service_id)
    
    if not service:
        flash('Service not found','danger')
        return redirect(url_for('views.admin_dashboard'))
    elif service.professionals:
        for professional in service.professionals:
            service.professionals.remove(professional)
        db.session.commit()
            
    elif service.service_requests:
        for request in service.service_requests:
            if request.review:
                db.session.delete(request.review)
            db.session.delete(request)
        db.session.commit()
 

    db.session.delete(service)
    db.session.commit()
    flash('Service deleted succesfully.','success')
    return redirect(url_for('views.admin_dashboard'))

    
@views.route('/admin/professional/approve/<int:professional_id>/approve', methods = ['GET','POST'])
@admin_required
def admin_professional_approve(professional_id):
    user = User.query.get(session['admin_id'])
    professional = Professional.query.get(professional_id)
    
    if request.method == 'POST':
        professional.is_approved = True
        professional.action = 'Approved'
        db.session.commit()
        flash('Professional approved successfully','success')
        return redirect(url_for('views.admin_dashboard'))
    return render_template('professional/approve.html', user = user, professional = professional)


@views.route('/admin/professional/reject/<int:professional_id>/reject', methods = ['GET','POST'])
@admin_required
def admin_professional_reject(professional_id):
    user = User.query.get(session['admin_id'])
    professional = Professional.query.get(professional_id)

    if request.method == 'POST':
        professional.action = 'Rejected'
        db.session.commit()
        flash('Professional Rejected successfully','success')
        return redirect(url_for('views.admin_dashboard'))
    return render_template('professional/reject.html', user = user, professional = professional)

@views.route('/admin/professional/delete/<int:professional_id>/delete')
@admin_required
def admin_professional_delete(professional_id):
    user = User.query.get(session['admin_id'])
    professional = Professional.query.get(professional_id)
    return render_template('professional/delete.html', user = user, professional = professional)


@views.route('/admin/professional/delete/<int:professional_id>/delete', methods = ['POST'])
@admin_required
def admin_professional_delete_post(professional_id):
    professional = Professional.query.get(professional_id)
    if not professional:
        flash('Professionals does not exist.','danger')
        return redirect(url_for('views.admin_dashboard'))
    
    if professional.services:
        for service in professional.services:
           if professional in service.professionals:
              service.professional.remove(professional)
        db.session.commit()
            
    if professional.service_requests:
        for request in professional.service_requests:
            if request.review:
                db.session.delete(request.review)
            db.session.delete(request)
        db.session.commit()

    db.session.delete(professional)
    db.session.commit()
    flash('Professional deleted succesfully.','success')
    return redirect(url_for('views.admin_dashboard'))

@views.route('/admin/dashboard/professional/unblock/<int:professional_id>',methods = ["POST"])
@admin_required
def admin_professional_unblock(professional_id):
    professional = Professional.query.get(professional_id)
    professional.action = 'None'
    db.session.commit()
    flash('Professional unblock succesfully','success')
    return redirect(url_for('views.admin_dashboard'))


@views.route('/customer/logout')
def customer_logout():
    session.pop('user_id',None)
    flash('you have been logged out','danger')
    return redirect(url_for('views.index'))

@views.route('/professional/logout')
def professional_logout():
    session.pop('professional_id',None)
    flash('you have been logged out','danger')
    return redirect(url_for('views.index'))

@views.route('/admin/logout')
def admin_logout():
    session.pop('admin_id',None)
    flash('you have been logged out','danger')
    return redirect(url_for('views.index'))


def generate_customer_summary(user_id):
    user = User.query.get(session['user_id'])
    customer = user.customer_details
    service_requests = ServiceRequest.query.filter(ServiceRequest.customer_id == customer.customer_id).all()
    labels = ["Requested","Assigned","Closed"]
    path="/Users/priyanshuyadav/Downloads/mad 1 project/Todo/static/customer_summary/"
    if not service_requests:
       fig,ax = plt.subplots()
       ax.text(0.5,0.5,'No Service Requests Yet',ha='center',va='center',fontsize=12)
       path="/Users/priyanshuyadav/Downloads/mad 1 project/Todo/static/customer_summary/"
       plt.savefig(path+f"customer_summary_{customer.customer_id}.jpg") 


    requested_count = 0
    assigned_count = 0
    closed_count = 0
    for service_request in service_requests:
        if service_request.service_status == 'Requested':
            requested_count += 1
        elif service_request.service_status == 'accepted':
            assigned_count += 1
        elif service_request.service_status == 'closed':
            closed_count += 1
    
    data = [requested_count,assigned_count,closed_count]

    plt.bar(labels,data,width=0.3,color="green")
    plt.savefig(path+f"customer_summary_{customer.customer_id}.jpg")
    plt.clf() #clear for next plot


def generate_professional_summary(professional_id):
    professional = Professional.query.get(session['professional_id'])
    service_requests = ServiceRequest.query.filter(ServiceRequest.professional_id == professional.professional_id).all()
    labels = ["Requested","Assigned","Closed"]
    path="/Users/priyanshuyadav/Downloads/mad 1 project/Todo/static/professional_summary/"
    requested_count = 0
    assigned_count = 0
    closed_count = 0
    rating = []
    for service_request in service_requests:
        if service_request.service_status == 'Requested':
            requested_count += 1
        elif service_request.service_status == 'accepted':
            assigned_count += 1
        elif service_request.service_status == 'closed':
            closed_count += 1
        if service_request.review:
            rating.append(service_request.review.rating)
        
    
    
    data = [requested_count,assigned_count,closed_count]

    plt.bar(labels,data,width=0.3,color="green")
    plt.savefig(path+f"professional_{professional.professional_id}"+".jpg")
    plt.clf() #clear for next plot

    if rating:
        rating_counts = Counter(rating)
        rating_labels = [f"Rating {r}" for r in rating_counts.keys()]
        rating_data = list(rating_counts.values())

        fig, ax = plt.subplots()
        ax.pie(rating_data,labels=rating_labels,autopct='%1.2f%%',startangle = 90, colors = ['red','yellow','lightgreen','lightskyblue',])
        
        image_path = "/Users/priyanshuyadav/Downloads/mad 1 project/Todo/static/professional_summary/"
        plt.savefig(image_path + f"professional_{professional.professional_id}_pie"+".jpg")
        plt.clf()
    else:
        fig, ax = plt.subplots()
        ax.pie([1],labels=["No Rating Available"], colors=["green"],startangle=90)
        image_path = "/Users/priyanshuyadav/Downloads/mad 1 project/Todo/static/professional_summary/"
        plt.savefig(image_path + f"professional_{professional.professional_id}_pie"+".jpg")
        plt.clf()



            

def generate_admin_summary(admin_id):
    service_requests = ServiceRequest.query.all()
    labels = ["Requested","Assigned","Closed"]
    path="/Users/priyanshuyadav/Downloads/mad 1 project/Todo/static/admin_summary/"
    requested_count = 0
    assigned_count = 0
    closed_count = 0

    rating = []
    for service_request in service_requests:
        if service_request.service_status == 'Requested':
            requested_count += 1
        elif service_request.service_status == 'accepted':
            assigned_count += 1
        elif service_request.service_status == 'closed':
            closed_count += 1
        if service_request.review:
            rating.append(service_request.review.rating)
    
    data = [requested_count,assigned_count,closed_count]


    plt.bar(labels,data,width=0.3,color="green")
    plt.savefig(path+"service_request"+".jpg")
    plt.clf() #clear for next plot
            
    if rating:
        rating_counts = Counter(rating)
        rating_labels = [f"Rating {r}" for r in rating_counts.keys()]
        rating_data = list(rating_counts.values())

        fig, ax = plt.subplots()
        ax.pie(rating_data,labels=rating_labels,autopct='%1.2f%%',startangle = 90, colors = ['red','yellow','lightgreen','lightskyblue','purple'])
        
        image_path = "/Users/priyanshuyadav/Downloads/mad 1 project/Todo/static/admin_summary/"
        plt.savefig(image_path +"rating_summary"+".jpg")
        plt.clf()

    else:
        fig, ax = plt.subplots()
        ax.pie([1],labels=["No Rating Available"], colors=["green"],startangle=90)
        image_path = "/Users/priyanshuyadav/Desktop/mad 1 project/Todo/static/admin_summary"
        plt.savefig(image_path + "rating_summary"+".jpg")
        plt.clf()


        

