from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import os
from functools import wraps

app = Flask(__name__)
app.secret_key = 'hotel_maroc_2024_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hotel.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)

db = SQLAlchemy(app)

# ==================== نماذج قاعدة البيانات ====================

class Room(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    room_number = db.Column(db.Integer, unique=True, nullable=False)
    room_type = db.Column(db.String(50), nullable=False)
    capacity = db.Column(db.Integer, nullable=False)
    price_per_night = db.Column(db.Float, nullable=False)
    is_available = db.Column(db.Boolean, default=True)
    reservations = db.relationship('Reservation', backref='room', lazy=True)

class Reservation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    guest_name = db.Column(db.String(100), nullable=False)
    guest_phone = db.Column(db.String(20), nullable=False)
    guest_email = db.Column(db.String(100))
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'), nullable=False)
    check_in_date = db.Column(db.String(50), nullable=False)
    check_out_date = db.Column(db.String(50), nullable=False)
    number_of_guests = db.Column(db.Integer, nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='pending')
    special_requests = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# ==================== إنشاء 200 غرفة ====================

def init_rooms():
    if Room.query.count() == 0:
        rooms = []
        
        # 50 غرفة عائلية (4-8 أشخاص) - الأرقام 1-50
        for i in range(1, 51):
            rooms.append(Room(
                room_number=i,
                room_type='family',
                capacity=8,
                price_per_night=800.0
            ))
        
        # 50 غرفة فردية (شخص واحد) - الأرقام 51-100
        for i in range(51, 101):
            rooms.append(Room(
                room_number=i,
                room_type='single',
                capacity=1,
                price_per_night=300.0
            ))
        
        # 50 غرفة مناسبات (حتى 20 شخص) - الأرقام 101-150
        for i in range(101, 151):
            rooms.append(Room(
                room_number=i,
                room_type='event',
                capacity=20,
                price_per_night=2000.0
            ))
        
        # 50 غرفة مزدوجة (شخصين) - الأرقام 151-200
        for i in range(151, 201):
            rooms.append(Room(
                room_number=i,
                room_type='double',
                capacity=2,
                price_per_night=500.0
            ))
        
        db.session.add_all(rooms)
        db.session.commit()

# ==================== الترجمات ====================

translations = {
    'en': {
        'title': 'Grand Hotel Maroc - 200 Rooms',
        'name': 'Full Name',
        'phone': 'Phone Number',
        'email': 'Email (Optional)',
        'room_type': 'Room Type',
        'check_in': 'Check-in Date (12:00 PM)',
        'check_out': 'Check-out Date (12:00 PM)',
        'guests': 'Number of Guests',
        'special_requests': 'Special Requests',
        'book': 'Book Now',
        'admin_login': 'Admin Login',
        'admin_logout': 'Logout',
        'admin_panel': 'Admin Panel',
        'password': 'Password',
        'login': 'Login',
        'family': 'Family Room (4-8 persons) - 800 MAD/night',
        'single': 'Single Room (1 person) - 300 MAD/night',
        'event': 'Event Room (up to 20 persons) - 2000 MAD/night',
        'double': 'Double Room (2 persons) - 500 MAD/night',
        'available': 'Available',
        'occupied': 'Occupied',
        'total_rooms': 'Total: 200 Rooms',
        'family_rooms': 'Family (50)',
        'single_rooms': 'Single (50)',
        'event_rooms': 'Event (50)',
        'double_rooms': 'Double (50)',
        'all_reservations': 'All Reservations',
        'pending': 'Pending',
        'confirmed': 'Confirmed',
        'cancelled': 'Cancelled',
        'confirm': 'Confirm',
        'cancel': 'Cancel',
        'delete': 'Delete',
        'print': 'Print Invoice',
        'id': 'ID',
        'guest': 'Guest',
        'room': 'Room',
        'dates': 'Dates',
        'status': 'Status',
        'actions': 'Actions',
        'total_price': 'Total Price',
        'statistics': 'Statistics',
        'total_reservations': 'Total Reservations',
        'total_revenue': 'Total Revenue',
        'occupancy_rate': 'Occupancy Rate',
        'wrong_password': 'Wrong password',
        'booking_success': 'Booking request sent! Waiting for confirmation.',
        'booking_confirmed': 'Booking confirmed',
        'booking_cancelled': 'Booking cancelled',
        'booking_deleted': 'Booking deleted',
        'room_changed': 'Room changed successfully',
        'max_guests_error': 'Maximum {max} guests allowed for this room type',
        'select_room': 'Select Room Type',
        'back_to_home': 'Back to Home',
        'dashboard': 'Dashboard',
        'rooms_management': 'Rooms Management',
        'capacity': 'Capacity',
        'price_per_night': 'Price/Night (MAD)',
        'admin_password': 'admin123',
        'currency': 'MAD',
        'welcome': 'Welcome to Grand Hotel Maroc',
        'luxury_stay': '200 luxury rooms in the heart of Morocco',
        'check_in_time': 'Check-in: 12:00 PM',
        'check_out_time': 'Check-out: 12:00 PM',
        'hours_24': '24-hour stay',
        'hotel_name': 'Grand Hotel Maroc',
        'invoice': 'Invoice',
        'thank_you': 'Thank you for your trust',
        'nights': 'nights'
    },
    'fr': {
        'title': 'Grand Hôtel Maroc - 200 Chambres',
        'name': 'Nom Complet',
        'phone': 'Numéro de Téléphone',
        'email': 'Email (Optionnel)',
        'room_type': 'Type de Chambre',
        'check_in': "Date d'arrivée (12:00)",
        'check_out': 'Date de départ (12:00)',
        'guests': 'Nombre de personnes',
        'special_requests': 'Demandes spéciales',
        'book': 'Réserver',
        'admin_login': 'Admin Connexion',
        'admin_logout': 'Déconnexion',
        'admin_panel': "Panneau d'Administration",
        'password': 'Mot de passe',
        'login': 'Connexion',
        'family': 'Chambre Familiale (4-8 pers) - 800 MAD/nuit',
        'single': 'Chambre Simple (1 pers) - 300 MAD/nuit',
        'event': 'Salle événement (20 pers) - 2000 MAD/nuit',
        'double': 'Chambre Double (2 pers) - 500 MAD/nuit',
        'available': 'Disponible',
        'occupied': 'Occupé',
        'total_rooms': 'Total: 200 Chambres',
        'family_rooms': 'Familiales (50)',
        'single_rooms': 'Simples (50)',
        'event_rooms': 'Événement (50)',
        'double_rooms': 'Doubles (50)',
        'all_reservations': 'Toutes les Réservations',
        'pending': 'En attente',
        'confirmed': 'Confirmé',
        'cancelled': 'Annulé',
        'confirm': 'Confirmer',
        'cancel': 'Annuler',
        'delete': 'Supprimer',
        'print': 'Imprimer Facture',
        'id': 'ID',
        'guest': 'Client',
        'room': 'Chambre',
        'dates': 'Dates',
        'status': 'Statut',
        'actions': 'Actions',
        'total_price': 'Prix Total',
        'statistics': 'Statistiques',
        'total_reservations': 'Total Réservations',
        'total_revenue': 'Revenu Total',
        'occupancy_rate': "Taux d'occupation",
        'wrong_password': 'Mot de passe incorrect',
        'booking_success': 'Demande envoyée! En attente de confirmation.',
        'booking_confirmed': 'Réservation confirmée',
        'booking_cancelled': 'Réservation annulée',
        'booking_deleted': 'Réservation supprimée',
        'room_changed': 'Chambre changée',
        'max_guests_error': 'Maximum {max} personnes pour ce type',
        'select_room': 'Sélectionner le type',
        'back_to_home': "Retour à l'Accueil",
        'dashboard': 'Tableau de bord',
        'rooms_management': 'Gestion des Chambres',
        'capacity': 'Capacité',
        'price_per_night': 'Prix/Nuit (MAD)',
        'admin_password': 'admin123',
        'currency': 'MAD',
        'welcome': 'Bienvenue au Grand Hôtel Maroc',
        'luxury_stay': '200 chambres de luxe au cœur du Maroc',
        'check_in_time': 'Arrivée: 12:00',
        'check_out_time': 'Départ: 12:00',
        'hours_24': 'Séjour de 24h',
        'hotel_name': 'Grand Hôtel Maroc',
        'invoice': 'Facture',
        'thank_you': 'Merci de votre confiance',
        'nights': 'nuits'
    },
    'ar': {
        'title': 'فندق جراند المغرب - 200 غرفة',
        'name': 'الاسم الكامل',
        'phone': 'رقم الهاتف',
        'email': 'البريد الإلكتروني (اختياري)',
        'room_type': 'نوع الغرفة',
        'check_in': 'تاريخ الوصول (12:00 ظهراً)',
        'check_out': 'تاريخ المغادرة (12:00 ظهراً)',
        'guests': 'عدد الأشخاص',
        'special_requests': 'طلبات خاصة',
        'book': 'احجز الآن',
        'admin_login': 'دخول المدير',
        'admin_logout': 'تسجيل خروج',
        'admin_panel': 'لوحة التحكم',
        'password': 'كلمة المرور',
        'login': 'دخول',
        'family': 'غرفة عائلية (4-8 أشخاص) - 800 درهم/ليلة',
        'single': 'غرفة فردية (شخص واحد) - 300 درهم/ليلة',
        'event': 'غرفة مناسبات (حتى 20 شخص) - 2000 درهم/ليلة',
        'double': 'غرفة مزدوجة (شخصين) - 500 درهم/ليلة',
        'available': 'متاحة',
        'occupied': 'محجوزة',
        'total_rooms': 'الإجمالي: 200 غرفة',
        'family_rooms': 'عائلية (50)',
        'single_rooms': 'فردية (50)',
        'event_rooms': 'مناسبات (50)',
        'double_rooms': 'مزدوجة (50)',
        'all_reservations': 'جميع الحجوزات',
        'pending': 'قيد الانتظار',
        'confirmed': 'مؤكد',
        'cancelled': 'ملغي',
        'confirm': 'تأكيد',
        'cancel': 'إلغاء',
        'delete': 'حذف',
        'print': 'طباعة فاتورة',
        'id': 'الرقم',
        'guest': 'الضيف',
        'room': 'الغرفة',
        'dates': 'التواريخ',
        'status': 'الحالة',
        'actions': 'الإجراءات',
        'total_price': 'السعر الإجمالي',
        'statistics': 'الإحصائيات',
        'total_reservations': 'إجمالي الحجوزات',
        'total_revenue': 'إجمالي الإيرادات',
        'occupancy_rate': 'نسبة الإشغال',
        'wrong_password': 'كلمة المرور خطأ',
        'booking_success': 'تم إرسال طلب الحجز! في انتظار التأكيد.',
        'booking_confirmed': 'تم تأكيد الحجز',
        'booking_cancelled': 'تم إلغاء الحجز',
        'booking_deleted': 'تم حذف الحجز',
        'room_changed': 'تم تغيير الغرفة بنجاح',
        'max_guests_error': 'الحد الأقصى {max} أشخاص لهذه الغرفة',
        'select_room': 'اختر نوع الغرفة',
        'back_to_home': 'العودة للرئيسية',
        'dashboard': 'لوحة الإحصائيات',
        'rooms_management': 'إدارة الغرف',
        'capacity': 'السعة',
        'price_per_night': 'السعر/ليلة (درهم)',
        'admin_password': 'admin123',
        'currency': 'درهم',
        'welcome': 'مرحباً بكم في فندق جراند المغرب',
        'luxury_stay': '200 غرفة فاخرة في قلب المغرب',
        'check_in_time': 'الدخول: 12:00 ظهراً',
        'check_out_time': 'الخروج: 12:00 ظهراً',
        'hours_24': 'إقامة 24 ساعة',
        'hotel_name': 'فندق جراند المغرب',
        'invoice': 'فاتورة',
        'thank_you': 'شكراً لثقتكم بنا',
        'nights': 'ليالي'
    }
}

# ==================== دالة التحقق ====================

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            flash(translations[session.get('lang', 'ar')]['wrong_password'], 'danger')
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function

# ==================== المسارات ====================

@app.route('/')
def home():
    lang = session.get('lang', 'ar')
    
    # إحصائيات الغرف المتاحة فقط (الغير محجوزة)
    rooms_stats = {
        'family': Room.query.filter_by(room_type='family', is_available=True).count(),
        'single': Room.query.filter_by(room_type='single', is_available=True).count(),
        'event': Room.query.filter_by(room_type='event', is_available=True).count(),
        'double': Room.query.filter_by(room_type='double', is_available=True).count()
    }
    
    # الحجوزات (للمدير فقط)
    reservations = []
    total_revenue = 0
    occupancy_rate = 0
    
    if session.get('admin_logged_in'):
        reservations = Reservation.query.order_by(Reservation.created_at.desc()).all()
        total_revenue = db.session.query(db.func.sum(Reservation.total_price)).filter(Reservation.status == 'confirmed').scalar() or 0
        occupied_rooms = Room.query.filter_by(is_available=False).count()
        occupancy_rate = (occupied_rooms / 200) * 100
    
    # جميع الغرف مرتبة حسب الرقم
    rooms = Room.query.order_by(Room.room_number).all()
    
    # التاريخ الحالي
    now = datetime.now().strftime('%Y-%m-%d')
    
    return render_template('index.html',
                         lang=lang,
                         t=translations[lang],
                         rooms_stats=rooms_stats,
                         reservations=reservations,
                         rooms=rooms,
                         total_revenue=total_revenue,
                         occupancy_rate=occupancy_rate,
                         admin_logged_in=session.get('admin_logged_in', False),
                         now=now)

@app.route('/set_language/<lang>')
def set_language(lang):
    if lang in translations:
        session['lang'] = lang
    return redirect(url_for('home'))

@app.route('/reserve', methods=['POST'])
def reserve():
    lang = session.get('lang', 'ar')
    
    if request.method == 'POST':
        guest_name = request.form['name']
        guest_phone = request.form['phone']
        guest_email = request.form.get('email', '')
        room_type = request.form['room']
        check_in = request.form['check_in']
        check_out = request.form['check_out']
        guests = int(request.form['guests'])
        special_requests = request.form.get('special_requests', '')
        
        # التحقق من صحة التواريخ
        if check_out <= check_in:
            flash('تاريخ المغادرة يجب أن يكون بعد تاريخ الوصول', 'danger')
            return redirect(url_for('home'))
        
        # التحقق من عدد الأشخاص حسب نوع الغرفة
        max_guests = {
            'single': 1,
            'double': 2,
            'family': 8,
            'event': 20
        }.get(room_type, 0)
        
        if guests > max_guests:
            error_msg = translations[lang]['max_guests_error'].format(max=max_guests)
            flash(error_msg, 'danger')
            return redirect(url_for('home'))
        
        # البحث عن غرفة متاحة من نفس النوع
        available_room = Room.query.filter_by(room_type=room_type, is_available=True).first()
        
        if available_room:
            check_in_date = datetime.strptime(check_in, '%Y-%m-%d')
            check_out_date = datetime.strptime(check_out, '%Y-%m-%d')
            nights = (check_out_date - check_in_date).days
            
            if nights > 0:
                total_price = nights * available_room.price_per_night
                
                # إنشاء الحجز بحالة pending والغرفة تبقى متاحة
                new_reservation = Reservation(
                    guest_name=guest_name,
                    guest_phone=guest_phone,
                    guest_email=guest_email,
                    room_id=available_room.id,
                    check_in_date=check_in,
                    check_out_date=check_out,
                    number_of_guests=guests,
                    total_price=total_price,
                    special_requests=special_requests,
                    status='pending'
                )
                
                db.session.add(new_reservation)
                db.session.commit()
                
                flash(translations[lang]['booking_success'], 'success')
            else:
                flash('يجب أن تكون مدة الإقامة يوم على الأقل', 'danger')
        else:
            flash('عذراً، لا توجد غرف متاحة من هذا النوع', 'danger')
    
    return redirect(url_for('home'))

@app.route('/admin/login', methods=['POST'])
def admin_login():
    lang = session.get('lang', 'ar')
    password = request.form['password']
    
    if password == translations[lang]['admin_password']:
        session['admin_logged_in'] = True
        session.permanent = True
        flash('مرحباً بك يا مدير', 'success')
    else:
        flash(translations[lang]['wrong_password'], 'danger')
    
    return redirect(url_for('home'))

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    flash('تم تسجيل الخروج بنجاح', 'info')
    return redirect(url_for('home'))

@app.route('/admin/confirm/<int:id>')
@login_required
def confirm_reservation(id):
    lang = session.get('lang', 'ar')
    reservation = Reservation.query.get_or_404(id)
    
    reservation.status = 'confirmed'
    
    room = Room.query.get(reservation.room_id)
    if room:
        room.is_available = False
    
    db.session.commit()
    flash(translations[lang]['booking_confirmed'], 'success')
    return redirect(url_for('home'))

@app.route('/admin/cancel/<int:id>')
@login_required
def cancel_reservation(id):
    lang = session.get('lang', 'ar')
    reservation = Reservation.query.get_or_404(id)
    
    reservation.status = 'cancelled'
    
    db.session.commit()
    flash(translations[lang]['booking_cancelled'], 'warning')
    return redirect(url_for('home'))

@app.route('/admin/delete/<int:id>')
@login_required
def delete_reservation(id):
    lang = session.get('lang', 'ar')
    reservation = Reservation.query.get_or_404(id)
    
    if reservation.status == 'confirmed':
        room = Room.query.get(reservation.room_id)
        if room:
            room.is_available = True
    
    db.session.delete(reservation)
    db.session.commit()
    flash(translations[lang]['booking_deleted'], 'info')
    return redirect(url_for('home'))

@app.route('/admin/change_room/<int:id>', methods=['POST'])
@login_required
def change_room(id):
    lang = session.get('lang', 'ar')
    reservation = Reservation.query.get_or_404(id)
    new_room_id = request.form.get('new_room_id')
    
    if new_room_id:
        new_room = Room.query.get(int(new_room_id))
        if new_room and new_room.room_type == reservation.room.room_type:
            old_room_id = reservation.room_id
            
            # تغيير الغرفة
            reservation.room_id = new_room.id
            
            # تحديث حالة الغرف
            old_room = Room.query.get(old_room_id)
            if old_room and reservation.status == 'confirmed':
                old_room.is_available = True
            
            if reservation.status == 'confirmed':
                new_room.is_available = False
            
            db.session.commit()
            flash(translations[lang]['room_changed'], 'success')
    
    return redirect(url_for('home'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        init_rooms()
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)