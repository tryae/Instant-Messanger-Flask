# About
This is a flask based web application that uses flask-SocketIO, flask-SQLalchemy and bootstrap to send messages online, keep in mind this code is not for commercial use. It has 4 main pages (login, signup, userpage, all conversations) and a logout link next to them in the navbar.
# Instructions
To create a user go to the signup page and after you submit it will take you to the userpage were you can see all that charooms the created user has visited. The user can select a chatroom and be transfered or create a new chatroom. You can also visit the all conversations page and see all chatrooms that exist created by any user outside of what you visited and select them as well as create a new room on that page as well. when you enter a room you can send messages that will be received instantly by any one else in the room.

# Requirements
To run the program you need to have flask, flask-socketio, flask-sqlachemy installed and if you don't already you can copy and paste these into command prompt to get it.
- pip install flask
- pip install flask-sqlalchemy
- pip install flask-socketio

once you have these it will work just fine.

## Notes
 - the userpage and all conversations page can only be accessed when a user has already been created and is currently in the session/logged in and while a user is signed the login and sign up pages can not be accessed until the user signs out.
 - once the code runs it will create a instance folder and inside a server.db file for the users and chatrooms to be stored in.
