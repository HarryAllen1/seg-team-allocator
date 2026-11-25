from django.db.models import IntegerChoices


class Gender(IntegerChoices):
    NOT_PROVIDED = 0, 'Not provided'
    WOMAN = 1, 'Woman'
    MAN = 2, 'Man'
    OTHER_NON_BINARY = 3, 'Other/Non-binary'


class Ethnicity(IntegerChoices):
    NOT_PROVIDED = 0, 'Not provided'
    ASIAN = 1, 'Asian, or Asian British'
    BLACK = 2, 'Black, Black British, Caribbean, or African'
    MIXED = 3, 'Mixed, or multiple ethnic groups'
    WHITE = 4, 'White'
    OTHER = 5, 'Other ethnic group (e.g. Arab)'
