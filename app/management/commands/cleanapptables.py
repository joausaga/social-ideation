from django.core.management.base import BaseCommand, CommandError
from app.models import Author, Location, AutoComment, Comment, Idea, Vote, SocialNetworkAppUser


class Command(BaseCommand):
    def handle(self, *args, **options):
        self.stdout.write('Starting to clean app tables...')
        try:
            Idea.objects.all().delete()
            self.stdout.write('Ideas were deleted')
            Comment.objects.all().delete()
            self.stdout.write('Comments were deleted')
            Vote.objects.all().delete()
            self.stdout.write('Votes were deleted')
            Location.objects.all().delete()
            self.stdout.write('Locations were deleted')
            Author.objects.all().delete()
            self.stdout.write('Authors were deleted')
            AutoComment.objects.all().delete()
            self.stdout.write('Automatic Comments were deleted')
            SocialNetworkAppUser.objects.all().delete()
            self.stdout.write('App users were deleted')
        except Exception as e:
            raise CommandError('The cleaning procedure couldn\'t finished. Error {}'.format(e))

        self.stdout.write('The procedure has finished successfully...')





