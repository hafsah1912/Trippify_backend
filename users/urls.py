from django.urls import path
from .views import home, register, login, get_profile, update_profile, contact, change_password, get_packages, packages_title, get_package_by_id, add_to_wishlist, get_wishlist, book_package,get_bookings,remove_from_wishlist,submit_review
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', home, name='home'),
    
    # auth
    path('api/register/', register, name='register'),
    path('api/login/', login, name='login'),
    
    #profile 
    path('api/get_profile/', get_profile, name='get_profile'),
    path('api/update-profile/', update_profile, name='update_profile'),
    path('api/change-password/', change_password, name='change_password'),
    
    path('api/contact/', contact, name='contact'),
    
    #packages
    path('api/get_packages/', get_packages, name='get_packages'),
    path('api/packages_title/', packages_title, name='packages_title'),
    path('api/get_package_by_id/<str:pkg_id>/', get_package_by_id, name='get_package_by_id'),
    
    #wishlist
    path('api/add_to_wishlist/', add_to_wishlist, name='add_to_wishlist'),
    path('api/get_wishlist/', get_wishlist, name='get_wishlist'),
    path('api/remove_from_wishlist/', remove_from_wishlist, name='remove_from_wishlist'),
    
    #booking
    path('api/book_package/<str:username>', book_package, name='book_package'),
    path('api/get_bookings/', get_bookings, name='get_bookings'),  
    path('api/book_package/', book_package, name='book_package'),
    
    path('api/submit_review/<str:pkgId>/', submit_review, name='submit_review'),

]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

