from django.core.management.base import BaseCommand, CommandError
from geopy.distance import distance
from math import inf
from hyper.models import EmailUser, EmailUserManager, Book, Knowledge, Chat, Message, Match
from django.db.models import Q

def invalid_coordinates(co):
    return co[0] == None or co[1] == None

def user_distance(user1,user2):
    co1 = (user1.latitude, user1.longitude)
    co2 = (user2.latitude, user2.longitude)
    print(co1)
    print(co2)
    if invalid_coordinates(co1) or invalid_coordinates(co2):
        return inf
    return distance(co1,co2).km

def has_intersection(l1,l2):
    listBooks = "Books: "
    added = False

    for l in l1:
        if l in l2:
            if added:
                listBooks += ", "
            #print(str(l.get_meta()['Title']))
            listBooks += l.get_meta()['Title']
            added = True
    
    if added:
        return listBooks
    else:
        return ""

def generate_message_match(text, u1, u2):
    try:
        match = Match.objects.get(text=text, usuario1=u1, usuario2=u2)
    except:
        try:
            match = Match.objects.get(text=text, usuario1=u2, usuario2=u1)
        except:
            match = Match(text=text, usuario1=u1, usuario2=u2)
            match.save()

            m = Message(text=text, userSent="system")
            m.save()

            added = False;

            criterion1 = Q(usuario1=u1)
            criterion2 = Q(usuario2=u2)

            for chat in Chat.objects.filter(criterion1 & criterion2):
                chat.readUser1 = False
                chat.readUser2 = False
                chat.save()
                chat.messages.add(m)
                added = True

            criterion1 = Q(usuario1=u2)
            criterion2 = Q(usuario2=u1)

            for chat in Chat.objects.filter(criterion1 & criterion2):
                chat.readUser1 = False
                chat.readUser2 = False
                chat.save()
                chat.messages.add(m)
                added = True

            if not added:
                c = Chat(usuario1=u1, usuario2=u2, readUser1=False, readUser2=False)
                c.save()
                c.messages.add(m)

            return True

class Command(BaseCommand):
    help = 'For each user, update the list of matched users'
    # Max distance between two matched users
    MAX_DISTANCE_KM=10
    def handle(self, *args, **options):
        self.normalmsg("Trying to match the users with each other...")
        users = EmailUser.objects.all()
        n = len(users)
        for i in range(n):
            for j in range(i+1,n):
                u = users[i]
                v = users[j]
                self.normalmsg(u.canonical_username + " " + v.canonical_username)
                self.normalmsg(str(user_distance(u,v)))
                if user_distance(u,v) <= self.MAX_DISTANCE_KM:
                    tt = self.has_something_of_interest(u,v)
                    #self.normalmsg(tt)
                    if tt != "":
                        u.matched_users.add(v)
                        self.sucessmsg("User %s was added to %s's list." % (v,u))
                        ttt1 = tt;

                    tt = self.has_something_of_interest(v,u)
                    #self.normalmsg(tt)
                    if tt != "":
                        v.matched_users.add(u)
                        self.sucessmsg("User %s was added to %s's list." % (u,v))
                        ttt2 = tt;

                    generate_message_match("A match were found!<br/>" + ttt1 + "<br/>" + ttt2, u, v)
        self.sucessmsg("Done!")

    def has_something_of_interest(self,u,v):
        """Test if user v has something that interests user u"""
        listInterest = "Knowledges: "

        added = False

        for ukn in u.desiredKnowledge.all():
            for vkn in v.myKnowledge.all():
                for w in ukn.nameKnowledge.split():
                    if w in vkn.nameKnowledge:
                        if added:
                            listInterest += ", "

                        listInterest += ukn.nameKnowledge
                        added = True
                        #return True

        if added:
            listInterest += " from user " + v.canonical_username

        listBooks = has_intersection(u.desiredBooks.all(),v.myBooks.all())

        if listBooks != "":
            listBooks += " from user " + v.canonical_username

        if added:
            if listBooks == "":
                return listInterest
            else:
                return listInterest + "<br/>" + listBooks
        else:
            return listBooks

        #return has_intersection(u.desiredBooks.all(),v.myBooks.all())

    def sucessmsg(self,msg):
        self.stdout.write(self.style.SUCCESS(msg))
    def normalmsg(self,msg):
        self.stdout.write(msg)
