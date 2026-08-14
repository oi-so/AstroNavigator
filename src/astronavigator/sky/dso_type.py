from enum import Enum, auto


class DeepSkyObjectType(Enum):
    STAR = auto()
    DOUBLE_STAR = auto() # 二重星
    STAR_ASSOCIATION = auto() # アソシエーション星団

    OPEN_CLUSTER = auto() # 散開星団
    GLOBULAR_CLUSTER = auto() # 球状星団
    CLUSTER_AND_NEBULA = auto() # 星団と星雲

    GALAXY = auto() # 単体銀河
    GALAXY_PAIR = auto() # 二重銀河
    GALAXY_TRIPLET = auto() # 三重銀河
    GALAXY_GROUP = auto() # 銀河群

    PLANETARY_NEBULA = auto() # 惑星状星雲
    HII_REGION = auto() # HII領域
    DARK_NEBULA = auto() # 暗黒星雲
    EMISSION_NEBULA = auto() # 散光星雲
    REFLECTION_NEBULA = auto() # 反射星雲
    NEBULA = auto() # 星雲
    SUPERNOVA_REMNANT = auto() # 超新星残骸

    NOVA = auto() # 新星
    OTHER = auto() # その他