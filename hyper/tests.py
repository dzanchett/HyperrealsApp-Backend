from django.test import TestCase
from django.urls import reverse
from .models import *
from .views import *
import json
from io import StringIO
from django.core.management import call_command
from isbnlib import is_isbn10, to_isbn13
# Create your tests here.

class NormalBehaviourTest(TestCase):
    def __post(self,viewname,jsondict={}):
        return self.client.post(reverse(viewname),json.dumps(jsondict), content_type="application/json")

    def __get(self,viewname):
        return self.client.get(reverse(viewname))
        
    def __create_user(self,email, username,password):
        dict_dump = {"email": email, "username": username, "password":  password}
        r = self.__post("create",dict_dump)
        self.assertEqual(r.status_code,200)
        u = EmailUser.objects.get(email=email)
        self.assertEqual(u.latitude, None)
        self.assertEqual(u.longitude, None)

    def __login(self, email, password):
        return self.__post("login",{"email": email, "password": password})

    def __logout(self):
        return self.__post("logout")

    def __add_book(self, isbn):
        return self.__post('create_mine_book',{"ISBN": isbn})

    def __add_desired_book(self, isbn):
        return self.__post('create_desired_book',{"ISBN": isbn})

    def test_create(self):
        self.__create_user("thiagoteodoro501@gmail.com","thiago123","hyperreals")

    def test_login_logout(self):
        email = "thiagoteodoro501@gmail.com"
        username = "thiago123"
        password = "hyperreals"
        self.__create_user(email,username,password)
        r = self.__login(email,password)
        self.assertEqual(r.status_code,200)
        self.__logout()

    def create_book(self,isbn):
        if is_isbn10(isbn):
            isbn = to_isbn13(isbn)
        try:
            b = Book.objects.get(isbnlike=isbn)
        except:
            try:
                b = Book(isbnlike=isbn)
                b.full_clean()
                b.save()
            except Exception as ex:
                print("Problem with isbn = ",isbn)
                raise(ex) 
        return b
        
    def test_match(self):
        a = EmailUser.objects.create_user(email="thiago@gmail.com",canonical_username="thiago123",password="123")
        b = EmailUser.objects.create_user(email="diego@gmail.com",canonical_username="diego453aaa",password="spock")
        c = EmailUser.objects.create_user(email="creyton@gmail.com",canonical_username="creytonpt",password="sailor")
        d = EmailUser.objects.create_user(email="polnareff@gmail.com",canonical_username="chariot",password="doppio")

        # Ignoring the distance for while
        a.latitude = 0
        a.longitude = 0
        b.latitude = 0
        b.longitude = 0
        c.latitude = 0
        c.longitude = 0
        d.latitude = 0
        d.longitude = 0
        
        a.save()
        b.save()
        c.save()
        d.save()

        isbn1 = "87-997016-5-0"
        isbn2 = "978-0-13-285620-1"
        isbn3 = "978-0914098911"
        isbn4 = "85-89200-44-2"
        isbn5 = "978-8593751318"
        isbn6 = "978-1107189638"
        isbn7 = "978-1974700523"
        
        a.myBooks.add(self.create_book(isbn1))
        a.myBooks.add(self.create_book(isbn2))
        a.myBooks.add(self.create_book(isbn3))
        a.desiredBooks.add(self.create_book(isbn5))
        a.desiredKnowledge.create(nameKnowledge="Dynamic      Programming")
        a.myKnowledge.create(nameKnowledge="Linear aLgebra")
        a.myKnowledge.create(nameKnowledge="Calculus")

        b.desiredBooks.add(self.create_book(isbn6))
        b.desiredBooks.add(self.create_book(isbn1))
        b.desiredKnowledge.create(nameKnowledge="Java")
        b.myKnowledge.create(nameKnowledge="   Python")
        b.myKnowledge.create(nameKnowledge="C++")

        c.myBooks.add(self.create_book(isbn6))
        c.desiredBooks.add(self.create_book(isbn5))
        c.desiredBooks.add(self.create_book(isbn1))
        c.myKnowledge.create(nameKnowledge="Physics")

        d.myBooks.add(self.create_book(isbn7))
        d.desiredBooks.add(self.create_book(isbn6))
        d.desiredBooks.add(self.create_book(isbn7))
        d.desiredKnowledge.add(Knowledge.objects.get(nameKnowledge="python"))
        d.desiredKnowledge.create(nameKnowledge="   Modern Algebra   ")
        d.myKnowledge.add(Knowledge.objects.get(nameKnowledge="  Java"))

        call_command("update_matched_users")

        self.assertSetEqual(set({}), set(a.matched_users.all()))
        self.assertSetEqual(set({a,c,d}), set(b.matched_users.all()))
        self.assertSetEqual(set({a}), set(c.matched_users.all()))
        self.assertSetEqual(set({c,b,a}), set(d.matched_users.all()))

        self.__login("diego@gmail.com",'spock')
        r = self.__get("matchs")
        print(r.json())
        self.__logout()
