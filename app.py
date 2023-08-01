from flask import Flask, render_template, url_for, request, redirect, jsonify, send_from_directory, flash
from models import db, User, logged_users, OAuth2Client
from flask_login import LoginManager, login_user, current_user, login_required, logout_user
from oauth2 import config_oauth, authorization, require_oauth
from authlib.oauth2 import OAuth2Error
import os
import time
import json
from authlib.integrations.flask_oauth2 import current_token

login_manager = LoginManager()

def create_app(config_file=None):
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'secret!'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'
    app.config['AUTHLIB_INSECURE_TRANSPORT'] = '1' #change this in production
    os.environ['AUTHLIB_INSECURE_TRANSPORT'] = '1'
    db.init_app(app)
    with app.app_context():
        db.create_all()

    login_manager.login_view = "login"
    login_manager.init_app(app)
    config_oauth(app)
    return app


app = create_app()


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    return 'Hello, World!' +( current_user.username if current_user.is_authenticated  else "not logged in")

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'GET':
        return render_template('signup.html')
    
    username = request.form.get('username')
    password = request.form.get('password')
    
    user = User.query.filter_by(username=username).first()
    if user:
        return "User already exists", 409
    
    user = User(username=username, password=password)
    db.session.add(user)
    db.session.commit()

    #Just to see if it works
    user = User.query.filter_by(username=username).first()
    return "User added successfully"+str(user.username),200


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')

    username = request.form.get('username')
    password = request.form.get('password')
    user = User.query.filter_by(username=username).first()
    if not user or not user.check_password(password):
        return "Wrong username or password", 401
    
    login_user(user)

    return redirect(url_for('me'))

# This is a protected route
@app.route('/me')
@login_required
def me():
    return render_template('me.html', user=User.query.filter_by(id = current_user.id), clients=OAuth2Client.query.filter_by(user_id=current_user.id).all())

@app.route('/client_register', methods=['GET', 'POST'])
@login_required
def client_register():
    if request.method == 'GET':
        return render_template('client_register.html')

    name = request.form.get('name')
    #Client ID and Client Secret are generated automatically
    client_id =  os.urandom(24).hex()
    client_secret = os.urandom(24).hex()

    client = OAuth2Client(
        client_id=client_id,
        client_id_issued_at=int(time.time()),
        user_id=current_user.id,
    )

    client_metadata = {
        "client_name": name,
        "redirect_uris": request.form.get('redirect_uris').splitlines(),
        "scope": "profile",
        "grant_types": ["authorization_code"], # For the token endpoint
        "response_types": ["code"] # For the authorization endpoint
    }

    client.set_client_metadata(client_metadata)
    client.client_secret = client_secret
    db.session.add(client)
    db.session.commit()
    return redirect(url_for('me'))


@app.route('/oauth/authorize', methods=['GET', 'POST'])
@login_required
def authorize():

    if request.method == 'POST':
        grant_user = None
        if request.form.get('confirm'):
            grant_user = current_user
        return authorization.create_authorization_response(grant_user=grant_user)
            
    try:
        grant = authorization.get_consent_grant(end_user=current_user)
        return render_template('authorize.html', grant=grant) #, 200, {'X-Frame-Options': 'DENY'}
    except OAuth2Error as error:
        return error.get_body() , error.status_code

@app.route('/oauth/token', methods=['POST'])
def token():
    return authorization.create_token_response()


@app.route('/api/profile')
@require_oauth('profile')
def api_profile():
    user = current_token.user
    return jsonify(id=user.id, username=user.username)

