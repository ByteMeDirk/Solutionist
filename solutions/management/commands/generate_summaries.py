from django.core.management.base import BaseCommand
from django.db import transaction
from solutions.models import Solution
from tqdm import tqdm


class Command(BaseCommand):
    help = 'Generates summaries for existing solutions'

    def handle(self, *args, **kwargs):
        solutions = Solution.objects.all()
        total = solutions.count()

        if total == 0:
            self.stdout.write(self.style.SUCCESS('No solutions found.'))
            return

        self.stdout.write(f'Generating summaries for {total} solutions...')

        with transaction.atomic():
            for solution in tqdm(solutions):
                solution.save(force_summary=True)

        self.stdout.write(self.style.SUCCESS('Successfully generated summaries!'))
