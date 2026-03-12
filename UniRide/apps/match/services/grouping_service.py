from sklearn.cluster import DBSCAN
import numpy as np


def build_groups_from_suggestions(suggestions, max_seats=4):

    suggestions_list = list(suggestions)

    if len(suggestions_list) < 2:
        return []

    data = []

    for s in suggestions_list:

        p = s.passenger_publication

        lat = float(p.lat_departure_place)
        lon = float(p.lon_departure_place)

        # normalizar hora
        minutes = p.departure_datetime.hour * 60 + p.departure_datetime.minute
        time_norm = minutes / 1440

        data.append([lat, lon, time_norm])

    X = np.array(data)

    model = DBSCAN(
        eps=0.035,     # ~3.5 km
        min_samples=2
    )

    labels = model.fit_predict(X)

    clusters = {}

    for i, label in enumerate(labels):

        if label == -1:
            continue

        if label not in clusters:
            clusters[label] = []

        clusters[label].append(suggestions_list[i])

    groups = []

    for cluster_id, cluster_suggestions in clusters.items():

        # ordenar por mejor score
        cluster_suggestions.sort(
            key=lambda x: x.score if x.score else 0,
            reverse=True
        )

        # respetar asientos
        selected = cluster_suggestions[:max_seats]

        group = []

        for s in selected:

            p = s.passenger_publication
            avg_score = sum(
                s.score if s.score else 0 for s in selected
            ) / len(selected)

            group.append({
                "suggestion_id": s.id,
                "score": s.score,
                "passenger": {
                    "name": p.user_id.name,
                    "publication_id": p.id,
                    "departure_place": p.departure_place,
                    "destination": p.destination,
                    "departure_datetime": p.departure_datetime,
                    "lat": p.lat_departure_place,
                    "lon": p.lon_departure_place
                }
            })

        groups.append({
            "group_score": avg_score,
            "passengers": group
        })

    return groups