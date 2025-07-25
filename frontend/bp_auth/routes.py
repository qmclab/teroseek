from flask import Blueprint, render_template, request, redirect, url_for

auth_bp = Blueprint('auth',
                     __name__,
                     static_folder='static',
                     template_folder='templates'
                     )


@auth_bp.route('/login')
def login():
    return render_template('auth/login.html') 

@auth_bp.route('/logout')
def logout():
    return redirect(url_for('auth.login'))

@auth_bp.route('/register')
def register():
    return render_template('auth/register.html')