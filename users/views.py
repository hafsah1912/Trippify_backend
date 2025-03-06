from django.http import JsonResponse
from pymongo import MongoClient
from django.views.decorators.csrf import csrf_exempt
from django.middleware.csrf import get_token
import json
import bcrypt
import base64
from django.utils.decorators import method_decorator
from django.views import View
from django.contrib.auth.decorators import login_required
from bson.objectid import ObjectId
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.core.mail import send_mail
from django.core.mail import EmailMessage
from django.contrib.auth.models import User
from django.conf import settings
from django.contrib.auth import update_session_auth_hash
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.contrib.auth.hashers import make_password, check_password
from django.views.decorators.http import require_GET,require_POST
from datetime import datetime
from django.core.files.storage import FileSystemStorage
import os

# Connect to MongoDB
client = MongoClient('mongodb://localhost:27017/')

# db = client['hafsah_traveldb']
db = client['Tourism']

# user_collection = db['user']
# collection = db['newtourpackages']
# categories_collection = db['categories']
# wishlist_collection  = db['wishlist']
# cart_collection  = db['cart']
# bookings_collection = db['bookings']

user_collection = db['user']
collection = db['tourpackages']
categories_collection = db['categories']
wishlist_collection  = db['wishlist']
cart_collection  = db['cart']
bookings_collection = db['bookings']
from django.http import JsonResponse
from django.middleware.csrf import get_token

def get_csrf_token(request):
    return JsonResponse({"csrfToken": get_token(request)})

@csrf_exempt
def login(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            username = data.get('username')
            password = data.get('password')

            if not username or not password:
                return JsonResponse({'error': 'Username and password are required'}, status=400)

            user_data = user_collection.find_one({'username': username})
            if user_data and bcrypt.checkpw(password.encode(), user_data['password'].encode()):
                # Prepare user data to send back
                user_info = {
                    'username': user_data['username'],
                    'name': user_data.get('name', ''),
                    'email': user_data.get('email', ''),
                    'area': user_data.get('area', ''),
                    'city': user_data.get('city', ''),
                    'state': user_data.get('state', ''),
                    'country': user_data.get('country', ''),
                    'contact_no': user_data.get('contact_no', ''),
                }
                request.session['user_id'] = str(user_data['_id'])
                encoded_username = base64.b64encode(username.encode('utf-8')).decode('utf-8')
                csrf_token = get_token(request)  # Get the CSRF token

                response = JsonResponse({
                    'message': 'Login successful',
                    'success': True,
                    'redirect': f'/home/{encoded_username}',
                    'user': user_info
                })
                
                response.set_cookie('csrftoken', csrf_token)  # Set CSRF token in the cookies

                return response
            else:
                return JsonResponse({'error': 'Invalid credentials'}, status=401)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=405)
    
@csrf_exempt
@csrf_exempt
def register(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            username = data.get('username')
            password = data.get('password')
            profile_photo = data.get('profile_photo', '')

            # Validate inputs
            if not username or not password:
                return JsonResponse({'error': 'Username and password are required'}, status=400)

            if user_collection.find_one({'username': username}):
                return JsonResponse({'error': 'Username already exists'}, status=400)

            hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
            user_id = user_collection.insert_one({
                'username': username,
                'password': hashed_password,
                'name': '',
                'email': '',
                'area': '',
                'city': '',
                'state': '',
                'country': '',
                'contact_no': '',
                'profile_photo': profile_photo
            }).inserted_id

            # Store user session
            request.session['user_id'] = str(user_id)

            # Encode username
            encoded_username = base64.b64encode(username.encode('utf-8')).decode()

            return JsonResponse({
                'message': 'User registered successfully',
                'redirect': f'/home/{encoded_username}'
            }, status=201)

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON format'}, status=400)
        except Exception as e:
            return JsonResponse({'error': f'Internal server error: {str(e)}'}, status=500)

    return JsonResponse({'error': 'Invalid request method'}, status=405)

# from django.views.decorators.csrf import csrf_exempt
# from django.http import JsonResponse
# import json
# from django.contrib.auth.models import User

# @csrf_exempt  # Disable CSRF for this endpoint (for testing)
# def register(request):
#     if request.method == "POST":
#         try:
#             data = json.loads(request.body)
#             username = data.get("username")
#             password = data.get("password")

#             if not username or not password:
#                 return JsonResponse({"error": "Username and password are required"}, status=400)

#             if User.objects.filter(username=username).exists():
#                 return JsonResponse({"error": "Username already taken"}, status=400)

#             user = User.objects.create_user(username=username, password=password)
#             user.save()

#             return JsonResponse({"message": "User registered successfully"}, status=201)

#         except json.JSONDecodeError:
#             return JsonResponse({"error": "Invalid JSON format"}, status=400)
    
#     return JsonResponse({"error": "Invalid request method"}, status=405)

def change_password(request):
    if request.method == 'POST':
        try:
            # Parse the JSON data from the request
            data = json.loads(request.body)
            username = data.get('username')
            current_password = data.get('current_password')
            new_password = data.get('new_password')
            
            # Find the user by username
            user = user_collection.find_one({'username': username})
            if not user:
                return JsonResponse({'error': 'User not found'}, status=404)
            
            # Verify the current password
            if not bcrypt.checkpw(current_password.encode(), user['password'].encode()):
                return JsonResponse({'error': 'Current password is incorrect'}, status=400)
            
            # Hash the new password
            hashed_password = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
            
            # Update the user's password in the database
            user_collection.update_one(
                {'username': username},
                {'$set': {'password': hashed_password}}
            )
            
            return JsonResponse({'message': 'Password changed successfully'}, status=200)
        
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Invalid request method'}, status=405)

@csrf_exempt
@require_GET
def get_user_details(request, username):
    try:
        user = user_collection.find_one({"username": username},{
             "username": 1,
                "email": 1,
                "contact_number": 1,
                "address": 1,
        })
        if user:
            user_details = {
                "username": user["username"],
                "email": user["email"],
                "contact_number": user["contact_number"],
                "address": user["address"],
            }
            return JsonResponse(user_details, status=200)
        else:
            return JsonResponse({"error": "User not found."}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@csrf_exempt
def get_profile(request):
    if request.method == 'GET':
        username = request.GET.get('username')
        if not username:
            return JsonResponse({'error': 'Username is required'}, status=400)

        try:
            user = user_collection.find_one({'username': username})
            if user:
                user_data = {
                    'username': user.get('username', ''),
                    'name': user.get('name', ''),
                    'email': user.get('email', ''),
                    'area': user.get('area', ''),
                    'city': user.get('city', ''),
                    'state': user.get('state', ''),
                    'country': user.get('country', ''),
                    'contact_no': user.get('contact_no', ''),
                    'profile_photo': user.get('profile_photo', '')  # Include profile photo URL
                }
                return JsonResponse({'user': user_data})
            else:
                return JsonResponse({'error': 'User not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
def update_profile(request):
    if request.method == 'POST':
        try:
            # Handle POST data and files
            data = request.POST
            files = request.FILES

            username = data.get('username')
            updated_data = {
                'name': data.get('name'),
                'email': data.get('email'),
                'area': data.get('area'),
                'city': data.get('city'),
                'state': data.get('state'),
                'country': data.get('country'),
                'contact_no': data.get('contact_no'),
            }

            # Handle file upload
            profile_photo = files.get('profile_photo')
            if profile_photo:
                # Define the storage path in the React app's public folder
                react_app_static_path = os.path.join('D:/SEM_4/tourismmgmt/frontend', 'public', 'static', 'image', 'profilephoto')
                
                # Create the directory if it doesn't exist
                os.makedirs(react_app_static_path, exist_ok=True)
                
                # Save the file to the defined location
                fs = FileSystemStorage(location=react_app_static_path)
                file_name = fs.save(profile_photo.name, profile_photo)
                
                # Get the relative URL to be stored in MongoDB
                file_url = os.path.join(file_name)
                updated_data['profile_photo'] = file_url

            if not username:
                return JsonResponse({'error': 'Username is required'}, status=400)

            # Update the profile in MongoDB
            result = user_collection.update_one({'username': username}, {'$set': updated_data})
            if result.modified_count > 0:
                user = user_collection.find_one({'username': username})
                user_data = {
                    'username': user['username'],
                    'name': user['name'],
                    'email': user['email'],
                    'area': user['area'],
                    'city': user['city'],
                    'state': user['state'],
                    'country': user['country'],
                    'contact_no': user['contact_no'],
                    'profile_photo': user.get('profile_photo', '')
                }
                return JsonResponse({'user': user_data})
            else:
                return JsonResponse({'error': 'User not found or no changes made'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Invalid request method'}, status=405)

@csrf_exempt
@require_POST
def book_package(request):
    try:
        data = json.loads(request.body)
        username = data.get("username")
        package_id = data.get("packageId")
        contact_number = data.get("contactNumber")
        family_members = data.get("familyMembers")

        booking_data = {
            "username": username,
            "package_id": package_id,
            "contact_number": contact_number,
            "family_members": family_members,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Add current date and time
        }

        bookings_collection.insert_one(booking_data)

        return JsonResponse({"message": "Booking successful!"}, status=201)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@csrf_exempt
def get_bookings(request):
    if request.method == 'GET':
        try:
            username = request.GET.get('username')
            if not username:
                return JsonResponse({'error': 'Username is required'}, status=400)

            user = user_collection.find_one({'username': username})
            if not user:
                return JsonResponse({'error': 'User not found'}, status=404)

            user['_id'] = str(user['_id'])  # Convert ObjectId to string

            # Encode username for querying bookings_collection
            encoded_username = base64.b64encode(username.encode('utf-8')).decode('utf-8')

            bookings = bookings_collection.find({'username': encoded_username})
            booking_list = list(bookings)

            for booking in booking_list:
                booking['_id'] = str(booking['_id'])  # Convert ObjectId to string

                # Fetch package details for each booking
                package = collection.find_one({'_id': ObjectId(booking['package_id'])})
                if package:
                    package['_id'] = str(package['_id'])  # Convert ObjectId to string
                    booking['package_details'] = {
                        'title': package['title'],
                        'map_image': package['map_image'],
                        'package_image': package['package_image'],
                        'banner_image': package['banner_image'],
                        'tour_highlights': package['tour_highlights'],
                        'itinerary': package['itinerary'],
                        'price': package['price'],
                        'duration': package['duration'],
                        'type': package['type'],
                        'key': package['key']
                    }

            response_data = {
                'user_details': {
                    'username': user['username'],
                    'email': user.get('email', ''),
                    'name': user.get('name', ''),
                    'contact_no': user.get('contact_no', '')
                },
                'bookings': booking_list
            }

            return JsonResponse(response_data, status=200)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_POST
def add_to_wishlist(request):
    try:
        data = json.loads(request.body)
        username = data.get('username')
        package_id = data.get('pkgId')

        if not username or not package_id:
            return JsonResponse({"error": "Username and package ID are required"}, status=400)

        # Check if the user already has a wishlist
        wishlist = wishlist_collection.find_one({"username": username})

        if wishlist:
            # If the package is already in the wishlist, remove it (toggle functionality)
            if package_id in wishlist["package_ids"]:
                wishlist_collection.update_one(
                    {"username": username},
                    {"$pull": {"package_ids": package_id}}
                )
                return JsonResponse({"message": "Removed from wishlist", "is_in_wishlist": False})
            else:
                wishlist_collection.update_one(
                    {"username": username},
                    {"$push": {"package_ids": package_id}}
                )
                return JsonResponse({"message": "Added to wishlist", "is_in_wishlist": True})
        else:
            # Create a new wishlist for the user
            wishlist_collection.insert_one({
                "username": username,
                "package_ids": [package_id]
            })
            return JsonResponse({"message": "Added to wishlist", "is_in_wishlist": True})

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)
    
@require_GET
def get_wishlist(request):
    try:
        username = request.GET.get('username')
        
        if not username:
            return JsonResponse({"error": "Username is required"}, status=400)

        wishlist = wishlist_collection.find_one({"username": username})
        if wishlist:
            # Convert ObjectId to string for compatibility with the frontend
            package_ids = [ObjectId(pid) for pid in wishlist["package_ids"]]
            packages = list(collection.find({"_id": {"$in": package_ids}}))
            
            # Convert ObjectId fields to strings
            for pkg in packages:
                pkg["_id"] = str(pkg["_id"])
            
            return JsonResponse({"packages": packages}, status=200)
        else:
            return JsonResponse({"packages": []}, status=200)
    
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)
       
@csrf_exempt
@require_POST
def remove_from_wishlist(request):
    try:
        data = json.loads(request.body)
        username = data.get('username')
        package_id = data.get('pkgId')

        if not username or not package_id:
            return JsonResponse({"error": "Username and package ID are required"}, status=400)

        # Remove the package from the wishlist
        wishlist_collection.update_one(
            {"username": username},
            {"$pull": {"package_ids": package_id}}
        )

        return JsonResponse({"message": "Removed from wishlist"}, status=200)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)
    ya 

@require_GET
def get_package_by_id(request, pkg_id):
    if not ObjectId.is_valid(pkg_id):
        return JsonResponse({'error': 'Invalid package ID'}, status=400)
    
    try:
        # Fetch the package by its ID
        package = collection.find_one({"_id": ObjectId(pkg_id)}, {
            '_id': 1,
            'title': 1,
            'package_image': 1,
            'banner_image': 1,
            'routes': 1,
            'tour_highlights': 1,
            'itinerary': 1,
            'images': 1,
            'states': 1,
            'price': 1,
            'reviews': 1,
            'duration': 1,
            'map_image': 1
        })

        if package:
            package_dict = {
                '_id': str(package['_id']),
                'title': package.get('title'),
                'package_image': package.get('package_image'),
                'banner_image': package.get('banner_image'),
                'routes': package.get('routes', []),
                'tour_highlights': package.get('tour_highlights'),
                'itinerary': package.get('itinerary', []),
                'images': package.get('images', []),
                'states': package.get('states', []),
                'price': package.get('price', {}),
                'reviews': package.get('reviews', {}),
                'duration': package.get('duration', {}),
                'map_image': package.get('map_image')
            }
            return JsonResponse(package_dict, safe=False)
        else:
            raise Http404("Package not found")
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@require_GET
def get_packages(request):
    try:
        # Get the query parameters from the request
        package_name = request.GET.get('name')
        search_query = request.GET.get('search')

        # Base query with no filters
        query = {}

        # Add name filter if provided
        if package_name:
            query['key'] = package_name

        # Add search query filter if provided
        if search_query:
            query['title'] = {'$regex': search_query, '$options': 'i'}

        # Fetch the packages based on the query
        packages = collection.find(query)
        packages_list = []
        
        for pkg in packages:
            pkg_dict = {
                '_id': str(pkg.get('_id')),
                'title': pkg.get('title'),
                'package_image': pkg.get('package_image'),
                'banner_image': pkg.get('banner_image'),
                'routes': pkg.get('routes', []),
                'tour_highlights': pkg.get('tour_highlights'),
                'itinerary': pkg.get('itinerary', []),
                'images': pkg.get('images', []),
                'states': pkg.get('states', []),
                'price': pkg.get('price', {}),
                'duration': pkg.get('duration', {}),
                'type': pkg.get('type')
            }
            packages_list.append(pkg_dict)

        return JsonResponse({'packages': packages_list})

    except Exception as e:
        print(f"Error in get_packages: {str(e)}")  # Log the error
        return JsonResponse({'error': 'An error occurred while fetching packages.'}, status=500)


@csrf_exempt
def packages_title(request):
    packages = list(categories_collection.find({}, {"_id": 0}))  # Exclude MongoDB `_id` field
    return JsonResponse(packages, safe=False)


# ------------------------------------------------------------------------------------

def home(request):
    return JsonResponse({'message': 'Welcome to the home page'})

@csrf_exempt
@require_POST
def submit_review(request, pkgId):
    review_text = request.POST.get('reviewText')
    title = request.POST.get('title')
    name = request.POST.get('name')
    image = request.FILES.get('image')

    # Define the storage path in the React app's public folder
    react_app_static_path = os.path.join('D:/SEM_4/tourismmgmt/frontend', 'public', 'static', 'image', 'review')
    
    # Create the directory if it doesn't exist
    os.makedirs(react_app_static_path, exist_ok=True)
    
    # Save the file to the defined location
    fs = FileSystemStorage(location=react_app_static_path)
    file_name = fs.save(image.name, image)
    
    # Get the relative URL to be stored in MongoDB
    file_url = os.path.join(file_name)
                
    review = {
        "title":title,
        "text": review_text,
        "image_url": file_url,
        "name":name,
        "date": datetime.now(),
    }
    
    collection.update_one(
        {"_id": ObjectId(pkgId)},
        {"$push": {"reviews": review}}
    )

    return JsonResponse({"message": "Review submitted successfully!"}, status=201)

@csrf_exempt
def contact(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            username = request.GET.get('username')

            # Ensure username is provided
            if not username:
                return JsonResponse({'error': 'Username parameter is missing'}, status=400)

            # Fetch user email
            try:
                user = user_collection.find_one({'username': username})
                user_email = user.get('email', '')
            except User.DoesNotExist:
                return JsonResponse({'error': 'User not found'}, status=404)

            subject = data.get('subject')
            message = data.get('message')
            from_email = user_email
            to_email = 'mahinsabbirhusen@gmail.com'

            # Check if essential fields are provided
            if not subject or not message:
                return JsonResponse({'error': 'Subject and message are required'}, status=400)

            # Send email
            email = EmailMessage(
                subject,
                message,
                from_email,
                [to_email],
            )
            email.send()

            return JsonResponse({'message': 'Message sent successfully!'}, status=200)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON data'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Invalid request method'}, status=400)