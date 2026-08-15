from __future__ import annotations

from astronavigator.scene.object_index import normalize_object_name
from astronavigator.sky.constellation_line import Constellation


DEFAULT_SEARCH_RESULT_LIMIT = 20


class ConstellationIndex:
    def __init__(self) -> None:
        self._constellations: list[Constellation] = []

    def update(self, constellations: list[Constellation]) -> None:
        self._constellations = list(constellations)

    def find_by_query(self, query: str, limit: int = DEFAULT_SEARCH_RESULT_LIMIT) -> list[Constellation]:
        normalized_query = normalize_object_name(query)
        if not normalized_query or limit <= 0:
            return []

        candidates: list[tuple[tuple[int, int, int, str], Constellation]] = []

        for constellation in self._constellations:
            best_rank: tuple[int, int, int, str] | None = None

            for name in (constellation.name, *constellation.aliases):
                normalized_name = normalize_object_name(name)
                if not normalized_name:
                    continue

                if normalized_name == normalized_query:
                    match_type = 0
                    match_position = 0
                elif normalized_name.startswith(normalized_query):
                    match_type = 1
                    match_position = 0
                else:
                    match_position = normalized_name.find(normalized_query)
                    if match_position < 0:
                        continue
                    match_type = 2

                rank = (match_type, match_position, len(normalized_name), name)

                if best_rank is None or rank < best_rank:
                    best_rank = rank

            if best_rank is not None:
                candidates.append((best_rank, constellation))

        candidates.sort(key=lambda x: x[0])
        return [constellation for _, constellation in candidates[:limit]]