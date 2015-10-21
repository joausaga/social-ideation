from django.core.management.base import BaseCommand, CommandError
from ideascale.models import Author, Location, Comment, Idea, Vote


class Command(BaseCommand):
    def handle(self, *args, **options):
        self.stdout.write('Starting to clean ideascale tables...')
        try:
            Idea.objects.all().delete()
            self.stdout.write('Ideas deleted')
            Comment.objects.all().delete()
            self.stdout.write('Comments deleted')
            Vote.objects.all().delete()
            self.stdout.write('Votes deleted')
            Location.objects.all().delete()
            self.stdout.write('Locations deleted')
            Author.objects.all().delete()
            self.stdout.write('Authors deleted')
        except Exception as e:
            raise CommandError('The cleaning procedure couldn\'t finished. Error {}'.format(e))

        self.stdout.write('The procedure has finished successfully...')





