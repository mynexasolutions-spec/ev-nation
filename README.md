# EV Nation - Admin & Storefront

A modern e-commerce platform for electric vehicles, featuring a customer-facing storefront and a robust administrative lead management system.

## Features

- **Storefront:** Browse electric vehicles, view detailed specifications, and request call-backs or WhatsApp inquiries.
- **Admin Dashboard:** Manage product catalog, track customer leads with automated timestamps, and search/filter through inquiries.
- **Lead Capture:** Seamless transition from inquiry to WhatsApp/Call with data persistence.
- **Scalable Leads:** Pagination and search built to handle high volume.

## Tech Stack

- **Backend:** FastAPI (Python)
- **Database:** SQLite with SQLAlchemy ORM
- **Frontend:** Jinja2 Templates, Vanilla CSS, and Modern JavaScript

## Getting Started

1. **Clone the repository:**
   ```bash
   git clone https://github.com/mynexasolutions-spec/ev-nation.git
   ```

2. **Setup virtual environment:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Variables:**
   Copy `.env.example` to `.env` and configure your settings.

5. **Run the application:**
   ```bash
   uvicorn app.main:app --reload
   ```

## License

Internal Use / Proprietary
