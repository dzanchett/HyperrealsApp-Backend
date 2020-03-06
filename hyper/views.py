from django.contrib.sites.shortcuts import get_current_site
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
import json
# from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import views as auth_views
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.forms import AuthenticationForm
from django import forms
from django.contrib.auth import authenticate, login, logout
from django.views.generic import View
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from .models import EmailUser, EmailUserManager, Book, Knowledge, Chat, Message
from django.core.validators import ValidationError
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import ObjectDoesNotExist
from isbnlib import is_isbn10, to_isbn13
from rest_framework.permissions import IsAuthenticated
from django.core.exceptions import PermissionDenied
from django.db.models import Q

from django.core import serializers

LOGIN_REPEATED, LOGIN_FAILED, LOGIN_SUCESS, CREATE_SUCESS, CREATE_FAILED, CREATE_BOOK_FAILED,CREATE_BOOK_SUCESS = range(1,8)

class LoginIsRequiredMixin:
    def dispatch(self, request, *args, **kwargs):
        try:
            env = json.loads(request.body)
            email = env['email']
            request.user = EmailUser.objects.get(email=email)
            return super().dispatch(request, *args, **kwargs)
        except:
            raise PermissionDenied

# TODO: Change or remove this later.
def profile(request):
    return JsonResponse({"message": "Ola Mundo"})


def login_for_angular(request):
    """
    The login view. The code is self explanatory.
    """
    env = json.loads(request.body)
    email = env['email']
    password = env['password']

    if request.user.is_authenticated:
        return JsonResponse({"auth": "true", "message": "User was already logged in!", "messageCode": LOGIN_REPEATED, "username": request.user.canonical_username})
    else:
        user = authenticate(username=email,password=password)
        if user == None:
            return JsonResponse({ "auth": "false", "message": "Login Failed", "messageCode": LOGIN_FAILED})
        else:
            login(request, user)
            return JsonResponse({ "auth": "true", "message": "Login Successful", "messageCode": LOGIN_SUCESS, "username": request.user.canonical_username})
        
def logout_for_angular(request):
    """
    The logout view. The code is self explanatory.
    """
    logout(request)
    return JsonResponse({"message": "Logout"})


def create_account(request):

    env = json.loads(request.body)
    
    email = env['email']
    canonical_username = env['username']
    password = env['password']

    try:
        u = EmailUser.objects.create_user(email,canonical_username,password)
        u.save()
        return JsonResponse({"message": "User successful created.", "messageCode": CREATE_SUCESS})
    except ValidationError as verr:
        # Here we convert the ValidationError message containing the possibles errors types in a dictionary suitable for json conversion.
        d = dict(verr)
        for k in d.keys():
            d[k] = d[k][0]
        d["message"] = "Error on user creation."
        d["messageCode"] = CREATE_FAILED
        resp =  JsonResponse(d)
        resp.status_code = 400
        return resp

class MatchsView(LoginRequiredMixin, View):
    def get(self, request):
        resp = {}
        u = request.user
        for v in u.matched_users.all():
            booklist = []
            for b in u.desiredBooks.all():
                if b in v.myBooks.all():
                    booklist.append(b.get_meta())
            resp[v.email] = {"books": booklist}
            
        return JsonResponse(resp)
# The LoginIsRequiredMixin class makes sure that only logged users can access this view.
# The raise_exception=True line guarantees that non logged users
# will receive a error.
class AddMyBookView(LoginIsRequiredMixin, View):
    permission_classes = (IsAuthenticated,)

    raise_exception=True

    def post(self,request):
        env = json.loads(request.body)
        isbnlike = env['ISBN']

        # Make sure that only isbn13 data gets in the database
        if is_isbn10(isbnlike):
            isbnlike = to_isbn13(isbnlike)
        # Search for a existing entry of this ISBN 
        try:
            b = Book.objects.get(isbnlike=isbnlike) #isDesired=False
        except ObjectDoesNotExist:
            # if it does not exits, tries to create a new one
            try:
                b = Book(isbnlike=isbnlike) #isDesired=False
                b.full_clean()  # Validates
                b.save()
            except ValidationError as verr:
                # if validation goes wrong, convert the exception message in dictionary suitable for json conversion and return this json
                # as a response
                d = dict(verr)
                for k in d.keys():
                    d[k] = d[k][0]
                d["messageCode"] = CREATE_BOOK_FAILED
                resp =  JsonResponse(d)
                resp.status_code = 400
                return resp

        # Add the book to the set of the current logged user.
        request.user.myBooks.add(b)
        return JsonResponse({"message": "Book successfully added", "messageCode": CREATE_BOOK_SUCESS})

class DeleteMyBookView(LoginIsRequiredMixin, View):
    raise_exception=True

    def post(self,request):
        env = json.loads(request.body)
        isbnlike = env['ISBN']

        # Make sure that only isbn13 data gets in the database
        if is_isbn10(isbnlike):
            isbnlike = to_isbn13(isbnlike)
        # Search for a existing entry of this ISBN 
        try:
            b = request.user.myBooks.get(isbnlike=isbnlike)
            request.user.myBooks.remove(b)
            return JsonResponse({"message": "Book successfully deleted", "messageCode": CREATE_BOOK_SUCESS})
        except ObjectDoesNotExist:
            return JsonResponse({"message": "Book not found", "messageCode": CREATE_BOOK_FAILED})
        

# This class, as the above, only accepts user current logged in. Users that are not logged will receive a error.
class ListMyBooksView(LoginIsRequiredMixin, View):
    raise_exception=True

    def post(self,request):
        print(request.headers)

        resp = {}
        booklist = []

        # Travels the user's list of books, gathering meta data information in a list of dictionaries.
        for book in request.user.myBooks.filter(): #isDesired=False
            d = {}
            meta = book.get_meta()
            for items in meta.items():
                d[items[0]] = items[1]
            d['isbnlike'] = book.isbnlike
            booklist.append(d)

        resp["books"] = booklist
        # Send this list of books in the json format.
        return JsonResponse(resp)

# The LoginIsRequiredMixin class makes sure that only logged users can access this view.
# The raise_exception=True line guarantees that non logged users
# will receive a error.
class AddDesiredBookView(LoginIsRequiredMixin, View):
    raise_exception=True

    def post(self,request):
        env = json.loads(request.body)
        isbnlike = env['ISBN']

        # Make sure that only isbn13 data gets in the database
        if is_isbn10(isbnlike):
            isbnlike = to_isbn13(isbnlike)
        # Search for a existing entry of this ISBN 
        try:
            b = Book.objects.get(isbnlike=isbnlike) #isDesired=True
        except ObjectDoesNotExist:
            # if it does not exits, tries to create a new one
            try:
                b = Book(isbnlike=isbnlike) #isDesired=True
                b.full_clean()  # Validates
                b.save()
            except ValidationError as verr:
                # if validation goes wrong, convert the exception message in dictionary suitable for json conversion and return this json
                # as a response
                d = dict(verr)
                for k in d.keys():
                    d[k] = d[k][0]
                d["messageCode"] = CREATE_BOOK_FAILED
                resp =  JsonResponse(d)
                resp.status_code = 400
                return resp

        # Add the book to the list of the current logged user.
        request.user.desiredBooks.add(b)
        return JsonResponse({"message": "Book successfully added", "messageCode": CREATE_BOOK_SUCESS})

class DeleteDesiredBookView(LoginIsRequiredMixin, View):
    raise_exception=True

    def post(self,request):
        env = json.loads(request.body)
        isbnlike = env['ISBN']

        # Make sure that only isbn13 data gets in the database
        if is_isbn10(isbnlike):
            isbnlike = to_isbn13(isbnlike)
        # Search for a existing entry of this ISBN 

        print(isbnlike)

        for b in Book.objects.all():
            print("\t"+b.isbnlike)

        try:
            b = request.user.desiredBooks.get(isbnlike=isbnlike)
            request.user.desiredBooks.remove(b)
            return JsonResponse({"message": "Book successfully deleted", "messageCode": CREATE_BOOK_SUCESS})
        except ObjectDoesNotExist:
            return JsonResponse({"message": "Book not found", "messageCode": CREATE_BOOK_FAILED})

# This class, as the above, only accepts user current logged in. Users that are not logged will receive a error.
class ListDesiredBooksView(LoginIsRequiredMixin, View):
    raise_exception=True
    def post(self,request):
        resp = {}
        booklist = []

        # Travels the user's list of books, gathering meta data information in a list of dictionaries.
        for book in request.user.desiredBooks.filter():
            d = {}
            meta = book.get_meta()
            for items in meta.items():
                d[items[0]] = items[1]
            d['isbnlike'] = book.isbnlike
            booklist.append(d)

        resp["books"] = booklist
        # Send this list of books in the json format.
        return JsonResponse(resp)

# The LoginIsRequiredMixin class makes sure that only logged users can access this view.
# The raise_exception=True line guarantees that non logged users
# will receive a error.
class AddMyKnowledgeView(LoginIsRequiredMixin, View):
    raise_exception=True

    def post(self,request):
        env = json.loads(request.body)
        nameKnowledge = env['knowledge']

        try:
            k = Knowledge.objects.get(nameKnowledge=nameKnowledge) #isDesired=False
        except ObjectDoesNotExist:
            # if it does not exits, tries to create a new one
            try:
                k = Knowledge(nameKnowledge=nameKnowledge)
                k.full_clean()  # Validates
                k.save()
            except ValidationError as verr:
                # if validation goes wrong, convert the exception message in dictionary suitable for json conversion and return this json
                # as a response
                d = dict(verr)
                for k in d.keys():
                    d[k] = d[k][0]
                d["messageCode"] = CREATE_BOOK_FAILED
                resp =  JsonResponse(d)
                resp.status_code = 400
                return resp

        # Add the book to the list of the current logged user.
        request.user.myKnowledge.add(k)
        return JsonResponse({"message": "Knowledge successfully added", "messageCode": CREATE_BOOK_SUCESS})

class DeleteMyKnowledgeView(LoginIsRequiredMixin, View):
    raise_exception=True

    def post(self,request):
        env = json.loads(request.body)
        nameKnowledge = env['knowledge']

        try:
            k = request.user.myKnowledge.get(nameKnowledge=nameKnowledge)
            request.user.myKnowledge.remove(k)
            return JsonResponse({"message": "Knowledge successfully deleted", "messageCode": CREATE_BOOK_SUCESS})
        except ObjectDoesNotExist:
            return JsonResponse({"message": "Knowledge not found", "messageCode": CREATE_BOOK_FAILED})

# This class, as the above, only accepts user current logged in. Users that are not logged will receive a error.
class ListMyKnowledgesView(LoginIsRequiredMixin, View):
    raise_exception=True
    def post(self,request):
        resp = {}
        knowledgelist = []

        # Travels the user's list of knowledges, gathering meta data information in a list of dictionaries.
        for knowledge in request.user.myKnowledge.filter(): #isDesired=False
            d = {}
            knowledgelist.append(knowledge.capitalized_name_knowledge())

        resp["knowledges"] = knowledgelist
        # Send this list of knowledges in the json format.
        return JsonResponse(resp)


# The LoginIsRequiredMixin class makes sure that only logged users can access this view.
# The raise_exception=True line guarantees that non logged users
# will receive a error.
class AddDesiredKnowledgeView(LoginIsRequiredMixin, View):
    raise_exception=True

    def post(self,request):
        env = json.loads(request.body)
        nameKnowledge = env['knowledge']

        try:
            k = Knowledge.objects.get(nameKnowledge=nameKnowledge) #isDesired=False
        except ObjectDoesNotExist:
            # if it does not exits, tries to create a new one
            try:
                k = Knowledge(nameKnowledge=nameKnowledge)
                k.full_clean()  # Validates
                k.save()
            except ValidationError as verr:
                # if validation goes wrong, convert the exception message in dictionary suitable for json conversion and return this json
                # as a response
                d = dict(verr)
                for k in d.keys():
                    d[k] = d[k][0]
                d["messageCode"] = CREATE_BOOK_FAILED
                resp =  JsonResponse(d)
                resp.status_code = 400
                return resp

        # Add the book to the list of the current logged user.
        request.user.desiredKnowledge.add(k)
        return JsonResponse({"message": "Knowledge successfully added", "messageCode": CREATE_BOOK_SUCESS})

class DeleteDesiredKnowledgeView(LoginIsRequiredMixin, View):
    raise_exception=True

    def post(self,request):
        env = json.loads(request.body)
        nameKnowledge = env['knowledge']

        try:
            k = request.user.desiredKnowledge.get(nameKnowledge=nameKnowledge)
            request.user.desiredKnowledge.remove(k)
            return JsonResponse({"message": "Knowledge successfully deleted", "messageCode": CREATE_BOOK_SUCESS})
        except ObjectDoesNotExist:
            return JsonResponse({"message": "Knowledge not found", "messageCode": CREATE_BOOK_FAILED})

# This class, as the above, only accepts user current logged in. Users that are not logged will receive a error.
class ListDesiredKnowledgesView(LoginIsRequiredMixin, View):
    raise_exception=True
    def post(self,request):
        resp = {}
        knowledgelist = []

        # Travels the user's list of knowledges, gathering meta data information in a list of dictionaries.
        for knowledge in request.user.desiredKnowledge.filter(): #isDesired=False
            d = {}
            knowledgelist.append(knowledge.capitalized_name_knowledge())

        resp["knowledges"] = knowledgelist
        # Send this list of knowledges in the json format.
        return JsonResponse(resp)

class ListMessagesView(LoginIsRequiredMixin, View):
    raise_exception=True
    def post(self,request):
        resp = {}
        chatList = []

        for chat in Chat.objects.filter(usuario1=request.user):
            chatList.append({'usuario': chat.usuario2.canonical_username, 'read': chat.readUser2})

        for chat in Chat.objects.filter(usuario2=request.user):
            chatList.append({'usuario': chat.usuario1.canonical_username, 'read': chat.readUser1})

        resp["users"] = chatList
        return JsonResponse(resp)

class ReceivedMessagesView(LoginIsRequiredMixin, View):
    raise_exception=True
    def post(self,request):
        resp = {}
        chatList = []

        env = json.loads(request.body)
        u = env['userSent']

        uu = EmailUser.objects.get(canonical_username=u)

        criterion1 = Q(usuario1=request.user)
        criterion2 = Q(usuario2=uu)

        for chat in Chat.objects.filter(criterion1 & criterion2):
            chat.readUser2 = True
            chat.save()
            mmm = chat.messages.all()
            for m in mmm:
                chatList.append({'userSent':m.userSent, 'message': m.text})

        criterion1 = Q(usuario1=uu)
        criterion2 = Q(usuario2=request.user)

        for chat in Chat.objects.filter(criterion1 & criterion2):
            chat.readUser1 = True
            chat.save()
            mmm = chat.messages.all()
            for m in mmm:
                chatList.append({'userSent':m.userSent, 'message': m.text})

        print(chatList)

        resp["messages"] = chatList
        return JsonResponse(resp)   

class SendMessagesView(LoginIsRequiredMixin, View):
    raise_exception=True
    def post(self,request):
        env = json.loads(request.body)
        u = env['userSent']
        message = env['message']

        uu = EmailUser.objects.get(canonical_username=u)

        m = Message(text=message, userSent=request.user.canonical_username)
        m.save()

        added = False;

        criterion1 = Q(usuario1=request.user)
        criterion2 = Q(usuario2=uu)

        for chat in Chat.objects.filter(criterion1 & criterion2):
            chat.readUser1 = False
            chat.save()
            chat.messages.add(m)
            added = True

        criterion1 = Q(usuario1=uu)
        criterion2 = Q(usuario2=request.user)

        for chat in Chat.objects.filter(criterion1 & criterion2):
            chat.readUser2 = False
            chat.save()
            chat.messages.add(m)
            added = True

        if not added:
            c = Chat(usuario1=request.user, usuario2=uu, readUser1=False, readUser2=False)
            c.save()
            c.messages.add(m)

        return JsonResponse({'status': 'sent'})    


class LocalizationView(LoginIsRequiredMixin,View):
    raise_exception=True
    def post(self,request):
        env = json.loads(request.body)
        lat = float(env['latitude'])
        lo = float(env['longitude'])
        request.user.coordinates = (lat,lo)
        request.user.latitude = lat
        request.user.longitude = lo
        request.user.save()
        return JsonResponse({"message": "Coordinates updated"})
