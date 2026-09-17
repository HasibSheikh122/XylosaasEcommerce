# 🛒 XyloSaaS — Multi-Tenant E-Commerce Backend Platform

A scalable, multi-tenant SaaS e-commerce backend built with **Django 5.2**, **django-tenants (PostgreSQL Schemas)**, **Django REST Framework (DRF)**, **Celery**, and **Redis**.

---

## 🏗️ Architecture Overview

The platform uses a schema-based multi-tenancy architecture where each store operates within its own PostgreSQL database schema, ensuring strict data isolation:

- **Public Schema (`localhost:8000`)**: Handles platform-wide data, merchant registrations, domain routing, subscription plans, and SaaS super-admin management.
- **Tenant Schemas (`<subdomain>.localhost:8000`)**: Dedicated schemas for each store containing isolated products, orders, customers, inventory, coupons, reviews, and store settings.

---

## 🚀 Key Modules & Capabilities

* **Multi-Tenant Routing:** Schema isolation via `django-tenants` with wildcard subdomain handling (`*.localhost`).
* **Authentication & RBAC:** JWT authentication (`rest_framework_simplejwt`) with strict role-based access control.
* **Order & Atomic Checkout:** High-concurrency checkout flow using `select_for_update()` row-locking to prevent inventory race conditions.
* **Payment Engine:** Unified gateway support (bKash, Nagad, SSLCommerz, Stripe) with webhook listeners, refund automation, and audit logging.
* **Storefront Management:** Themes, branding, announcements, navigation menus, and custom pages per tenant.
* **Background Tasks (Async):** Celery + Redis worker for decoupled order confirmation emails.
* **Scheduled Tasks (Periodic):** Celery Beat DatabaseScheduler for automated daily subscription expiration audits.

---

## 🛠️ Tech Stack

* **Framework:** Django 5.2 | Django REST Framework (DRF)
* **Multi-Tenancy:** `django-tenants`
* **Database:** PostgreSQL (Schema-based isolation)
* **Task Queue & Cache:** Celery 5.2 | Redis
* **API Documentation:** Swagger / OpenAPI (`drf-yasg`)
* **Admin Theme:** Jazzmin

---

## ⚙️ Local Development Setup

### 1. Clone & Environment Setup
```powershell
git clone <repository-url>
cd XylosaasEcommerce

# Create & activate virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt


Command:
 Server Run: 
        python manage.py runserver 

 Celery Werker run: 
        celery -A xyloshop worker --pool=solo -l info


 xyloshop celery run:
        celery -A xyloshop beat -l info



2. Database Migration (Multi-Tenant)
    python manage.py makemigrations
    python manage.py migrate_schemas


# 3. Seed Initial Subscription Plans & Superuser
Create a superuser inside the public schema:
    python manage.py create_tenant_superuser
    # Enter Tenant Schema: public


Terminal 1: Redis Server
    redis-cli ping  # Confirms Redis is running (returns PONG)

Terminal 2: Django Development Server
    python manage.py runserver

Terminal 3: Celery Worker (Windows)
    celery -A xyloshop worker --pool=solo -l info

Terminal 4: Celery Beat (Periodic Scheduler)
    celery -A xyloshop beat -l info