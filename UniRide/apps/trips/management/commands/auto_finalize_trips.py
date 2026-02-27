from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from apps.trips.models import Trip, TripStatus, TripPassengerStatus
from apps.chat.models import Chat

class Command(BaseCommand):
    help = 'Auto-finalize trips that have been in "Pendiente finalizado" for more than 1 hour'

    def handle(self, *args, **options):
        # Calculate the threshold time (1 hour ago)
        threshold_time = timezone.now() - timedelta(hours=1)
        
        try:
            pending_finalized_status = TripStatus.objects.get(name='Pendiente finalizado')
            finalized_status = TripStatus.objects.get(name='Finalizado')
            passenger_finalized_status = TripPassengerStatus.objects.get(name='Finalizado')
        except (TripStatus.DoesNotExist, TripPassengerStatus.DoesNotExist) as e:
            self.stdout.write(self.style.ERROR(f"Required status not found in database: {e}"))
            return

        # Find stale trips: status is 'Pendiente finalizado' AND updated_at < 1 hour ago
        stale_trips = Trip.objects.filter(
            status_id=pending_finalized_status,
            updated_at__lt=threshold_time
        )
        
        count = stale_trips.count()
        if count == 0:
            self.stdout.write(self.style.SUCCESS("No stale trips found."))
            return

        self.stdout.write(self.style.WARNING(f"Found {count} stale trips to auto-finalize..."))

        processed_count = 0
        for trip in stale_trips:
            try:
                # 1. Update Trip status
                trip.status_id = finalized_status
                trip.finalized_at = timezone.now()
                trip.auto_finalized = True
                trip.save()
                
                # 2. Deactivate publication
                trip.publication_id.is_active = False
                trip.publication_id.save()
                
                # 3. Close chats
                Chat.objects.filter(publication=trip.publication_id, is_active=True).update(
                    is_active=False,
                    closed_at=timezone.now()
                )
                
                # 4. Mark remaining passengers as finalized (auto)
                # We update passengers who are 'Aceptado' to 'Finalizado'
                passengers_to_update = trip.passengers.filter(status_id__name='Aceptado')
                
                for p in passengers_to_update:
                    p.status_id = passenger_finalized_status
                    p.finalized_at = timezone.now()
                    p.auto_finalized = True
                    p.save()
                
                processed_count += 1
                self.stdout.write(self.style.SUCCESS(f"Auto-finalized trip {trip.id}"))
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error finalizing trip {trip.id}: {e}"))
            
        self.stdout.write(self.style.SUCCESS(f"Successfully processed {processed_count} trips"))
