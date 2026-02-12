from django.core.management.base import BaseCommand
from apps.match.models import Route, RoutePoint


class Command(BaseCommand):
    help = "Carga las rutas lógicas y sus puntos en la base de datos"

    def handle(self, *args, **options):
        """
        Este comando crea las rutas internas del sistema UniRide.
        Las rutas NO son visibles al usuario.
        Se usan únicamente para el emparejamiento inteligente.
        """

        routes_data = [
            # ---------------- RUTA LA 80 ----------------
            {
                "name": "LA 80",
                "direction": "MUNI_TO_U",
                "points": [
                    ("ENGATIVA Club Parfum", 4.70730049807101, -74.1093969603456),
                    ("Puente de Guadua", 4.72793176469878, -74.1260166062308),
                    ("Market Bogota COTA", 4.75441088078764, -74.1503381645539),
                    ("Vereda Puente Piedra", 4.81516045707826, -74.2230753079925),
                    ("Carrera 13 # 10-12", 4.85170686001598, -74.2710784079657),
                    ("La Cantareta Campestre", 4.83621427113365, -74.3015408822103),
                    ("Alpina Facatativá", 4.80901960803076, -74.3278920027876),
                    ("Facatativá Centro", 4.81074174666673, -74.3485862980234),
                    ("Universidad de Cundinamarca", 4.82903310108029, -74.3551978801524),
                ],
            },

            # ---------------- RUTA LA 13 ----------------
            {
                "name": "LA 13",
                "direction": "MUNI_TO_U",
                "points": [
                    ("Hayuelos", 4.66365350533975, -74.1304876359098),
                    ("Peaje Río Bogotá", 4.69856046734414, -74.1793805666052),
                    ("Hotel Transportador", 4.70200416424035, -74.224590663904),
                    ("Round Point Madrid", 4.71212530664640, -74.2385497359942),
                    ("Ferrelectricos La 15", 4.74119269835856, -74.2558218966808),
                    ("Madrid Centro", 4.73961271100862, -74.2771922701036),
                    ("Peaje El Corzo", 4.74897299919493, -74.290927371364),
                    ("Cartagenita", 4.78644338257929, -74.2920423055089),
                    ("Calle de los Abogados", 4.80838026686688, -74.3546728045771),
                    ("Universidad de Cundinamarca", 4.82903310108029, -74.3551978801524),
                ],
            },

            # ---------------- RUTA LA VEGA ----------------
            {
                "name": "LA VEGA",
                "direction": "MUNI_TO_U",
                "points": [
                    ("Trapiche Los Abuelos", 5.0264184516495, -74.4684777873956),
                    ("Parador Las Marías", 5.0738754685642, -74.4458563644951),
                    ("Peaje Caiquero", 5.0654126869021, -74.4142441915149),
                    ("Cruce Nocaima", 5.0432896225815, -74.3741108355369),
                    ("La Vega Centro", 5.0017380590997, -74.3422458610018),
                    ("Parador Pacho", 4.9769193183708, -74.3096913772714),
                    ("Le Petit Jardin", 4.9492165212708, -74.2985486921962),
                    ("Delicias del Campo", 4.9134936360640, -74.2955274365639),
                    ("Alto del Vino", 4.8730386237580, -74.2924778016720),
                    ("Universidad de Cundinamarca", 4.8290331010803, -74.3551978801524),
                ],
            },

            # ---------------- RUTA SASAIMA ----------------
            {
                "name": "SASAIMA",
                "direction": "MUNI_TO_U",
                "points": [
                    ("La esquina de Lalo", 5.00991830873569, -74.4719715255572),
                    ("Hotel Campestre El Trapiche", 4.99644003999034, -74.4722954517790),
                    ("Granja San Pablo Savicol", 4.98067358283635, -74.4417102965891),
                    ("Cl. 7 # 4-122 (Sasaima)", 4.96272541920153, -74.4355702400984),
                    ("Proyecto Pastor DBC", 4.92617209978229, -74.4280697786438),
                    ("Peaje Jalisco", 4.90120958052094, -74.4261074068392),
                    ("Quesos Santa Fé", 4.87853654204632, -74.4365992060041),
                    ("Alto de la Tribuna - Carrilera", 4.85806261674026, -74.4100979461060),
                    ("Salón Comunal Barrio Brasilia", 4.82043215757898, -74.3675729090381),
                    ("Universidad de Cundinamarca", 4.82903310108029, -74.3551978801524),
                ],
            },

            # ---------------- RUTA LA FLORIDA ----------------
            {
                "name": "LA FLORIDA",
                "direction": "MUNI_TO_U",
                "points": [
                    ("Pompilio 111 #111", 4.76787596857676, -74.4359944141867),
                    ("Misty Farms", 4.77012151741155, -74.4250226091306),
                    ("Vivero Valparaíso", 4.78098978749820, -74.4218580004553),
                    ("La Pica Tienda", 4.79345507248030, -74.4261309386283),
                    ("Facatativá - La Florida", 4.80906915985520, -74.4069042110800),
                    ("Granja Avícola El Mirador", 4.83092822287524, -74.4043531078226),
                    ("Casa de Eventos Casa de Astilla", 4.83509111088238, -74.3884878263904),
                    ("Universidad de Cundinamarca", 4.82903310108029, -74.3551978801524),
                ],
            },

            # ---------------- RUTA ZIPACÓN ----------------
            {
                "name": "ZIPACÓN",
                "direction": "MUNI_TO_U",
                "points": [
                    ("Finca La Esperanza Florida Anolaima", 4.76325723492398, -74.4310031459214),
                    ("Polideportivo de Petaluma", 4.75628383087434, -74.4245893773701),
                    ("Cachipay - Zipacón", 4.74865024329732, -74.4211623737427),
                    ("Granja Avícola Miluc Santa Ana", 4.73702308445510, -74.4068486992932),
                    ("Hacienda Nebraska", 4.75174566033526, -74.3997214377940),
                    ("Cra. 3 # 2-27", 4.75742267515216, -74.3810209899613),
                    ("Tipicarnes Panadería", 4.78055622566162, -74.3644640771967),
                    ("Universidad de Cundinamarca", 4.82903310108029, -74.3551978801524),
                ],
            },
        ]

        for route_data in routes_data:
            route, created = Route.objects.get_or_create(
                name=route_data["name"],
                direction=route_data["direction"],
            )

            if created:
                self.stdout.write(self.style.SUCCESS(f"Ruta creada: {route.name}"))

            RoutePoint.objects.filter(route=route).delete()

            for index, (name, lat, lon) in enumerate(route_data["points"], start=1):
                RoutePoint.objects.create(
                    route=route,
                    name=name,
                    latitude=lat,
                    longitude=lon,
                    order=index,
                )

        self.stdout.write(self.style.SUCCESS("✔ Todas las rutas cargadas correctamente"))
