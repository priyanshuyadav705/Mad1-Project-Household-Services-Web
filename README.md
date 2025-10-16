# A-Z Household Services (MAD–I Project)

**Name:** Priyanshu Yadav  
**Roll No.:** 23f1000018  
**Email:** 23f1000018@ds.study.iitm.ac.in  
**Course:** IITM BS – Diploma Level  

---

## 📄 Description

I approached the given problem statement in the following 3 phases:

- **Phase 1:**  
  Finalized the necessary information required for the proper and smooth functioning of the webapp. Designed a suitable database structure for information storage.

- **Phase 2:**  
  Created the basic framework with routes and functions implemented.

- **Phase 3:**  
  Styling and Aesthetics – Focused on polishing the web pages to look cleaner and more user-friendly.

---

## 🛠 Modules / Technologies Used

- **Flask:** Entire web application built on the Flask framework.  
- **Jinja Template:** Webpages follow Jinja templating.  
- **SQLite3:** Database used is SQLite3.  
- **CSS:** Basic styling of pages.  
- **Flask-SQLAlchemy:** For creating the relational database.  
- **Session:** Provides basic login and logout features.  
- **matplotlib.pyplot:** For creating graphs.  
- **datetime:** For storing dates of requests and service completion.

---

## 🗄 Database Design

- **Tables used:** User, Customer, Professional, Service, Service Request, Review.  
- **Many-to-Many Relationship:** Used between `Professional` and `Service`. One service can be offered by multiple professionals and one professional can offer multiple services. A joint table is used to implement this relationship.  


---

## 🏗 Architecture

The project folder consists of three main parts:

1. **Todo Folder:**  
   Contains the `templates` folder with HTML files, `models.py` for database tables, `views.py` and `__init__.py` for controllers and routes.

2. **Instance Folder:**  
   Contains the generated SQLite database.

3. **main.py:**  
   Main controllers to run the application.

**How to use the application:**
After extracting the zip folder, create a virtual environment in the same folder and run:

``bash
python main.py

## ✨ Features

**Core Features:**

- **Separate Login Forms:** Admin, User, and Professional.  
- **Service Management:** Admin can perform CRUD operations on services.  
- **Professional Management:** Admin can perform CRUD operations on professionals.  
- **Booking Services:** Users can book services.  
- **Rating:** Users can rate services.  
- **Service Approval:** Professionals can accept or reject service requests.  
- **Search:** Search for services, professionals, or service requests by service name, professional name, location, pincode, etc.  
- **Forms:** Designed with suitable messages and fields for easy data entry.  
- **Success/Error Messages:** Implemented using Jinja templates.  
- **Styling:** Minor styling using CSS.  
- **Login Framework:** Session-based login system for users and professionals.
  
## 🎥 Demo Video

🔗 [**Watch the demo on Google Drive**](https://drive.google.com/file/d/1j8MNO3WWhrF_5kbCkayBuwv1HYILZn3E/view?usp=sharing)
