from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.utils import timezone
from apps.users.models import User, Role, Vehicle, VehicleType
from apps.trips.models import (
    Publication, PublicationType, Trip, TripPassenger,
    TripStatus, TripPassengerStatus
)
from apps.chat.models import Chat
import datetime


class TripViewSetBaseTestCase(TestCase):
    """
    Base compartida para todos los tests de TripViewSet.
    Crea usuarios, vehículo, tipos de publicación y estados necesarios.
    """

    def setUp(self):
        self.client = APIClient()

        # Roles
        self.role_user = Role.objects.create(name='Usuario')

        # Usuarios
        self.driver = User.objects.create_user(
            username='driver', email='driver@ucundinamarca.edu.co',
            password='pass123', name='Driver', role_id=self.role_user
        )
        self.passenger1 = User.objects.create_user(
            username='passenger1', email='passenger1@ucundinamarca.edu.co',
            password='pass123', name='Passenger One', role_id=self.role_user
        )
        self.passenger2 = User.objects.create_user(
            username='passenger2', email='passenger2@ucundinamarca.edu.co',
            password='pass123', name='Passenger Two', role_id=self.role_user
        )
        self.outsider = User.objects.create_user(
            username='outsider', email='outsider@ucundinamarca.edu.co',
            password='pass123', name='Outsider', role_id=self.role_user
        )

        # Vehículo del conductor
        self.v_type = VehicleType.objects.create(name='Carro')
        self.vehicle = Vehicle.objects.create(
            user_id=self.driver, type_id=self.v_type,
            brand='Toyota', plate='ABC-123', is_active=True
        )

        # Tipos de publicación
        self.type_offer = PublicationType.objects.create(name='Oferta')
        self.type_request = PublicationType.objects.create(name='Solicitud')

        # Estados de viaje
        self.st_pending, _    = TripStatus.objects.get_or_create(name='Pendiente')
        self.st_in_progress, _ = TripStatus.objects.get_or_create(name='En curso')
        self.st_finalized, _  = TripStatus.objects.get_or_create(name='Finalizado')
        self.st_canceled, _   = TripStatus.objects.get_or_create(name='Cancelado')
        self.st_pend_cancel, _ = TripStatus.objects.get_or_create(name='Pendiente Cancelación')
        self.st_pend_final, _  = TripStatus.objects.get_or_create(name='Pendiente finalizado')

        # Estados de pasajero
        self.tp_pending, _   = TripPassengerStatus.objects.get_or_create(name='Pendiente')
        self.tp_accepted, _  = TripPassengerStatus.objects.get_or_create(name='Aceptado')
        self.tp_rejected, _  = TripPassengerStatus.objects.get_or_create(name='Rechazado')
        self.tp_canceled, _  = TripPassengerStatus.objects.get_or_create(name='Cancelado')
        self.tp_finalized, _ = TripPassengerStatus.objects.get_or_create(name='Finalizado')

    # ------------------------------------------------------------------ #
    # Helpers                                                              #
    # ------------------------------------------------------------------ #

    def _make_publication(self, user=None, seats=2, active=True):
        return Publication.objects.create(
            user_id=user or self.driver,
            type_id=self.type_offer,
            vehicle_id=self.vehicle,
            departure_place='A',
            destination='B',
            departure_datetime=timezone.now() + datetime.timedelta(days=1),
            lat_departure_place=1.0, lon_departure_place=1.0,
            lat_destination=2.0,    lon_destination=2.0,
            available_seats=seats,
            is_active=active,
        )

    def _make_trip(self, publication=None, trip_status=None):
        pub = publication or self._make_publication()
        return Trip.objects.create(
            publication_id=pub,
            driver_id=pub.user_id,
            vehicle_id=pub.vehicle_id,
            status_id=trip_status or self.st_pending,
        )

    def _make_trip_passenger(self, trip, passenger, tp_status=None, seats=1):
        return TripPassenger.objects.create(
            trip_id=trip,
            passenger_id=passenger,
            status_id=tp_status or self.tp_pending,
            seats_reserved=seats,
        )

    def _make_chat(self, trip_passenger):
        """
        Crea un Chat pasando passenger y driver explícitamente,
        que son campos NOT NULL en el modelo Chat.
        """
        return Chat.objects.create(
            trip_passenger=trip_passenger,
            publication=trip_passenger.trip_id.publication_id,
            passenger=trip_passenger.passenger_id,
            driver=trip_passenger.trip_id.driver_id,
            is_active=True,
        )

    def _full_accepted_setup(self, extra_passenger=False):
        """
        Devuelve (trip, tp1, chat1) con passenger1 aceptado.
        Si extra_passenger=True también acepta passenger2.
        """
        pub = self._make_publication(seats=3)
        trip = self._make_trip(publication=pub)
        tp1 = self._make_trip_passenger(trip, self.passenger1, self.tp_accepted)
        chat1 = self._make_chat(tp1)

        if extra_passenger:
            tp2 = self._make_trip_passenger(trip, self.passenger2, self.tp_accepted)
            chat2 = self._make_chat(tp2)
            return trip, tp1, chat1, tp2, chat2

        return trip, tp1, chat1


# ================================================================== #
# START                                                               #
# ================================================================== #

class TripStartTests(TripViewSetBaseTestCase):

    def test_driver_starts_trip_successfully(self):
        trip, tp, _ = self._full_accepted_setup()
        self.client.force_authenticate(user=self.driver)

        resp = self.client.post(f'/api/trips/trips/{trip.id}/start/')

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        trip.refresh_from_db()
        self.assertEqual(trip.status_id.name, 'En curso')

    def test_start_rejects_pending_passengers(self):
        trip, _, _ = self._full_accepted_setup()
        # Agregar pasajero pendiente
        tp_pend = self._make_trip_passenger(trip, self.passenger2, self.tp_pending)

        self.client.force_authenticate(user=self.driver)
        self.client.post(f'/api/trips/trips/{trip.id}/start/')

        tp_pend.refresh_from_db()
        self.assertEqual(tp_pend.status_id.name, 'Rechazado')

    def test_non_driver_cannot_start(self):
        trip, _, _ = self._full_accepted_setup()
        self.client.force_authenticate(user=self.passenger1)

        resp = self.client.post(f'/api/trips/trips/{trip.id}/start/')

        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_cannot_start_trip_not_pending(self):
        pub = self._make_publication()
        trip = self._make_trip(publication=pub, trip_status=self.st_in_progress)
        self._make_trip_passenger(trip, self.passenger1, self.tp_accepted)

        self.client.force_authenticate(user=self.driver)
        resp = self.client.post(f'/api/trips/trips/{trip.id}/start/')

        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_start_without_accepted_passengers(self):
        pub = self._make_publication()
        trip = self._make_trip(publication=pub)
        # Solo pasajero pendiente, ninguno aceptado
        self._make_trip_passenger(trip, self.passenger1, self.tp_pending)

        self.client.force_authenticate(user=self.driver)
        resp = self.client.post(f'/api/trips/trips/{trip.id}/start/')

        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)


# ================================================================== #
# FINALIZE                                                            #
# ================================================================== #

class TripFinalizeTests(TripViewSetBaseTestCase):

    def test_driver_finalizes_first_sets_pending_finalized(self):
        trip, tp, chat = self._full_accepted_setup()
        trip.status_id = self.st_in_progress
        trip.save()

        self.client.force_authenticate(user=self.driver)
        resp = self.client.post(f'/api/trips/trips/{trip.id}/finalize/')

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        trip.refresh_from_db()
        self.assertEqual(trip.status_id.name, 'Pendiente finalizado')
        self.assertTrue(trip.driver_finalized)

    def test_passenger_finalizes_first_sets_pending_finalized(self):
        trip, tp, chat = self._full_accepted_setup()
        trip.status_id = self.st_in_progress
        trip.save()

        self.client.force_authenticate(user=self.passenger1)
        resp = self.client.post(f'/api/trips/trips/{trip.id}/finalize/')

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        tp.refresh_from_db()
        self.assertEqual(tp.status_id.name, 'Finalizado')

    def test_all_finalize_trip_becomes_finalized(self):
        trip, tp, chat = self._full_accepted_setup()
        trip.status_id = self.st_in_progress
        trip.save()

        # Pasajero finaliza
        self.client.force_authenticate(user=self.passenger1)
        self.client.post(f'/api/trips/trips/{trip.id}/finalize/')

        # Conductor finaliza
        self.client.force_authenticate(user=self.driver)
        resp = self.client.post(f'/api/trips/trips/{trip.id}/finalize/')

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        trip.refresh_from_db()
        self.assertEqual(trip.status_id.name, 'Finalizado')
        self.assertIsNotNone(trip.finalized_at)

    def test_finalize_closes_chats(self):
        trip, tp, chat = self._full_accepted_setup()
        trip.status_id = self.st_in_progress
        trip.save()

        self.client.force_authenticate(user=self.passenger1)
        self.client.post(f'/api/trips/trips/{trip.id}/finalize/')
        self.client.force_authenticate(user=self.driver)
        self.client.post(f'/api/trips/trips/{trip.id}/finalize/')

        chat.refresh_from_db()
        self.assertFalse(chat.is_active)

    def test_finalize_deactivates_publication(self):
        trip, tp, chat = self._full_accepted_setup()
        trip.status_id = self.st_in_progress
        trip.save()

        self.client.force_authenticate(user=self.passenger1)
        self.client.post(f'/api/trips/trips/{trip.id}/finalize/')
        self.client.force_authenticate(user=self.driver)
        self.client.post(f'/api/trips/trips/{trip.id}/finalize/')

        trip.publication_id.refresh_from_db()
        self.assertFalse(trip.publication_id.is_active)

    def test_outsider_cannot_finalize(self):
        trip, _, _ = self._full_accepted_setup()
        self.client.force_authenticate(user=self.outsider)

        resp = self.client.post(f'/api/trips/trips/{trip.id}/finalize/')

        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_non_accepted_passenger_cannot_finalize(self):
        trip, tp, chat = self._full_accepted_setup()
        tp.status_id = self.tp_pending
        tp.save()

        self.client.force_authenticate(user=self.passenger1)
        resp = self.client.post(f'/api/trips/trips/{trip.id}/finalize/')

        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)


# ================================================================== #
# CANCEL PARTICIPATION                                                #
# ================================================================== #

class TripCancelParticipationTests(TripViewSetBaseTestCase):

    def test_driver_cancels_sets_pending_cancellation(self):
        trip, tp, chat = self._full_accepted_setup()
        trip.status_id = self.st_in_progress
        trip.save()

        self.client.force_authenticate(user=self.driver)
        resp = self.client.post(
            f'/api/trips/trips/{trip.id}/cancel_participation/',
            {'reason': 'Me surgió algo'}
        )

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        trip.refresh_from_db()
        self.assertEqual(trip.status_id.name, 'Pendiente Cancelación')

    def test_sole_passenger_cancels_sets_pending_cancellation(self):
        """Solo hay conductor + 1 pasajero aceptado → viaje pasa a Pendiente Cancelación."""
        trip, tp, chat = self._full_accepted_setup()

        self.client.force_authenticate(user=self.passenger1)
        resp = self.client.post(
            f'/api/trips/trips/{trip.id}/cancel_participation/',
            {'reason': 'Ya no puedo'}
        )

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        trip.refresh_from_db()
        self.assertEqual(trip.status_id.name, 'Pendiente Cancelación')

    def test_passenger_cancels_with_more_participants_only_removes_him(self):
        """Conductor + 2 pasajeros → el pasajero se va solo, viaje sigue activo."""
        trip, tp1, chat1, tp2, chat2 = self._full_accepted_setup(extra_passenger=True)

        self.client.force_authenticate(user=self.passenger1)
        resp = self.client.post(
            f'/api/trips/trips/{trip.id}/cancel_participation/',
            {'reason': 'Mejor voy caminando'}
        )

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        tp1.refresh_from_db()
        self.assertEqual(tp1.status_id.name, 'Cancelado')
        # El viaje sigue en el mismo estado
        trip.refresh_from_db()
        self.assertIn(trip.status_id.name, ['Pendiente', 'En curso'])

    def test_cancel_frees_seat_when_offer(self):
        """Al cancelar un pasajero aceptado en oferta, se libera su cupo."""
        pub = self._make_publication(seats=2)
        pub.available_seats = 0   # simula cupos llenos
        pub.save()
        trip = self._make_trip(publication=pub)
        tp1 = self._make_trip_passenger(trip, self.passenger1, self.tp_accepted, seats=1)
        self._make_chat(tp1)
        tp2 = self._make_trip_passenger(trip, self.passenger2, self.tp_accepted, seats=1)
        self._make_chat(tp2)

        self.client.force_authenticate(user=self.passenger1)
        self.client.post(
            f'/api/trips/trips/{trip.id}/cancel_participation/',
            {'reason': 'Me bajo'}
        )

        pub.refresh_from_db()
        self.assertEqual(pub.available_seats, 1)

    def test_outsider_cannot_cancel_participation(self):
        trip, _, _ = self._full_accepted_setup()
        self.client.force_authenticate(user=self.outsider)

        resp = self.client.post(
            f'/api/trips/trips/{trip.id}/cancel_participation/',
            {'reason': 'Soy un intruso'}
        )

        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_cancel_finalized_trip_returns_400(self):
        trip, tp, chat = self._full_accepted_setup()
        trip.status_id = self.st_finalized
        trip.save()

        self.client.force_authenticate(user=self.driver)
        resp = self.client.post(
            f'/api/trips/trips/{trip.id}/cancel_participation/',
            {'reason': 'Tarde'}
        )

        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cancel_without_reason_returns_400(self):
        trip, _, _ = self._full_accepted_setup()
        self.client.force_authenticate(user=self.driver)

        resp = self.client.post(f'/api/trips/trips/{trip.id}/cancel_participation/', {})

        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)


# ================================================================== #
# CONFIRM CANCELLATION READ                                           #
# ================================================================== #

class TripConfirmCancellationReadTests(TripViewSetBaseTestCase):

    def _setup_pending_cancellation(self, extra_passenger=False):
        if extra_passenger:
            trip, tp1, chat1, tp2, chat2 = self._full_accepted_setup(extra_passenger=True)
        else:
            trip, tp1, chat1 = self._full_accepted_setup()
        trip.status_id = self.st_pend_cancel
        trip.cancel_reason = 'Razón de prueba'
        trip.canceled_by = self.driver
        trip.save()

        if extra_passenger:
            return trip, tp1, chat1, tp2, chat2
        return trip, tp1, chat1

    def test_trip_not_in_pending_cancellation_returns_400(self):
        trip, tp, chat = self._full_accepted_setup()
        self.client.force_authenticate(user=self.driver)

        resp = self.client.post(f'/api/trips/trips/{trip.id}/confirm_cancellation_read/')

        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_outsider_cannot_confirm(self):
        trip, tp, chat = self._setup_pending_cancellation()
        self.client.force_authenticate(user=self.outsider)

        resp = self.client.post(f'/api/trips/trips/{trip.id}/confirm_cancellation_read/')

        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_driver_confirms_waiting_for_passenger(self):
        trip, tp, chat = self._setup_pending_cancellation()
        self.client.force_authenticate(user=self.driver)

        resp = self.client.post(f'/api/trips/trips/{trip.id}/confirm_cancellation_read/')

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        trip.refresh_from_db()
        # Aún no todos confirmaron → sigue en Pendiente Cancelación
        self.assertEqual(trip.status_id.name, 'Pendiente Cancelación')

    def test_all_confirm_trip_becomes_canceled(self):
        trip, tp, chat = self._setup_pending_cancellation()

        # Conductor confirma
        self.client.force_authenticate(user=self.driver)
        self.client.post(f'/api/trips/trips/{trip.id}/confirm_cancellation_read/')

        # Pasajero confirma
        self.client.force_authenticate(user=self.passenger1)
        resp = self.client.post(f'/api/trips/trips/{trip.id}/confirm_cancellation_read/')

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        trip.refresh_from_db()
        self.assertEqual(trip.status_id.name, 'Cancelado')

    def test_all_confirm_closes_chats(self):
        trip, tp, chat = self._setup_pending_cancellation()

        self.client.force_authenticate(user=self.driver)
        self.client.post(f'/api/trips/trips/{trip.id}/confirm_cancellation_read/')

        self.client.force_authenticate(user=self.passenger1)
        self.client.post(f'/api/trips/trips/{trip.id}/confirm_cancellation_read/')

        chat.refresh_from_db()
        self.assertFalse(chat.is_active)

    def test_all_confirm_deactivates_publication(self):
        trip, tp, chat = self._setup_pending_cancellation()

        self.client.force_authenticate(user=self.driver)
        self.client.post(f'/api/trips/trips/{trip.id}/confirm_cancellation_read/')
        self.client.force_authenticate(user=self.passenger1)
        self.client.post(f'/api/trips/trips/{trip.id}/confirm_cancellation_read/')

        trip.publication_id.refresh_from_db()
        self.assertFalse(trip.publication_id.is_active)


# ================================================================== #
# HISTORY                                                             #
# ================================================================== #

class TripHistoryTests(TripViewSetBaseTestCase):

    def _get_ids(self, resp):
        """
        Extrae los ids de la respuesta, sea lista plana o dict paginado.
        """
        data = resp.data
        if isinstance(data, list):
            items = data
        elif isinstance(data, dict):
            items = data.get('results', list(data.values())[0] if data else [])
        else:
            items = list(data)
        return [t['id'] for t in items]

    def test_driver_sees_finalized_trip_in_history(self):
        pub = self._make_publication()
        trip = self._make_trip(publication=pub, trip_status=self.st_finalized)

        self.client.force_authenticate(user=self.driver)
        resp = self.client.get('/api/trips/trips/history/')

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn(trip.id, self._get_ids(resp))

    def test_driver_does_not_see_active_trip_in_history(self):
        pub = self._make_publication()
        trip = self._make_trip(publication=pub, trip_status=self.st_pending)

        self.client.force_authenticate(user=self.driver)
        resp = self.client.get('/api/trips/trips/history/')

        self.assertNotIn(trip.id, self._get_ids(resp))

    def test_passenger_sees_rejected_trip_in_history(self):
        pub = self._make_publication()
        trip = self._make_trip(publication=pub, trip_status=self.st_finalized)
        self._make_trip_passenger(trip, self.passenger1, self.tp_rejected)

        self.client.force_authenticate(user=self.passenger1)
        resp = self.client.get('/api/trips/trips/history/')

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn(trip.id, self._get_ids(resp))

    def test_outsider_sees_empty_history(self):
        pub = self._make_publication()
        self._make_trip(publication=pub, trip_status=self.st_finalized)

        self.client.force_authenticate(user=self.outsider)
        resp = self.client.get('/api/trips/trips/history/')

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(self._get_ids(resp)), 0)

    def test_unauthenticated_history_returns_401(self):
        resp = self.client.get('/api/trips/trips/history/')
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)


# ================================================================== #
# CURRENT                                                             #
# ================================================================== #

class TripCurrentTests(TripViewSetBaseTestCase):

    def test_driver_with_active_trip_returns_trip(self):
        pub = self._make_publication()
        trip = self._make_trip(publication=pub, trip_status=self.st_pending)

        self.client.force_authenticate(user=self.driver)
        resp = self.client.get('/api/trips/trips/current/')

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['id'], trip.id)

    def test_accepted_passenger_with_active_trip_returns_trip(self):
        pub = self._make_publication()
        trip = self._make_trip(publication=pub, trip_status=self.st_in_progress)
        self._make_trip_passenger(trip, self.passenger1, self.tp_accepted)

        self.client.force_authenticate(user=self.passenger1)
        resp = self.client.get('/api/trips/trips/current/')

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['id'], trip.id)

    def test_no_active_trip_returns_204(self):
        self.client.force_authenticate(user=self.outsider)
        resp = self.client.get('/api/trips/trips/current/')

        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)

    def test_driver_finalized_trip_not_returned_as_current(self):
        pub = self._make_publication()
        self._make_trip(publication=pub, trip_status=self.st_finalized)

        self.client.force_authenticate(user=self.driver)
        resp = self.client.get('/api/trips/trips/current/')

        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)

    def test_unauthenticated_current_returns_401(self):
        resp = self.client.get('/api/trips/trips/current/')
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)


# ================================================================== #
# RATEABLE MEMBERS                                                    #
# ================================================================== #

class TripRateableMembersTests(TripViewSetBaseTestCase):

    def test_passenger_sees_driver_in_rateable(self):
        trip, tp, chat = self._full_accepted_setup()
        self.client.force_authenticate(user=self.passenger1)

        resp = self.client.get(f'/api/trips/trips/{trip.id}/rateable_members/')

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        member_ids = [m['id'] for m in resp.data['members']]
        self.assertIn(self.driver.id, member_ids)

    def test_driver_sees_accepted_passengers_in_rateable(self):
        trip, tp, chat = self._full_accepted_setup()
        self.client.force_authenticate(user=self.driver)

        resp = self.client.get(f'/api/trips/trips/{trip.id}/rateable_members/')

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        member_ids = [m['id'] for m in resp.data['members']]
        self.assertIn(self.passenger1.id, member_ids)

    def test_user_does_not_see_himself_in_rateable(self):
        trip, tp, chat = self._full_accepted_setup()
        self.client.force_authenticate(user=self.passenger1)

        resp = self.client.get(f'/api/trips/trips/{trip.id}/rateable_members/')

        member_ids = [m['id'] for m in resp.data['members']]
        self.assertNotIn(self.passenger1.id, member_ids)

    def test_outsider_cannot_see_rateable_members(self):
        trip, tp, chat = self._full_accepted_setup()
        self.client.force_authenticate(user=self.outsider)

        resp = self.client.get(f'/api/trips/trips/{trip.id}/rateable_members/')

        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)


# ================================================================== #
# FINALIZATION STATUS                                                 #
# ================================================================== #

class TripFinalizationStatusTests(TripViewSetBaseTestCase):

    def test_returns_pending_members_before_anyone_finalizes(self):
        trip, tp, chat = self._full_accepted_setup()
        self.client.force_authenticate(user=self.driver)

        resp = self.client.get(f'/api/trips/trips/{trip.id}/finalization_status/')

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        pending_ids = [m['id'] for m in resp.data['pending_members']]
        self.assertIn(self.driver.id, pending_ids)

    def test_driver_moves_to_finalized_after_finalizing(self):
        trip, tp, chat = self._full_accepted_setup()
        trip.driver_finalized = True
        trip.save()

        self.client.force_authenticate(user=self.driver)
        resp = self.client.get(f'/api/trips/trips/{trip.id}/finalization_status/')

        finalized_ids = [m['id'] for m in resp.data['finalized_members']]
        self.assertIn(self.driver.id, finalized_ids)

    def test_passenger_moves_to_finalized_after_finalizing(self):
        trip, tp, chat = self._full_accepted_setup()
        tp.status_id = self.tp_finalized
        tp.save()

        self.client.force_authenticate(user=self.driver)
        resp = self.client.get(f'/api/trips/trips/{trip.id}/finalization_status/')

        finalized_ids = [m['id'] for m in resp.data['finalized_members']]
        self.assertIn(self.passenger1.id, finalized_ids)

    def test_trip_id_present_in_response(self):
        trip, tp, chat = self._full_accepted_setup()
        self.client.force_authenticate(user=self.driver)

        resp = self.client.get(f'/api/trips/trips/{trip.id}/finalization_status/')

        self.assertEqual(resp.data['trip_id'], trip.id)