from flask import Blueprint, flash, render_template, request, jsonify
from flask_login import login_required, current_user
from . import db
from flask import redirect, url_for 
from .models import User, Friend, Job
from sqlalchemy import and_, func

views = Blueprint('views', __name__)

@views.route('/', methods=['GET', 'POST'])
def front_page():
  return render_template("front_page.html", user=current_user)

@views.route('/incollege-video', methods=['GET', 'POST'])
def incollege_video():
  flash('Video is playing.', category='success')
  return render_template("incollege_video.html", user=current_user)

# help-center route
@views.route('/help-center', methods=['GET', 'POST'])
def help_center():
  return render_template("help_center.html", user=current_user)

# about route
@views.route('/about', methods=['GET', 'POST'])
def about():
  return render_template("about.html", user=current_user)


# Links below will require the user to be logged in to access them
@views.route('/home', methods=['GET', 'POST'])
@login_required
def home():
    account_name = current_user.accountName
    pending_requests = Friend.query.filter_by(friend=account_name, status='pending').all()
    if pending_requests:
       flash(f"You have {len(pending_requests)} pending friend request(s).", category='success')

    return render_template("home.html", user=current_user)

@views.route('/job-search', methods=['GET', 'POST'])
@login_required
def job_search():
  return render_template("job_search.html", user=current_user)

# Accessibility route
@views.route('/accessibility', methods=['GET', 'POST'])
def accessibility():
    return render_template("accessibility.html", user=current_user)


# function 
def check_if_friends(user_id, friend_id):
    # Logic to check if user_id and friend_id are friends
    # Assume a query to the Friend table to check if the friendship exists

    # if the status is 'accepted' or 'pending', then the users are friends
    friendship = Friend.query.filter(
        (Friend.user == user_id) & (Friend.friend == friend_id) |
        (Friend.user == friend_id) & (Friend.friend == user_id)
    ).filter(Friend.status.in_(['accepted', 'pending'])).first()

    print(friendship)

    return friendship is not None


@views.route('/finder', methods=['GET', 'POST'])
@login_required
def finder():
    match_found = False
    # Use a list of tuples or a list of dictionaries to track both the user and their friendship status
    matching_users_with_status = []

    if request.method == 'POST':
        lname = request.form.get('lname')
        
        # Example using a simple query to fetch matching users
        matching_users = User.query.filter(func.lower(User.lname) == func.lower(lname)).all()

        # Iterate over matching users to check friendship status
        for user in matching_users:
            # Assume a function or query here that checks if current_user is friends with 'user'
            is_friend = check_if_friends(current_user.accountName, user.accountName)  # You need to implement this check based on your database schema
            
            # Append both user and friendship status
            matching_users_with_status.append((user, is_friend))

        if not matching_users:
            flash('No users with a matching last name were found.', category='error')
        else:
            flash(f'Users with the last name {lname} found!', category='success')
            match_found = True

    return render_template("finder.html", matching_users=matching_users_with_status, user=current_user, match_found=match_found)

# Toan's code


# pending friend requests route
@views.route('/pending-friend-requests', methods=['GET'])
@login_required
def pending_friend_requests():
    
    # logic to get the pending friend requests for the current user

    # go to the friend table and get all the pending requests for the current user

    # first, get the current user's account name
    account_name = current_user.accountName

    # then, go to the Friend table and get all the pending requests for the current user
    pending_requests = Friend.query.filter_by(friend=account_name, status='pending').all()

    # Convert the pending requests to a list of dictionaries
    pending_requests = [
        {
            'user_name': request.user,
            'friend_user_name': request.friend
        }
        for request in pending_requests
    ]
  
    # Return the pending requests as JSON
    return jsonify(pending_requests)

# my-network route epic
@views.route('/my-network', methods=['GET'])
@login_required
def my_network():
    # get all the friends of the current user
    account_name = current_user.accountName
    friends = Friend.query.filter_by(user=account_name, status='accepted').all()
    friends = [
        {
            'user_name': friend.user,
            'friend_user_name': friend.friend
        }
        for friend in friends
    ]
    return jsonify(friends)


# add friend route
@views.route('/add-friend', methods=['POST'])
@login_required
def add_friend():
    # Extract the friend's account name from the request body
    friend_account_name = request.json.get('friend_account_name', '').strip()

    # Get the current user's account name
    account_name = current_user.accountName

    # Prevent adding oneself as a friend
    if friend_account_name == account_name:
        return jsonify({'error': 'You cannot add yourself as a friend.'}), 400

    # Ensure the friend_account_name is not empty
    if not friend_account_name:
        return jsonify({'error': 'Friend account name is required.'}), 400

    # Check if the friend's account name exists in the User table
    friend = User.query.filter_by(accountName=friend_account_name).first()
    if not friend:
        return jsonify({'error': 'Friend account does not exist.'}), 404

    # Check if the friend connection already exists (either way)
    existing_connection = Friend.query.filter(
        (Friend.user == account_name) & (Friend.friend == friend_account_name) |
        (Friend.user == friend_account_name) & (Friend.friend == account_name)
    ).first()
    if existing_connection:
        return jsonify({'error': 'Friend request already sent or connection already exists.'}), 400

    try:
        # Create a new friend connection
        new_friend_connection = Friend(user=account_name, friend=friend_account_name, status='pending')  # Assuming a 'status' field for friend requests

        # Add the new friend connection to the database
        db.session.add(new_friend_connection)

        # Commit the changes to the database
        db.session.commit()

        # Return a success message
        return jsonify({'message': 'Friend request sent successfully.'}), 200
    except Exception as e:
        # Log the exception e if needed
        db.session.rollback()  # Rollback in case of error
        return jsonify({'error': 'An error occurred while sending friend request.'}), 500



# Friend Request Endpoint
@views.route('/accept-friend-request', methods=['POST'])
@login_required
def accept_friend_request():
    user_name = request.json.get('user_name')
    friend_user_name = request.json.get('friend_user_name')
    
    
    # Logic to accept the friend request based on user names

    # go to the Friend table and update the status of the friend request to 'accepted'
    friend_request = Friend.query.filter_by(user=user_name, friend=friend_user_name).first()
    friend_request.status = 'accepted'
    
    # also, make the connection the other way. Add this row since this row is not in the table
    new_friend_connection = Friend(user=friend_user_name, friend=user_name, status='accepted')
    db.session.add(new_friend_connection)
    db.session.commit()
    
    print(user_name, friend_user_name)

    return jsonify({
            'message': 'Friend request accepted',
            'user_name': user_name,
            'friend_user_name': friend_user_name
        }), 200

# Delete Friend Request Endpoint
@views.route('/delete-friend-request', methods=['POST'])
@login_required
def delete_friend_request():
    request_id = request.json.get('request_id')
    # Logic to find and delete the friend request
    # Assume request_id is enough to find the request
    user_name = request.json.get('user_name')
    friend_user_name = request.json.get('friend_user_name')

    # go to the Friend table and delete the friend request
    friend_request = Friend.query.filter_by(user=user_name, friend=friend_user_name).first()
    db.session.delete(friend_request)

    # also, delete the connection the other way. But only if it exists
    friend_request = Friend.query.filter_by(user=friend_user_name, friend=user_name).first()
    if friend_request:
        db.session.delete(friend_request)
    db.session.commit()


    return jsonify({
            'message': 'Friend request deleted',
            'user_name': user_name,
            'friend_user_name': friend_user_name
        }), 200

@views.route('/remove-friend', methods=['POST'])
@login_required
def remove_friend():
    user_name = request.json.get('user_name')  # The username of the user initiating the removal
    friend_user_name = request.json.get('friend_user_name')  # The username of the friend to be removed

    # Find the friend connection in the Friend table and delete it
    friend_connection = Friend.query.filter_by(user=user_name, friend=friend_user_name).first()
    if friend_connection:
        db.session.delete(friend_connection)
        db.session.commit()
        message = 'Friend removed successfully'
    else:
        # If no connection found, perhaps they're not friends or wrong username provided
        message = 'Friend connection not found'

    # Attempt to find and delete the reciprocal connection, if it exists
    reciprocal_connection = Friend.query.filter_by(user=friend_user_name, friend=user_name).first()
    if reciprocal_connection:
        db.session.delete(reciprocal_connection)
        db.session.commit()

    return jsonify({
        'message': message,
        'user_name': user_name,
        'friend_user_name': friend_user_name
    }), 200







@views.route('/skills', methods=['GET', 'POST'])
@login_required
def skills():
  return render_template("skill.html", user=current_user)

@views.route('/skills/<int:skill_id>', methods=['GET'])
@login_required
def learn_skill(skill_id):
    skills = {
      1: {'name': 'Programming Languages'},
      2: {'name': 'Graphic Design'},
      3: {'name': 'Digital Marketing'},
      4: {'name': 'Data Analysis and Visualization'},
      5: {'name': 'Public Speaking and Presentation'}
    }

    skill = skills.get(skill_id)
    if skill:
        return render_template("skill_details.html", user=current_user, skill=skill)
    else:
        return redirect(url_for('views.home'))

# privacy-policy route

@views.route('/privacy-policy', methods=['GET', 'POST'])
@login_required
def privacy_policy():
    if request.method == 'POST':
        # Extract form data and update current_user's settings
        current_user.email_option = 'emailOption' in request.form
        current_user.sms_option = 'smsOption' in request.form
        current_user.advertising_option = 'advertisingOption' in request.form

        try:
            db.session.commit()
            flash('Your settings have been updated.', 'success')
        except:
            db.session.rollback()
            flash('An error occurred. Please try again.', 'error')
        return redirect(url_for('views.privacy_policy'))

    return render_template("privacy_policy.html", user=current_user)

# Copyright Policy route
@views.route('/copyright-policy', methods=['GET', 'POST'])
def copyright_policy():
    return render_template("copyright_policy.html", user=current_user)

# User Agreement route
@views.route('/user-agreement', methods=['GET', 'POST'])
def user_agreement():
    return render_template("user_agreement.html", user=current_user)

# copyright notice route
@views.route('/copyright-notice', methods=['GET', 'POST'])
def copyright():
  return render_template("notice.html", user=current_user)

# Cookie Policy and Settings route
@views.route('/cookie-policy', methods=['GET', 'POST'])
def cookie_policy():
    return render_template("cookie_policy.html", user=current_user)

# Brand Policy route
@views.route('/brand-policy', methods=['GET', 'POST'])
def brand_policy():
    return render_template("brand_policy.html", user=current_user)

# language route
@views.route('/languages', methods=['GET', 'POST'])
@login_required
def language():
    if request.method == 'POST':
        # Extract form data
        selected_language = request.form.get('language')

        # Update current_user's settings
        current_user.language = selected_language

        try:
            # Save to database
            db.session.commit()
            flash('Your language settings have been updated.', 'success')
        except Exception as e:
            db.session.rollback()
            flash('An error occurred. Please try again.', 'error')
        return redirect(url_for('views.language'))

    # No need to modify anything here for GET request handling
    # Just ensure the current language is passed to the template
    return render_template("language.html", user=current_user)


#################################################################
#                       UNDER CONSTRUCTION                      #
#################################################################


# press route
@views.route('/press', methods=['GET', 'POST'])
def press():
  return render_template("press.html", user=current_user)

# blog route
@views.route('/blog', methods=['GET', 'POST'])
def blog():
  return render_template("under_construction.html", user=current_user)

# careers
@views.route('/careers', methods=['GET', 'POST'])
def careers():
  return render_template("under_construction.html", user=current_user)

# developers route
@views.route('/developers', methods=['GET', 'POST'])
def developers():
  return render_template("under_construction.html", user=current_user)

# browse incollege route
@views.route('/browse-incollege', methods=['GET', 'POST'])
def browse():
  return render_template("under_construction.html", user=current_user)

# business solution route
@views.route('/business-solutions', methods=['GET', 'POST'])
def business():
  return render_template("under_construction.html", user=current_user)

# directories route
@views.route('/directories', methods=['GET', 'POST'])
def directories():
  return render_template("under_construction.html", user=current_user)

# search by university route
@views.route('/search-by-uni', methods=['GET', 'POST'])
def search_uni():
   return render_template("under_construction.html", user=current_user)

# search by major route
@views.route('/search-by-major', methods=['GET', 'POST'])
def search_major():
   return render_template("under_construction.html", user=current_user)

