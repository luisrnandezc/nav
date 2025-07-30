# NAV Aviation - Flight School Management System

A comprehensive Django-based web application for managing flight school operations, student records, flight training, and academic progress tracking.

<img width="1732" height="1125" alt="NAV LOGO HORIZONTAL MINIATURA ORANGE" src="https://github.com/user-attachments/assets/8ce428d1-82e1-4b2f-a76c-591ec036bbe2" />

## 🚁 Overview

NAV Aviation is a complete flight school management system designed to streamline operations for aviation training institutions. The system manages student enrollment, flight training records, academic progress, instructor assignments, and administrative tasks.

## ✨ Features

### 🎓 Academic Management
- **Course Management**: Complete course catalog with different aviation programs (PPA, HVI, PCA, IVA, IVS, RCL)
- **Subject Tracking**: Individual subject management with credit hours and passing grades
- **Grade Management**: Comprehensive grading system with test types and recovery options
- **Student Progress**: Real-time tracking of academic performance and course completion

### 🛩️ Flight Training Management
- **Flight Logs**: Detailed flight session recording with evaluation criteria
- **Simulator Training**: Comprehensive simulator session tracking and evaluation
- **Flight Evaluations**: Structured evaluation forms for different flight training phases:
  - 0-100 hours (Basic training)
  - 100-120 hours (Intermediate training)
  - 120-170 hours (Advanced training)
- **Aircraft Management**: Fleet tracking and aircraft assignment
- **Instructor Assignment**: Automatic instructor-student pairing based on qualifications

### 👥 User Management
- **Multi-Role System**: Students, Instructors, and Staff with role-based permissions
- **Profile Management**: Detailed profiles for each user type with aviation-specific information
- **Authentication**: Secure login system with password management
- **Permission Control**: Granular permissions for different user roles

### 💰 Financial Management
- **Payment Tracking**: Student payment records and confirmation system
- **Balance Management**: Real-time student account balance tracking
- **Payment Confirmation**: Staff approval workflow for payments

### 📊 Dashboard & Reporting
- **Student Dashboard**: Personal progress tracking, grades, and flight hours
- **Instructor Dashboard**: Teaching assignments, student progress, and evaluation tools
- **Staff Dashboard**: Administrative overview and management tools
- **PDF Generation**: Automated report generation for flight logs and evaluations

### 🌐 Website & Marketing
- **Public Website**: Professional website showcasing courses and services
- **Course Information**: Detailed course descriptions and requirements
- **3D Aircraft Viewer**: Interactive 3D aircraft model display
- **Responsive Design**: Mobile-friendly interface

## 🛠️ Technology Stack

- **Backend**: Django 5.2.3
- **Database**: PostgreSQL
- **Frontend**: HTML5, CSS3, JavaScript
- **PDF Generation**: WeasyPrint
- **3D Visualization**: Three.js
- **Deployment**: PythonAnywhere (Production)

## 📋 Prerequisites

- Python 3.8+
- PostgreSQL
- Git

## 🎯 Key Applications

### Academic App (`academic/`)
- Course and subject management
- Student enrollment tracking
- Grade management system
- Academic progress monitoring

### Flight Management System (`fms/`)
- Flight log recording
- Simulator training tracking
- Comprehensive evaluation forms
- PDF report generation

### User Management (`accounts/`)
- Multi-role user system
- Profile management
- Authentication and authorization
- Role-based permissions

### Dashboard (`dashboard/`)
- Student progress dashboards
- Instructor management tools
- Administrative overview
- Reporting and analytics

## 🔐 User Roles & Permissions

### Student
- View personal progress and grades
- Access flight training records
- View course materials
- Track payment history

### Instructor
- Manage assigned students
- Record flight evaluations
- Submit grades and assessments
- Access teaching materials

### Staff
- Administrative oversight
- Payment confirmation
- User management
- System configuration

## 🛫 Flight Training Features

### Flight Evaluation Forms
The system includes comprehensive evaluation forms for different training phases:

1. **Basic Training (0-100 hours)**
   - Pre-flight procedures
   - Basic flight maneuvers
   - Emergency procedures
   - Solo flight preparation

2. **Intermediate Training (100-120 hours)**
   - Advanced maneuvers
   - Instrument flying
   - Cross-country planning
   - Emergency scenarios

3. **Advanced Training (120-170 hours)**
   - Complex IFR procedures
   - Advanced aircraft operations
   - Commercial pilot skills
   - Instructor preparation

### Simulator Training
- FPT and B737 simulator support
- Detailed session tracking
- Performance evaluation
- Progress monitoring

## 📱 Mobile Responsiveness

The application is fully responsive and optimized for:
- Desktop computers
- Tablets
- Mobile phones
- Touch interfaces

## 🚀 Deployment

### Production Deployment (PythonAnywhere)
The application is configured for deployment on PythonAnywhere with:
- Automatic environment detection
- Production security settings
- SSL certificate support
- Domain configuration

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📞 Support

For support and questions:
- Email: luisrnandezc@gmail.com
- Website: [www.navaviation.org](https://www.navaviation.org)

---

**NAV Aviation** - Empowering the next generation of pilots through innovative technology and comprehensive training management. 