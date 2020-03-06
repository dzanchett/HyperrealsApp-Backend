from django.db import models
from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.core.validators import MinLengthValidator, RegexValidator, ValidationError
from isbnlib import notisbn, meta, canonical, mask, is_isbn13
# Create your models here.

def isbn_validator(isbnlike):
    """
    This is a validator for our isbn data. The Book class only accepts isbn13 format, so
    if this function receive a isbn10 it will raise a exception.
    """
    if (not is_isbn13(isbnlike)) or notisbn(isbnlike):
        raise ValidationError("ISBN invalid")
    else:
        try:
            m = meta(canonical(isbnlike))
            print(m)
        except Exception:
            raise ValidationError("ISBN valid but not used")
        
# Remaps the possible erros messages to more "easy to handle" versions.
# Only the invalid error type is not mapped, because our validator function can raise more than
# one type of invalid error.
generic_error_messages={'null': 'null', 'blank': 'blank',
                        'invalid_choice':'invalid_choice',
                        'unique': 'unique', 'unique_for_date': 'unique_for_date' }

class Book(models.Model):
    isbnlike = models.CharField(max_length=40,unique=True,error_messages=generic_error_messages,validators=[isbn_validator])
    def get_meta(self):
        """
        Return the book's meta data (Title, Authors, Year, etc...) in a dictionary form, with the isbn13 field masked.
        """
        d = meta(canonical(self.isbnlike))
        d['ISBN-13'] = mask(d['ISBN-13'])
        return d

class KnowledgeManager(models.Manager):
    def create(self, *args, **kwargs):
        kwargs["nameKnowledge"] = self.model.normalize_name(kwargs["nameKnowledge"])
        return super().create(*args,**kwargs)
    def get(self, *args, **kwargs):
        kwargs["nameKnowledge"] = self.model.normalize_name(kwargs["nameKnowledge"])
        return super().get(*args,**kwargs)

class Knowledge(models.Model):
    nameKnowledge = models.CharField(max_length=100,unique=True,error_messages=generic_error_messages)
    objects = KnowledgeManager()

    def clean(self):
        self.nameKnowledge = self.normalize_name(self.nameKnowledge)
    @classmethod
    def normalize_name(cls, name):
        name = " ".join(name.split())
        name = name.lower()
        return name

    def capitalized_name_knowledge(self):
        return " ".join([s.capitalize() for s in self.nameKnowledge.split() ])

class EmailUserManager(BaseUserManager):
    def create_user(self, email, canonical_username, password=None):
        """
        Creates and saves a User with the given email, canonical_username
        and password.
        """
        user = self.model(
            email=self.normalize_email(email),
            canonical_username=canonical_username
        )
        user.set_password(password)

        # The method full_clean validates the objects. It will not clean the object 
        user.full_clean()
        user.save(using=self._db)
        return user

# If a invalid error occurs, we only says that is was 'invalid'
generic_error_messages['invalid'] = 'invalid'

# The email is used as a username for this class. As it is not the "kind" of username tha someone would expect, we
# have a canonical_username field to make this role.
class EmailUser(AbstractBaseUser):
    # The true username for this class
    email = models.EmailField(
        verbose_name='email address',
        max_length=255,
        unique=True,
        error_messages=generic_error_messages
    )
    # The "more normal" type of username, such as "donald_duck33"
    canonical_username = models.CharField(max_length=40,unique=True,error_messages=generic_error_messages,validators=[RegexValidator(regex=r"^[a-zA-Z0-9_]+$")]) 
    myBooks = models.ManyToManyField(Book, related_name="myBooks")
    desiredBooks = models.ManyToManyField(Book, related_name="desiredBooks")
    myKnowledge = models.ManyToManyField(Knowledge, related_name="myKnowledge")
    desiredKnowledge = models.ManyToManyField(Knowledge, related_name="desiredKnowledge")
    objects = EmailUserManager()
    latitude = models.FloatField(default=None,blank=True,null=True)
    longitude = models.FloatField(default=None,blank=True,null=True)
    # This is the list others users who own a book or knowledge that we are interested in. 
    matched_users= models.ManyToManyField("self",symmetrical=False, verbose_name="list of interested users")
    USERNAME_FIELD = 'email'
    EMAIL_FIELD = 'email'
    REQUIRED_FIELDS = ['canonical_username']

    def __str__(self):
        return self.email

class Message(models.Model):
    idMessage = models.AutoField(primary_key=True)
    text = models.TextField()
    userSent = models.CharField(max_length=40,error_messages=generic_error_messages,validators=[RegexValidator(regex=r"^[a-zA-Z0-9_]+$")]) 

class Chat(models.Model):
    readUser1 = models.BooleanField()
    readUser2 = models.BooleanField()
    messages = models.ManyToManyField(Message)
    usuario1 = models.OneToOneField(EmailUser, related_name="usuario1", on_delete=models.PROTECT)
    usuario2 = models.OneToOneField(EmailUser, related_name="usuario2", on_delete=models.PROTECT)

class Match(models.Model):
    text = models.TextField()
    usuario1 = models.OneToOneField(EmailUser, related_name="u1", on_delete=models.PROTECT)
    usuario2 = models.OneToOneField(EmailUser, related_name="u2", on_delete=models.PROTECT)
