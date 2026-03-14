from django.db import migrations

def populate_match_data(apps, schema_editor):
    Route = apps.get_model('match', 'Route')
    RoutePoint = apps.get_model('match', 'RoutePoint')

    # 1. Crear Rutas (Route)
    # Según los datos proporcionados, hay route_id del 1 al 6.
    # Asumiremos nombres genéricos o basados en los puntos para las rutas si no se especificaron.
    # Basado en los puntos:
    # 1: Ruta por Calle 80 / Engativá -> U Cundinamarca
    # 2: Ruta por Calle 13 / Mosquera / Madrid -> U Cundinamarca
    # 3: Ruta La Vega / Nocaima -> U Cundinamarca
    # 4: Ruta Sasaima / Albán -> U Cundinamarca
    # 5: Ruta Zipacón / Cachipay (parece otra ruta del sector) -> U Cundinamarca (por los puntos finales)
    # 6: Ruta Anolaima -> U Cundinamarca

    # Nota: Todos los puntos finales parecen ser "Universidad de Cundinamarca", 
    # así que asumiremos dirección 'MUNI_TO_U' para este ejemplo inicial.
    
    routes_data = [
        (1, "LA 80", 'MUNI_TO_U'),
        (2, "Calle 13", 'MUNI_TO_U'),
        (3, "La Vega", 'MUNI_TO_U'),
        (4, "Sasaima", 'MUNI_TO_U'),
        (5, "LA FLORIDA", 'MUNI_TO_U'), # Nombre inferido por ubicación
        (6, "ZIPACÓN", 'MUNI_TO_U'),
    ]

    for pk, name, direction in routes_data:
        if not Route.objects.filter(pk=pk).exists():
            Route.objects.create(pk=pk, name=name, direction=direction)

    # 2. Crear Puntos de Ruta (RoutePoint)
    # id, name, latitude, longitude, order, route_id
    points_data = [
        (1, "ENGATIVA Club Parfum", 4.70730049807101, -74.1093969603456, 1, 1),
        (2, "Puente de Guadua", 4.72793176469878, -74.1260166062308, 2, 1),
        (3, "Market Bogota COTA", 4.75441088078764, -74.1503381645539, 3, 1),
        (4, "Vereda Puente Piedra", 4.81516045707826, -74.2230753079925, 4, 1),
        (5, "Carrera 13 # 10-12", 4.85170686001598, -74.2710784079657, 5, 1),
        (6, "La Cantareta Campestre", 4.83621427113365, -74.3015408822103, 6, 1),
        (7, "Alpina Facatativá", 4.80901960803076, -74.3278920027876, 7, 1),
        (8, "Facatativá Centro", 4.81074174666673, -74.3485862980234, 8, 1),
        (9, "Universidad de Cundinamarca", 4.82903310108029, -74.3551978801524, 9, 1),
        (10, "Hayuelos", 4.66365350533975, -74.1304876359098, 1, 2),
        (11, "Peaje Río Bogotá", 4.69856046734414, -74.1793805666052, 2, 2),
        (12, "Hotel Transportador", 4.70200416424035, -74.224590663904, 3, 2),
        (13, "Round Point Madrid", 4.7121253066464, -74.2385497359942, 4, 2),
        (14, "Ferrelectricos La 15", 4.74119269835856, -74.2558218966808, 5, 2),
        (15, "Madrid Centro", 4.73961271100862, -74.2771922701036, 6, 2),
        (16, "Peaje El Corzo", 4.74897299919493, -74.290927371364, 7, 2),
        (17, "Cartagenita", 4.78644338257929, -74.2920423055089, 8, 2),
        (18, "Calle de los Abogados", 4.80838026686688, -74.3546728045771, 9, 2),
        (19, "Universidad de Cundinamarca", 4.82903310108029, -74.3551978801524, 10, 2),
        (20, "Trapiche Los Abuelos", 5.0264184516495, -74.4684777873956, 1, 3),
        (21, "Parador Las Marías", 5.0738754685642, -74.4458563644951, 2, 3),
        (22, "Peaje Caiquero", 5.0654126869021, -74.4142441915149, 3, 3),
        (23, "Cruce Nocaima", 5.0432896225815, -74.3741108355369, 4, 3),
        (24, "La Vega Centro", 5.0017380590997, -74.3422458610018, 5, 3),
        (25, "Parador Pacho", 4.9769193183708, -74.3096913772714, 6, 3),
        (26, "Le Petit Jardin", 4.9492165212708, -74.2985486921962, 7, 3),
        (27, "Delicias del Campo", 4.913493636064, -74.2955274365639, 8, 3),
        (28, "Alto del Vino", 4.873038623758, -74.292477801672, 9, 3),
        (29, "Universidad de Cundinamarca", 4.8290331010803, -74.3551978801524, 10, 3),
        (30, "La esquina de Lalo", 5.00991830873569, -74.4719715255572, 1, 4),
        (31, "Hotel Campestre El Trapiche", 4.99644003999034, -74.472295451779, 2, 4),
        (32, "Granja San Pablo Savicol", 4.98067358283635, -74.4417102965891, 3, 4),
        (33, "Cl. 7 # 4-122 (Sasaima)", 4.96272541920153, -74.4355702400984, 4, 4),
        (34, "Proyecto Pastor DBC", 4.92617209978229, -74.4280697786438, 5, 4),
        (35, "Peaje Jalisco", 4.90120958052094, -74.4261074068392, 6, 4),
        (36, "Quesos Santa Fé", 4.87853654204632, -74.4365992060041, 7, 4),
        (37, "Alto de la Tribuna - Carrilera", 4.85806261674026, -74.410097946106, 8, 4),
        (38, "Salón Comunal Barrio Brasilia", 4.82043215757898, -74.3675729090381, 9, 4),
        (39, "Universidad de Cundinamarca", 4.82903310108029, -74.3551978801524, 10, 4),
        (40, "Pompilio 111 #111", 4.76787596857676, -74.4359944141867, 1, 5),
        (41, "Misty Farms", 4.77012151741155, -74.4250226091306, 2, 5),
        (42, "Vivero Valparaíso", 4.7809897874982, -74.4218580004553, 3, 5),
        (43, "La Pica Tienda", 4.7934550724803, -74.4261309386283, 4, 5),
        (44, "Facatativá - La Florida", 4.8090691598552, -74.40690421108, 5, 5),
        (45, "Granja Avícola El Mirador", 4.83092822287524, -74.4043531078226, 6, 5),
        (46, "Casa de Eventos Casa de Astilla", 4.83509111088238, -74.3884878263904, 7, 5),
        (47, "Universidad de Cundinamarca", 4.82903310108029, -74.3551978801524, 8, 5),
        (48, "Finca La Esperanza Florida Anolaima", 4.76325723492398, -74.4310031459214, 1, 6),
        (49, "Polideportivo de Petaluma", 4.75628383087434, -74.4245893773701, 2, 6),
        (50, "Cachipay - Zipacón", 4.74865024329732, -74.4211623737427, 3, 6),
        (51, "Granja Avícola Miluc Santa Ana", 4.7370230844551, -74.4068486992932, 4, 6),
        (52, "Hacienda Nebraska", 4.75174566033526, -74.399721437794, 5, 6),
        (53, "Cra. 3 # 2-27", 4.75742267515216, -74.3810209899613, 6, 6),
        (54, "Tipicarnes Panadería", 4.78055622566162, -74.3644640771967, 7, 6),
        (55, "Universidad de Cundinamarca", 4.82903310108029, -74.3551978801524, 8, 6),
    ]

    for pk, name, lat, lon, order, route_id in points_data:
        if not RoutePoint.objects.filter(pk=pk).exists():
            RoutePoint.objects.create(
                pk=pk,
                name=name,
                latitude=lat,
                longitude=lon,
                order=order,
                route_id=route_id
            )

class Migration(migrations.Migration):

    dependencies = [
        ('match', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(populate_match_data),
    ]
