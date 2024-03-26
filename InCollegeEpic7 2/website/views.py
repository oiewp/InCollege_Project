from flask import Blueprint, flash, render_template, request, jsonify
from flask_login import login_required, current_user
from . import db
from flask import redirect, url_for 
from .models import JobApplication, Message, SavedJob, User, Friend, Job, Experience, Education
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

    if current_user.message_notification:
        flash('You have a new message.', category='info')
        current_user.message_notification = False
        db.session.commit()

    return render_template("home.html", user=current_user)

@views.route('/job-search', methods=['GET', 'POST'])
@login_required
def job_search():
    if (current_user.notified_job_deletion):
        flash('A job you applied to has been deleted.', category='info')
        current_user.notified_job_deletion = False
        db.session.commit()
    return render_template("job_search.html", user=current_user)

@views.route('/job-network', methods=['GET'])
@login_required
def job_network():
    jobs = Job.query.all()
    job_list = []
    for job in jobs:
        is_poster = job.accountName == current_user.accountName
        has_applied = JobApplication.query.filter_by(user_id=current_user.id, job_id=job.id).first() is not None
        is_saved = SavedJob.query.filter_by(user_id=current_user.id, job_id=job.id).first() is not None
        job_info = {
            'job_id': job.id,
            'job_title': job.title,
            'is_poster': is_poster,
            'is_saved': is_saved,
            'has_applied': has_applied
        }
        job_list.append(job_info)
    return jsonify(job_list)

@views.route('/job-list', methods=['GET'])
@login_required
def job_list():
    return render_template("job_list.html", user=current_user)

@views.route('/view-job', methods=['GET'])
@login_required
def view_job():
    job_id = request.args.get('job_id')  # Get the selected job_id from the query parameters
    job = Job.query.filter_by(id=job_id).first()  # Filter the job by the selected job_id
    if job:
        job_data = {
            'job_title': job.title,
            'job_description': job.description,
            'employer': job.employer,
            'location': job.location,
            'salary': job.salary
            # Add other job fields as needed
        }
        return render_template("view_job.html", job_data=job_data, user = current_user)
    else:
        flash('Job not found.', category='error')
        return redirect(url_for('views.job_search'))
    
@views.route('/job-apply/<int:job_id>', methods=['GET', 'POST'])
def job_apply(job_id):
    
    # Check if the user has already applied for this job
    existing_application = JobApplication.query.filter_by(user_id=current_user.id, job_id=job_id).first()

    if existing_application:
        flash('You have already applied for this job.', category='info')
        return redirect(url_for('views.job_list'))  # Redirect them away or to the job list
    
    if request.method == 'POST':
        # Assuming job_id is passed as a hidden input in the form
        job_id = request.form.get('job_id')
        graduationDate = request.form.get('graduationDate')
        startDate = request.form.get('startDate')
        coverLetter = request.form.get('coverLetter')
    
        new_apply = JobApplication(
            user_id=current_user.id,
            job_id=job_id,
            graduation_date=graduationDate,
            start_date=startDate,
            cover_letter=coverLetter
        )
        db.session.add(new_apply)
        db.session.commit()
        flash('Application completed!', category='success')
        return redirect(url_for('views.job_list', job_id=job_id))
    return render_template("job_apply.html", job_id=job_id, user=current_user)  # Ensure 'views.job_list' is the correct endpoint

@views.route('/applied-jobs', methods=['GET'])
@login_required
def job_applied():
    return render_template("applied_jobs.html", user=current_user)

@views.route('/not-applied-jobs', methods=['GET'])
@login_required
def job_not_applied():
    return render_template("not_applied_jobs.html", user=current_user)

@views.route('/saved-jobs', methods=['GET'])
@login_required
def saved_jobs():
    return render_template("saved_jobs.html", user=current_user)

@views.route('/save-job/<int:job_id>', methods=['POST'])
@login_required
def save_job(job_id):
    # Check if the job is already saved
    if not SavedJob.query.filter_by(user_id=current_user.id, job_id=job_id).first():
        saved_job = SavedJob(user_id=current_user.id, job_id=job_id)
        db.session.add(saved_job)
        db.session.commit()
        flash('Job saved successfully.', 'success')
    else:
        flash('Job is already saved.', 'info')
    return redirect(url_for('views.job_list'))

@views.route('/unsave-job/<int:job_id>', methods=['DELETE'])
@login_required
def unsave_job(job_id):
    saved_job = SavedJob.query.filter_by(user_id=current_user.id, job_id=job_id).first()
    if saved_job:
        db.session.delete(saved_job)
        db.session.commit()
        return jsonify({'message': 'Job unsaved successfully.'}), 200
    else:
        return jsonify({'error': 'Job not found or not saved.'}), 404


@views.route('/delete-job/<int:job_id>', methods=['DELETE'])
@login_required
def delete_job(job_id):
    job = Job.query.get_or_404(job_id)
    if job.accountName != current_user.accountName:
        # If the current user is not the poster of the job, deny the deletion
        response = jsonify({"error": "Unauthorized to delete this job."})
        response.status_code = 403  # Forbidden
        return response
    
    applications = JobApplication.query.filter_by(job_id=job_id).all()
    for application in applications:
        user = User.query.get(application.user_id)
        # Check if the user is not the job owner before setting the notification flag
        if user.accountName != job.accountName:
            user.notified_job_deletion = True
    db.session.commit()

    db.session.delete(job)
    db.session.commit()
    flash('Job deleted successfully.', 'success')
    return jsonify({"success": "Job deleted successfully."})


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

# search by university route
@views.route('/search-uni', methods=['GET', 'POST'])
def search_uni():
    match_found = False
    # Use a list of tuples or a list of dictionaries to track both the user and their friendship status
    matching_users_with_status = []

    if request.method == 'POST':
        university = (request.form.get('university')).title()
        
        # Example using a simple query to fetch matching users
        matching_users = User.query.filter(User.university == university).all()

        # Iterate over matching users to check friendship status
        for user in matching_users:
            # Assume a function or query here that checks if current_user is friends with 'user'
            is_friend = check_if_friends(current_user.accountName, user.accountName)  # You need to implement this check based on your database schema
            
            # Append both user and friendship status
            matching_users_with_status.append((user, is_friend))

        if not matching_users:
            flash('No users with a matching university were found.', category='error')
        else:
            flash(f'Users from {university} found!', category='success')
            match_found = True

    return render_template("search_uni.html", matching_users=matching_users_with_status, user=current_user, match_found=match_found)

# search by major route
@views.route('/search-major', methods=['GET', 'POST'])
def search_major():
    match_found = False
    # Use a list of tuples or a list of dictionaries to track both the user and their friendship status
    matching_users_with_status = []

    if request.method == 'POST':
        major = (request.form.get('major')).title()
        
        # Example using a simple query to fetch matching users
        matching_users = User.query.filter(User.major == major).all()

        # Iterate over matching users to check friendship status
        for user in matching_users:
            # Assume a function or query here that checks if current_user is friends with 'user'
            is_friend = check_if_friends(current_user.accountName, user.accountName)  # You need to implement this check based on your database schema
            
            # Append both user and friendship status
            matching_users_with_status.append((user, is_friend))

        if not matching_users:
            flash('No users with a matching major were found.', category='error')
        else:
            flash(f'Users with the major {major} found!', category='success')
            match_found = True

    return render_template("search_major.html", matching_users=matching_users_with_status, user=current_user, match_found=match_found)

@views.route('/friend-list', methods=['GET', 'POST'])
def friend_list():
    return render_template("friend_list.html", user=current_user)

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
    for friend in friends:
        print(friend.friend)
    friends = [
        {
            'friend_id': User.query.filter_by(accountName=friend.friend).first().id,
            'friend_fname': User.query.filter_by(accountName=friend.friend).first().fname,
            'friend_lname': User.query.filter_by(accountName=friend.friend).first().lname,
            'user_name': friend.user,
            'friend_user_name': friend.friend
        }
        for friend in friends
    ]
    print(current_user.tier)
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


@views.route('/create_profile', methods=['GET', 'POST'])
@login_required
def create_profile():

    profile_data = {
        'title': current_user.title,
        'major': current_user.major,
        'university': current_user.university,
        'about': current_user.about
    }

    schoolName = ""   # Fetch schoolName data from wherever it's stored
    degree = ""       # Fetch degree data from wherever it's stored
    years = ""        # Fetch years attended data from wherever it's stored

    # Fetch the user's experience and education if it exists
    experience = Experience.query.filter_by(user=current_user.accountName).all()
    numSaved = len(experience)
    total_experiences = numSaved

    education = Education.query.filter_by(user=current_user.accountName).first()

    if request.method == 'POST':
        title = request.form.get('title')
        major = (request.form.get('major')).title()
        university = (request.form.get('university')).title()
        about = request.form.get('about')

        experiences = []
        # Limit the loop to iterate only three times

        current_user.hasExp = True
        for i in range(1, 4):
            jobTitle = request.form.get(f'jobTitle_{i}')
            jobEmployer = request.form.get(f'jobEmployer_{i}')
            dateStart = request.form.get(f'dateStart_{i}')
            dateEnd = request.form.get(f'dateEnd_{i}')
            jobLocation = request.form.get(f'jobLocation_{i}')
            jobDescription = request.form.get(f'jobDescription_{i}')

            if i <= numSaved:
                experience[i-1].jobTitle = jobTitle
                experience[i-1].jobEmployer = jobEmployer
                experience[i-1].dateStart = dateStart
                experience[i-1].dateEnd = dateEnd
                experience[i-1].jobLocation = jobLocation
                experience[i-1].jobDescription = jobDescription
            # Only add experience if at least one variable is provided
            else:
                if (jobTitle or jobEmployer or dateStart or dateEnd or jobLocation or jobDescription) and (total_experiences < 3):
                    experiences.append(Experience(user=current_user.accountName, jobTitle=jobTitle, jobEmployer=jobEmployer, dateStart=dateStart, dateEnd=dateEnd, jobLocation=jobLocation, jobDescription=jobDescription))
                    total_experiences += 1

        schoolName = request.form.get('schoolName')
        degree = request.form.get('degree')
        years = request.form.get('years')

        current_user.title = title
        current_user.major = major
        current_user.university = university
        current_user.about = about

        # set hasInfo as false if any variables have not been set to True
        if current_user.title and current_user.major and current_user.university and current_user.about:
            current_user.hasInfo = True
        else:
            current_user.hasInfo = False

        for exp in experiences:
            db.session.add(exp)

        # If education entry already exists, update it
        if education:
            education.schoolName = schoolName
            education.degree = degree
            education.years = years
        else:
            newEdu = Education(user=current_user.accountName, schoolName=schoolName, degree=degree, years=years)
            current_user.hasEdu = True
            db.session.add(newEdu)

        if schoolName and degree and years:
            current_user.hasEdu = True
        else:
            current_user.hasEdu = False

        if current_user.hasEdu and current_user.hasInfo and current_user.hasExp:
            current_user.hasProfile = True
        else:
            current_user.hasProfile = False

        try:
            db.session.commit()
            flash('Your profile has been updated.', 'success')
        except:
            db.session.rollback()
            flash('An error occurred. Please try again.', 'error')
    return render_template("create_profile.html", user=current_user, profile_data=profile_data, numSaved=numSaved, experiences=experience, education=education)


@views.route('/view_profile', methods=['GET'])
@login_required
def view_profile():
    user = current_user
    if user.hasProfile:  
        # Check if essential profile fields are filled
        profile_data = {
            
            'title': user.title,
            'major': user.major,
            'university': user.university,
            'about': user.about
            # Add other profile fields as needed
        }
        experiences = Experience.query.filter_by(user=user.accountName).all()
        educations = Education.query.filter_by(user=user.accountName).all()
        return render_template("view_profile.html", user=user, profile_data=profile_data, experiences=experiences, educations=educations)
    else:
        flash('Profile is not complete. Please fill in all required fields.', 'error')
        return redirect(url_for('views.create_profile'))


@views.route('/view_friend_profile', methods=['GET'])
@login_required
def view_friend_profile():
    # Retrieve friend_user_name from query parameters instead of JSON body
    friendName = request.args.get('friend_user_name')

    if not friendName:
        flash("No friend username provided.", "error")
        # Redirect or render a template as necessary
        return render_template("some_error_template.html", user=current_user)

    friend = User.query.filter_by(accountName=friendName).first()

    if friend is None:
        flash("Friend not found.", "error")
        # Redirect or render a template as necessary
        return render_template("some_error_template.html", user=current_user)

    # Initialize empty structures in case friend.hasProfile is False
    profile_data = {}
    experiences = []
    educations = []

    if friend.hasProfile:
        # Check if essential profile fields are filled
        profile_data = {
            'title': friend.title,
            'major': friend.major,
            'university': friend.university,
            'about': friend.about
        }
        experiences = Experience.query.filter_by(user=friend.accountName).all()
        educations = Education.query.filter_by(user=friend.accountName).all()
        return render_template("view_friend_profile.html", user=current_user, friend=friend, profile_data=profile_data, experiences=experiences, educations=educations)
    else:
        flash('This friend has not set up a profile yet. Please try again later.', 'error')
        return redirect(url_for('views.friend_list'))
        

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

# language route
@views.route('/messaging', methods=['GET', 'POST'])
@login_required
def messaging():
    return render_template("messaging.html", user=current_user)

@views.route('/my-inbox', methods=['GET'])
@login_required
def my_inbox():
    # get all the friends of the current user
    account_id = current_user.id
    messages = Message.query.filter_by(receiver_id=account_id).all()
    messages = [
        {
            'id': message.id,
            'sender_name': message.sender.fname + " " + message.sender.lname,
            'header': message.header
        }
        for message in messages
    ]
    return jsonify(messages)

@views.route('/list-users', methods=['GET'])
@login_required
def list_users():
    users = User.query.filter(User.id != current_user.id).all()
    users = [
        {
            'id': user.id,
            'fname': user.fname,
            'lname': user.lname
        }
        for user in users
    ]
    return jsonify(users)

@views.route('/delete-message/<int:message_id>', methods=['DELETE'])
@login_required
def delete_message(message_id):
    message = Message.query.get_or_404(message_id)
    db.session.delete(message)
    db.session.commit()
    flash('Message deleted successfully.', 'success')
    return jsonify({"success": "Message deleted successfully."})

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



