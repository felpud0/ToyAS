from flask import Flask, render_template, url_for, request
from models import db, User


def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'secret!'
    return app

def setup_app(app):
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'
    db.init_app(app)
    with app.app_context():
        db.create_all()

app = create_app()


@app.route('/')
def index():
    return 'Hello, World!'

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
    return "Logged in successfully"+str(user.username), 200

if __name__ == '__main__':
    setup_app(app)
    app.run(debug=True)