# 💼 BusinessMS — Business Management System

[![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.12%20%7C%203.13-blue.svg?logo=python&logoColor=white)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-5.1%20%2F%206.1-darkgreen.svg?logo=django&logoColor=white)](https://www.djangoproject.com/)
[![Tests](https://img.shields.io/badge/Tests-31%20Passed-success.svg?logo=checkmarx&logoColor=white)](#automated-testing)
[![License](https://img.shields.io/badge/License-MIT-purple.svg)](LICENSE)
[![UI/UX](https://img.shields.io/badge/UI%2FUX-Bootstrap%205%20%2B%20Plus%20Jakarta%20Sans-orange.svg)](https://getbootstrap.com/)

A modern, full-featured **Business Management System (ERP / CRM / Billing)** built with **Django** and **Python**. Designed for small-to-medium businesses to manage customers, track inventory & products, generate tax-compliant invoices, record payments, and monitor business analytics through an executive dashboard.

---

## 🌟 Key Features

### 1. 📊 Executive Dashboard & Analytics
- **Live KPI Metric Cards:** Real-time metrics for Total Customers, Active Products, Total Sales, Revenue Collected, and Pending Outstandings.
- **Dynamic Charts:** 
  - 6-Month Monthly Revenue trend line/bar chart using **Chart.js**.
  - Invoice status distribution doughnut chart (Paid, Partial, Unpaid, Overdue, Draft).
- **Recent Activities Feed:** Quick review of latest invoices, newly registered customers, and incoming payments.
- **Inventory Stock Alerts:** Instant warnings for low-stock (≤ 5 units) and out-of-stock items.

### 2. 👥 Customer Relationship Management (CRM)
- Full **CRUD** operations (Create, Read, Update, Delete with confirmation dialog).
- Multi-field search by customer name, email, phone, company, or city.
- Status filtering (Active / Inactive) and pagination (10 per page).
- Customer profile detail view displaying lifetime spending (`total_spent`) and invoice history.

### 3. 📦 Products & Inventory Management
- Physical products vs. professional services categorization.
- Automatic stock level tracking with badge alerts (`In Stock`, `Low Stock`, `Out of Stock`).
- Model-level validation preventing negative prices or negative stock quantities.
- Filter by category, item type, and stock availability.

### 4. 📄 Sales & Invoicing System
- **Guaranteed Sequential Invoice Numbers:** Auto-generated `INV-YYYY-XXXX` format.
- **Dynamic Line Items:** Multiple products/services per invoice with quantity, unit price, and automated subtotals.
- **Tax & Discount Calculations:** Accurate percentage-based tax and currency discount processing.
- **Automated Lifecycle Status:** Smart status transitions between `Draft`, `Unpaid`, `Sent`, `Partially Paid`, `Paid`, and `Overdue`.
- **Printable Invoices:** Dedicated clean print view (`invoice_print.html`) optimized for A4 paper print and PDF generation with signature blocks.

### 5. 💳 Payment Tracking & Accounting
- Multiple payment modes supported: UPI, Direct Bank Transfer, Credit/Debit Card, Cash, Cheque.
- **Server-Side Overpayment Prevention:** Prevents entering payments greater than outstanding invoice balance.
- Automated balance due deduction and instant invoice status updates upon payment submission or deletion.

### 6. 🛡️ Custom Executive Admin Portal
- Modern Slate theme (`#0f172a`) with custom typography (**Plus Jakarta Sans**).
- Direct **"← Return to Main App"** navigation bar button.
- Real-time database metrics strip and categorized application cards.
- Status pill badges for invoices, stock levels, and active customers.

---

## 🛠️ Technology Stack

| Layer | Technology |
| :--- | :--- |
| **Backend** | Python 3.13, Django 6.1 (compatible with Django 5.x) |
| **Database** | SQLite (Production-ready for PostgreSQL / MySQL) |
| **Frontend** | HTML5, CSS3, JavaScript, Bootstrap 5.3, Bootstrap Icons |
| **Visualizations** | Chart.js 4.x |
| **Typography** | Plus Jakarta Sans (Google Fonts) |
| **Testing** | Django TestCase (`django.test`) |

---

## 🚀 Getting Started

Follow these step-by-step instructions to set up and run the project locally.

### 1. Prerequisites
Ensure you have Python 3.11+ and Git installed on your system:
```bash
python --version
git --version
```

### 2. Clone the Repository
```bash
git clone https://github.com/<your-username>/businessms.git
cd businessms
```

### 3. Create & Activate a Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

### 5. Set Up Environment Variables (Optional)
```bash
# Copy the example environment file
cp .env.example .env
```

### 6. Apply Database Migrations
```bash
python manage.py migrate
```

### 7. Create Superuser (Admin Account)
```bash
python manage.py createsuperuser
```

### 8. Run the Development Server
```bash
python manage.py runserver
```

Open your browser and navigate to:
- **Main Application:** [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- **Admin Portal:** [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)

---

## 🧪 Automated Testing

The project includes 31 comprehensive automated unit tests covering all core modules, business validations, financial calculations, and access control.

To run the full test suite:
```bash
python manage.py test
```

### Test Coverage Highlights:
- **Core App (`core/tests.py`):** Dashboard view protection, context aggregation, user registration, authentication flow.
- **Customers App (`customers/tests.py`):** Model validation, search filters, pagination, CRUD views, deletion confirmations.
- **Products App (`products/tests.py`):** Stock level checks, non-negative price validation, service vs physical item logic.
- **Sales App (`sales/tests.py`):** Sequential invoice number generation, line item calculation, tax & discount logic, overpayment prevention, status transitions.

---

## 📁 Project Structure

```text
businessms/
├── businessms/          # Project settings, root URL configuration, WSGI
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── core/                # Dashboard, Authentication, Profile, Custom Tags
│   ├── forms.py
│   ├── models.py
│   ├── views.py
│   └── templatetags/
├── customers/           # Customer Management (CRM)
│   ├── forms.py
│   ├── models.py
│   ├── views.py
│   └── urls.py
├── products/            # Products & Inventory Management
│   ├── forms.py
│   ├── models.py
│   ├── views.py
│   └── urls.py
├── sales/               # Invoices, Line Items & Payment Processing
│   ├── forms.py
│   ├── models.py
│   ├── views.py
│   └── urls.py
├── static/              # CSS Stylesheets, JS, Images
│   └── css/
│       ├── dashboard.css
│       └── custom_admin.css
├── templates/           # Jinja/Django HTML Templates
│   ├── admin/
│   ├── core/
│   ├── customers/
│   ├── products/
│   ├── sales/
│   └── base.html
├── .env.example         # Template for environment configuration
├── .gitignore           # Git ignore rules (protects db.sqlite3 & secrets)
├── manage.py            # Django CLI management script
├── requirements.txt     # Python dependencies
└── README.md            # Project documentation
```

---

## 🔒 Security Best Practices
- **Protected Database & Secrets:** `.gitignore` ensures that SQLite databases, `.env` files, and local logs are never tracked or committed.
- **CSRF Protection:** All POST forms strictly use Django's `{% csrf_token %}`.
- **Access Control:** All sensitive customer, inventory, and sales endpoints are guarded with `@login_required`.
- **Server-Side Validation:** All financial inputs (taxes, discounts, quantities, prices, payments) are validated in Django model `clean()` methods to prevent tampered requests.

---

## 👤 Author
Developed by **Aman Kumar**  
- Email: [techcodemn@gmail.com](mailto:techcodemn@gmail.com)

---

## 📄 License
This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
