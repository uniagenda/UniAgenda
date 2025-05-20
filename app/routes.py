from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from . import db, login_manager, mail
from .models import User, Appointment, Service
from flask_mail import Message
from datetime import datetime

main = Blueprint('main', __name__)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@main.route('/')
def index():
    return render_template('index.html')

@main.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        full_name = request.form['full_name']
        phone = request.form['phone']
        email = request.form['email']
        password = request.form['password']
        is_admin = False

        if User.query.filter_by(email=email).first():
            flash('E-mail já cadastrado.')
            return redirect(url_for('main.register'))

        user = User(full_name=full_name, phone=phone, email=email,
                    password=generate_password_hash(password), is_admin=is_admin)
        db.session.add(user)
        db.session.commit()
        flash('Cadastro realizado com sucesso!')
        return redirect(url_for('main.login'))
    return render_template('register.html')

@main.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email, is_admin=False).first()

        if not user or not check_password_hash(user.password, password):
            flash('Credenciais inválidas.')
            return redirect(url_for('main.login'))

        if user.bloqueado:
            flash('Seu acesso está bloqueado pelo administrador.')
            return redirect(url_for('main.login'))

        login_user(user)
        return redirect(url_for('main.dashboard'))
    return render_template('login.html')

@main.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))

@main.route('/dashboard')
@login_required
def dashboard():
    if current_user.is_admin:
        appointments = Appointment.query.all()
        services = Service.query.all()
        return render_template('admin_dashboard.html', appointments=appointments, services=services)
    else:
        appointments = Appointment.query.filter_by(user_id=current_user.id)
        return render_template('user_dashboard.html', appointments=appointments)

@main.route('/agendar', methods=['GET', 'POST'])
@login_required
def agendar():
    services = Service.query.all()
    if request.method == 'POST':
        date = request.form['date']
        time = request.form['time']
        service_id = request.form['service']
        existing = Appointment.query.filter_by(date=date, time=time).first()
        if existing:
            flash('Horário indisponível.')
            return redirect(url_for('main.agendar'))

        ag = Appointment(user_id=current_user.id, date=date, time=time, service_id=service_id)
        db.session.add(ag)
        db.session.commit()

        try:
            service = Service.query.get(service_id)
            msg = Message("Confirmação de Agendamento",
                          sender="SEU_EMAIL@gmail.com",
                          recipients=[current_user.email])
            data_formatada = datetime.strptime(date, "%Y-%m-%d").strftime("%d/%m/%Y")

            msg.body = (
                f"Seu agendamento para {service.name} foi realizado com sucesso "
                f"para {data_formatada} às {time}."
            )

            mail.send(msg)

            empresas = User.query.filter_by(is_admin=True, bloqueado=False).all()
            for empresa in empresas:
                msg_empresa = Message("Novo Agendamento Recebido",
                                      sender="SEU_EMAIL@gmail.com",
                                      recipients=[empresa.email])
                msg_empresa.body = (
                    f"Novo agendamento de {current_user.full_name} ({current_user.phone})\n"
                    f"Serviço: {service.name}\n"
                    f"Data: {data_formatada} às {time}\n"
                )
                mail.send(msg_empresa)
        except:
            pass

        flash('Agendamento realizado com sucesso!')
        return redirect(url_for('main.dashboard'))
    return render_template('agendamento.html', services=services)

@main.route('/servicos', methods=['GET', 'POST'])
@login_required
def servicos():
    if not current_user.is_admin:
        return redirect(url_for('main.dashboard'))
    if request.method == 'POST':
        nome = request.form['nome']
        novo = Service(name=nome)
        db.session.add(novo)
        db.session.commit()
        flash('Serviço cadastrado!')
    services = Service.query.all()
    return render_template('servicos.html', services=services)

@main.route('/servicos/excluir/<int:id>')
@login_required
def excluir_servico(id):
    if not current_user.is_admin:
        return redirect(url_for('main.dashboard'))
    servico = Service.query.get(id)
    if servico:
        db.session.delete(servico)
        db.session.commit()
        flash('Serviço excluído com sucesso.')
    return redirect(url_for('main.servicos'))

@main.route('/empresa/register', methods=['GET', 'POST'])
def empresa_register():
    if request.method == 'POST':
        full_name = request.form['full_name']
        phone = request.form['phone']
        email = request.form['email']
        password = request.form['password']
        if User.query.filter_by(email=email).first():
            flash('E-mail já cadastrado.')
            return redirect(url_for('main.empresa_register'))
        user = User(full_name=full_name, phone=phone, email=email,
                    password=generate_password_hash(password), is_admin=True)
        db.session.add(user)
        db.session.commit()
        flash('Cadastro de empresa realizado com sucesso!')
        return redirect(url_for('main.empresa_login'))
    return render_template('empresa_register.html')

@main.route('/empresa/login', methods=['GET', 'POST'])
def empresa_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email, is_admin=True).first()
        if not user or not check_password_hash(user.password, password):
            flash('Credenciais inválidas.')
            return redirect(url_for('main.empresa_login'))

        if user.bloqueado:
            flash('Seu acesso está bloqueado pelo administrador.')
            return redirect(url_for('main.empresa_login'))

        login_user(user)
        return redirect(url_for('main.dashboard'))
    return render_template('empresa_login.html')

@main.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == 'admin' and password == 'system10':
            session['admin_logged_in'] = True
            return redirect(url_for('main.admin_painel'))
        flash('Credenciais incorretas.')
    return render_template('admin_login.html')

@main.route('/admin/painel')
def admin_painel():
    if not session.get('admin_logged_in'):
        return redirect(url_for('main.admin_login'))
    users = User.query.all()
    return render_template('admin_painel.html', users=users)

@main.route('/admin/bloquear/<int:id>')
def admin_bloquear(id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('main.admin_login'))
    user = User.query.get(id)
    user.bloqueado = True
    db.session.commit()
    return redirect(url_for('main.admin_painel'))

@main.route('/admin/desbloquear/<int:id>')
def admin_desbloquear(id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('main.admin_login'))
    user = User.query.get(id)
    user.bloqueado = False
    db.session.commit()
    return redirect(url_for('main.admin_painel'))

@main.route('/admin/excluir/<int:id>')
def admin_excluir(id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('main.admin_login'))
    user = User.query.get(id)
    db.session.delete(user)
    db.session.commit()
    return redirect(url_for('main.admin_painel'))
