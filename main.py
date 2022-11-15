from flask import Flask, render_template, redirect, session, flash, request, url_for
from flask_socketio import SocketIO, join_room
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SECRET_KEY'] = 'key'
socketio = SocketIO(app)

# cconfiguring the database
db = SQLAlchemy()
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///server.db'
db.init_app(app)

# Tables in the database
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String)
    password = db.Column(db.String)
    visitedchatrooms = db.Column(db.String)

class Chatroom(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)

class Chatlogs(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    chatroom = db.Column(db.String)
    user = db.Column(db.String)
    message = db.Column(db.String)

# Creates the tables and the database file if it doesn't exist already
with app.app_context():
    db.create_all()

# this this is used in the function below to get the current url the user is on
currenturl = []

# this function is used to direct a user back to the page they were originally on if they click a link they can't access yet
def get_cur_url(new):
    if currenturl:
        currenturl.pop()
    currenturl.append(new)

# if you are in the session it redirects you to userpage
# if you are not then it redirects you to the login page
@app.route('/')
def redirectlogin():
    if 'user' in session:
        return redirect('/userpage')
    else:
        return redirect('/Login')

# login page
@app.route('/Login', methods=['POST', 'GET'])
def login():
    # see if the user is in session and if they are send them to the page they were on before
    if 'user' in session:
        flash('can\'t visit login page while signed in', 'info')
        return redirect(currenturl[0])
    # get the current url
    get_cur_url('/Login')

    if request.method == 'POST':
        # see if the user exist in the database
        userexist = db.session.query(db.session.query(User).filter_by(username=request.form['user'], password= request.form['pass']).exists()).scalar()
        print(userexist)

        # if they do put them in the session and redirect them to the userpage
        if userexist:
            session['user'] = request.form['user']
            return redirect('/userpage')

        else:
            # if that doesn't work flash them a message telling them they put something in wrong
            flash('incorrect username or password', 'info')
            return render_template('login.html')
    
    return render_template('login.html')

# signup page
@app.route('/Signup', methods=['POST', 'GET'])
def signup():
    # redirects the user back if they are already signed in
    if 'user' in session:
        flash('can\'t visit signup page while signed in', 'info')
        return redirect(currenturl[0])

    # get the current url
    get_cur_url('/Signup')

    if request.method == 'POST':
        # seeing if that username entered already exist in the database
        userexist = db.session.query(db.session.query(User).filter_by(username=request.form['user']).exists()).scalar()
        # if it does flash a message saying so
        if userexist:
            flash('username already exist', 'info')
            return render_template('signup.html')

        # if the username entered too short tell them it has to be longer
        elif len(request.form['user']) < 4:
            flash('username too short, has to be longer than 3 charecters', 'info')
            return render_template('signup.html')

        # if the passwords match to create the user
        elif request.form['pass'] == request.form['repass']:
            # see if the password length is too short
            if len(request.form['pass']) > 3:
                session['user'] = request.form['user']
                user = User(username = request.form['user'], password = request.form['pass'], visitedchatrooms = '')
                db.session.add(user)
                db.session.commit()
                return redirect('/userpage')
            # if it is too short then flash a message
            else:
                flash('password is too short, it has to be greater than 3 charecters', 'warning')
                return render_template('signup.html')
        else:
            # if they didn't retype it correctly flash a message telling them so
            flash('Passwords did not match', 'info')
            return render_template('signup.html')
    
    return render_template('signup.html')

# logout page
@app.route('/Logout')
def logout():
    # if there is a user in session log them out
    if 'user' in session:
        # tell them it worked
        flash('logout successful', 'info')
        # take them out of the session
        session.pop('user', None)
        return redirect('/Login')
    # if there is no user in session tell them they have to be signed in to logout
    else:
        if currenturl:
            flash('have to be signed in to log out', 'info')
            return redirect(currenturl[0])
        # if they don't have a current url because they accessed it in the search bar suggestions not having this else would give them a error
        else:
            # put them on the login page if they don't have a cur url
            return redirect('/Login')

# userpage
@app.route('/userpage', methods=['POST', 'GET'])
def user():
    # if there is no user in session redirect them back
    if not 'user' in session:
        flash('can\'t visit your page yet until you log in', 'info')
        return redirect(currenturl[0])

    # get the url
    get_cur_url('/userpage')

    # pull from the database the user and get all the chatrooms they have visited
    user = User.query.filter_by(username=session['user']).first()
    userchatrooms = user.visitedchatrooms.split(',')

    # this is here so the statement won't run possitive in future if statements
    if userchatrooms == ['']:
        userchatrooms = None

    if request.method == 'POST':
        # to identify which form they submited on
        form_name = request.form['form_name']

        # if its this from send them to the chatrooms with the name they selected
        if form_name == 'chatselect':
            return redirect(url_for('make_chatroom', chatroom = request.form.get('Userchats')))

        # if it not then make a chatroom
        else:
            # names can't contain a comma and flash a message if it does
            if request.form['make_chatroom_name'].__contains__(','):
                flash('name can\'t contain a comma', 'info')

            else:
                # see if the name already exist
                chatroomexist = db.session.query(db.session.query(Chatroom).filter_by(name=request.form['make_chatroom_name']).exists()).scalar()
                # if it doesn't add it toe the list of visited chatrooms as well as create it
                if not chatroomexist:
                    if userchatrooms:
                        user.visitedchatrooms = user.visitedchatrooms + ',' + request.form['make_chatroom_name']
                        userchatrooms.append(request.form['make_chatroom_name'])
                    else:
                        # if it was added with a comma before then a blank space would fill the first position
                        user.visitedchatrooms += request.form['make_chatroom_name']
                        userchatrooms = [request.form['make_chatroom_name']]
                    chatroom = Chatroom(name = request.form['make_chatroom_name'])
                    db.session.add(chatroom)
                    db.session.commit()
                    return render_template('user.html', userchatrooms = userchatrooms)
                # give this if the chatroom name exist
                else:
                    flash('that chatroom name already exist', 'warning')
                    return render_template('user.html', userchatrooms = userchatrooms)

    return render_template('user.html', userchatrooms = userchatrooms)

# all convos page
@app.route('/allconvos', methods=['POST', 'GET'])
def allconvos():
    # if user isn't a user in session send them back to the page they were on
    if not 'user' in session:
        flash('can\'t visit all conversations yet until you log in', 'info')
        return redirect(currenturl[0])

    # get the current url
    get_cur_url('/allconvos')

    # get the user and all the chatrooms that exist
    user = User.query.filter_by(username = session['user']).first()
    allchatrooms = Chatroom.query.order_by(Chatroom.name).all()

    # have all the chatroom names in the list insead of chatroom objects that are given above
    for index, i in enumerate(allchatrooms):
        allchatrooms[index] = i.name

    if request.method == 'POST':
        # see the form that was selected
        form_name = request.form['form_name']

        # if it was chatselect send them to that room
        if form_name == 'chatselect':
            # if the selected room is not in the user's visited chatrooms then add it in
            if not user.visitedchatrooms.__contains__(request.form.get('Userchats')):
                if user.visitedchatrooms:
                    user.visitedchatrooms = user.visitedchatrooms + ',' + request.form.get('Userchats')
                else:
                    user.visitedchatrooms += request.form.get('Userchats')
                db.session.commit()
            return redirect(url_for('make_chatroom', chatroom = request.form.get('Userchats')))
        else:
            # chatroom name can't contain a comma
            if request.form['make_chatroom_name'].__contains__(','):
                flash('name can\'t contain a comma', 'info')
            else:
                # see if the chatroom exist
                chatroomexist = db.session.query(db.session.query(Chatroom).filter_by(name=request.form['make_chatroom_name']).exists()).scalar()
                # if it doesn't then make it
                if not chatroomexist:
                    if user.visitedchatrooms:
                        user.visitedchatrooms = user.visitedchatrooms + ',' + request.form['make_chatroom_name']
                    else:
                        # if it is the first user visited chatroom it has to be entered without the comma at the start
                        user.visitedchatrooms += request.form['make_chatroom_name']
                    chatroom = Chatroom(name = request.form['make_chatroom_name'])
                    db.session.add(chatroom)
                    db.session.commit()
                    allchatrooms.append(request.form['make_chatroom_name'])
                    return render_template('allconvos.html', chatrooms = allchatrooms)
                else:
                    # flash this if the name entered already exist
                    flash('that chatroom name already exist', 'warning')
                    return render_template('allconvos.html', chatrooms = allchatrooms)

    return render_template('allconvos.html', chatrooms = allchatrooms)

# when a chatroom is first entered make a announcement
@socketio.on('join_room')
def handle_join_room(data):
    join_room(data['room'])
    # make it appear for others in that room
    socketio.emit('join_room_announcement', data, room=data['room'])

# send the message 
@socketio.on('send_message')
def handle_send_message(data):
    #make the message appear for others in the room
    socketio.emit('receive_message', data, room=data['room'])
    # add message to database
    mes = Chatlogs(chatroom = data['room'], user = data['user'], message = data['message'])
    db.session.add(mes)
    db.session.commit()

# chatroom page (custom url)
@app.route('/userpage/<chatroom>', methods=['POST', 'GET'])
def make_chatroom(chatroom):
    # get the page's url
    get_cur_url('/userpage/' + chatroom)
    # get the existing logs for the chatroom 
    chatroomlogs = Chatlogs.query.filter_by(chatroom = chatroom).all()
    return render_template('chatroom.html', chatroom = chatroom, logs = chatroomlogs, user = session['user'])

if __name__ == '__main__':
    socketio.run(app)