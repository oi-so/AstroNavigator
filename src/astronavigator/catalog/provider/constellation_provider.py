

from astronavigator.catalog.catalog import ConstellationCatalog


class ConstellationProvider:
    def load(self) -> ConstellationCatalog:
        raise NotImplementedError("ConstellationProvider.load() must be implemented in subclasses.")